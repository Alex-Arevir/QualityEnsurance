import pytest as pt
import os
import time
import sqlite3
import distribution_center as dc
from dotenv import load_dotenv


load_dotenv()
db_testing = os.getenv('DB_TESTING')


class TestPackageTracking:
    """Test cases for FR4: Package Tracking"""

    def setup_method(self):
        """Setup test database before each test"""
        self.db = dc.DistributionCenterDB(db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = dc.PackageManager(self.db)
    
    def teardown_method(self):
        """Clean up after each test"""
        self.db.disconnect()

    # CP-FR4-001: Búsqueda exitosa de paquete por código de barras
    def test_successful_package_search_by_barcode(self):
        """Test successful package search returns complete information within 1 second"""
        # Arrange
        barcode = "PKG001"
        self.manager.register_package(barcode, 10.0, 20.0, 15.0, 10.0, 
                                      "New York, USA", "Standard")
        
        # Act
        start_time = time.time()
        result = self.manager.search_package(barcode)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert result is not None
        assert result['barcode'] == barcode
        assert result['status'] == 'Stored'
        assert result['category'] is not None
        assert result['location'] is not None
        assert result['received_at'] is not None
        assert elapsed_time < 1.0

    # CP-FR4-002: Búsqueda de paquete inexistente
    def test_search_nonexistent_package(self):
        """Test searching for non-existent package returns None"""
        # Arrange
        barcode = "PKG999"
        
        # Act
        result = self.manager.search_package(barcode)
        
        # Assert
        assert result is None

    # CP-FR4-003: Actualización de estado Received a Stored con audit trail
    def test_status_update_received_to_stored_with_audit(self):
        """Test status update from Received to Stored creates audit trail"""
        # Arrange
        barcode = "PKG002"
        self.db.cursor.execute("""
            INSERT INTO Packages 
            (barcode, weight, length, width, height, destination, priority, 
             category_id, location_id, status)
            VALUES (?, 10.0, 20.0, 15.0, 10.0, 'Chicago', 'Standard', 1, 1, 'Received')
        """, (barcode,))
        self.db.conn.commit()
        
        # Act
        success = self.manager.update_package_status(barcode, "Stored")
        
        # Assert
        assert success == True
        
        package = self.manager.search_package(barcode)
        assert package['status'] == 'Stored'
        
        # Verify audit trail
        audit_records = self.db.cursor.execute("""
            SELECT action, old_status, new_status, timestamp
            FROM AuditTrail
            WHERE package_id = (SELECT package_id FROM Packages WHERE barcode = ?)
        """, (barcode,)).fetchall()
        
        assert len(audit_records) > 0
        latest = audit_records[-1]
        assert latest[0] == 'STATUS_UPDATE'
        assert latest[1] == 'Received'
        assert latest[2] == 'Stored'
        assert latest[3] is not None

    # CP-FR4-004: Cambio de estado Stored a In Transit
    def test_status_update_stored_to_in_transit(self):
        """Test status change from Stored to In Transit with audit record"""
        # Arrange
        barcode = "PKG003"
        self.manager.register_package(barcode, 15.0, 25.0, 20.0, 18.0,
                                      "Boston, USA", "Standard")
        
        # Act
        success = self.manager.update_package_status(barcode, "In Transit")
        
        # Assert
        assert success == True
        
        # Verify audit trail
        audit_records = self.db.cursor.execute("""
            SELECT action, old_status, new_status, old_location
            FROM AuditTrail
            WHERE package_id = (SELECT package_id FROM Packages WHERE barcode = ?)
            AND action = 'STATUS_UPDATE'
        """, (barcode,)).fetchall()
        
        assert len(audit_records) > 0
        latest = audit_records[-1]
        assert latest[0] == 'STATUS_UPDATE'
        assert latest[1] == 'Stored'
        assert latest[2] == 'In Transit'
        assert latest[3] is not None

    # CP-FR4-005: Múltiples cambios de estado con histórico completo
    def test_multiple_status_changes_chronological_order(self):
        """Test multiple status changes maintain chronological audit history"""
        # Arrange
        barcode = "PKG004"
        self.db.cursor.execute("""
            INSERT INTO Packages 
            (barcode, weight, length, width, height, destination, priority, 
             category_id, location_id, status)
            VALUES (?, 10.0, 20.0, 15.0, 10.0, 'Miami', 'Standard', 1, 2, 'Received')
        """, (barcode,))
        package_id = self.db.cursor.lastrowid
        
        self.db.cursor.execute("""
            INSERT INTO AuditTrail (package_id, action, new_status, notes)
            VALUES (?, 'REGISTERED', 'Received', 'Initial registration')
        """, (package_id,))
        self.db.conn.commit()
        
        # Act
        time.sleep(0.1)
        self.manager.update_package_status(barcode, "Stored")
        time.sleep(0.1)
        self.manager.update_package_status(barcode, "In Transit")
        time.sleep(0.1)
        self.manager.update_package_status(barcode, "Delivered")
        
        # Assert
        audit_trail = self.db.cursor.execute("""
            SELECT action, old_status, new_status, timestamp
            FROM AuditTrail
            WHERE package_id = ?
            ORDER BY timestamp ASC
        """, (package_id,)).fetchall()
        
        assert len(audit_trail) == 4
        
        # Verify chronological order
        timestamps = [record[3] for record in audit_trail]
        assert timestamps == sorted(timestamps)
        
        # Verify status progression
        status_updates = [r for r in audit_trail if r[0] == 'STATUS_UPDATE']
        assert status_updates[0][1] == 'Received' and status_updates[0][2] == 'Stored'
        assert status_updates[1][1] == 'Stored' and status_updates[1][2] == 'In Transit'
        assert status_updates[2][1] == 'In Transit' and status_updates[2][2] == 'Delivered'

    # CP-FR4-006: Liberación de ubicación al marcar como Delivered
    def test_location_freed_when_delivered(self):
        """Test location is freed when package status is set to Delivered"""
        # Arrange
        barcode = "PKG005"
        self.manager.register_package(barcode, 12.0, 22.0, 18.0, 14.0,
                                      "Seattle, USA", "Standard")
        
        package = self.manager.search_package(barcode)
        location_code = package['location']
        
        location_id, is_occupied_before = self.db.cursor.execute("""
            SELECT location_id, is_occupied 
            FROM Locations 
            WHERE location_code = ?
        """, (location_code,)).fetchone()
        
        # Act
        self.manager.update_package_status(barcode, "Delivered")
        
        # Assert
        package_after = self.manager.search_package(barcode)
        assert package_after['status'] == 'Delivered'
        
        is_occupied_after = self.db.cursor.execute("""
            SELECT is_occupied 
            FROM Locations 
            WHERE location_id = ?
        """, (location_id,)).fetchone()[0]
        
        assert is_occupied_before == 1
        assert is_occupied_after == 0

    # CP-FR4-007: Prevención de eliminación de paquete con audit trail
    def test_prevent_package_deletion_with_audit_trail(self):
        """Test foreign key constraint prevents deletion of packages with audit records"""
        # Arrange
        barcode = "PKG006"
        self.manager.register_package(barcode, 8.0, 18.0, 12.0, 10.0,
                                      "Portland, USA", "Standard")
        
        package = self.manager.search_package(barcode)
        package_id = package['package_id']
        
        audit_count = self.db.cursor.execute("""
            SELECT COUNT(*) 
            FROM AuditTrail 
            WHERE package_id = ?
        """, (package_id,)).fetchone()[0]
        
        assert audit_count > 0
        
        # Act & Assert
        with pt.raises(sqlite3.IntegrityError):
            self.db.cursor.execute(
                "DELETE FROM Packages WHERE package_id = ?", 
                (package_id,)
            )
            self.db.conn.commit()
        
        # Verify package still exists
        self.db.conn.rollback()
        package_check = self.manager.search_package(barcode)
        assert package_check is not None

    # CP-FR4-008: Búsqueda por categoría y estado
    @pt.mark.parametrize("category,status,expected_min", [
        ("Standard", "Stored", 5),
        ("Express", "Stored", 0),
    ])
    def test_search_by_category_and_status(self, category, status, expected_min):
        """Test searching packages by category and status"""
        # Arrange
        for i in range(5):
            barcode = f"STD{i:03d}"
            self.manager.register_package(barcode, 10.0, 20.0, 15.0, 10.0,
                                         f"City{i}", "Standard")
        
        # Act
        results = self.db.cursor.execute("""
            SELECT p.barcode, p.status, c.category_name
            FROM Packages p
            JOIN Categories c ON p.category_id = c.category_id
            WHERE c.category_name = ? AND p.status = ?
        """, (category, status)).fetchall()
        
        # Assert
        assert len(results) >= expected_min
        for result in results:
            assert result[1] == status

    # CP-FR4-009: Búsqueda por ubicación
    def test_search_by_location(self):
        """Test searching packages by location"""
        # Arrange
        test_location = self.db.cursor.execute("""
            SELECT location_code, location_id 
            FROM Locations 
            WHERE category_id = 1 
            LIMIT 1
        """).fetchone()
        
        location_code, location_id = test_location
        
        # Create 2 packages at this location
        for i in range(2):
            barcode = f"LOC{i:03d}"
            self.db.cursor.execute("""
                INSERT INTO Packages 
                (barcode, weight, length, width, height, destination, priority,
                 category_id, location_id, status)
                VALUES (?, 10.0, 20.0, 15.0, 10.0, 'TestCity', 'Standard', 1, ?, 'Stored')
            """, (barcode, location_id))
        
        self.db.cursor.execute("""
            UPDATE Locations SET is_occupied = 1 WHERE location_id = ?
        """, (location_id,))
        self.db.conn.commit()
        
        # Act
        packages = self.db.cursor.execute("""
            SELECT p.barcode, p.status, l.location_code
            FROM Packages p
            JOIN Locations l ON p.location_id = l.location_id
            WHERE l.location_code = ?
        """, (location_code,)).fetchall()
        
        # Assert
        assert len(packages) == 2
        for pkg in packages:
            assert pkg[2] == location_code

    # CP-FR4-010: Audit trail completo con notas
    def test_complete_audit_trail_with_notes(self):
        """Test audit trail records all fields including notes"""
        # Arrange
        barcode = "PKG010"
        self.manager.register_package(barcode, 14.0, 24.0, 20.0, 16.0,
                                      "Denver, USA", "Standard")
        
        custom_note = "Enviado a centro de distribución regional"
        
        # Act
        package = self.manager.search_package(barcode)
        self.db.cursor.execute("""
            INSERT INTO AuditTrail 
            (package_id, action, old_status, new_status, notes)
            VALUES (?, 'STATUS_UPDATE', 'Stored', 'In Transit', ?)
        """, (package['package_id'], custom_note))
        self.db.conn.commit()
        
        # Assert
        audit_record = self.db.cursor.execute("""
            SELECT action, old_status, new_status, timestamp, notes
            FROM AuditTrail
            WHERE package_id = ? AND action = 'STATUS_UPDATE'
        """, (package['package_id'],)).fetchone()
        
        assert audit_record is not None
        assert audit_record[0] == 'STATUS_UPDATE'
        assert audit_record[1] == 'Stored'
        assert audit_record[2] == 'In Transit'
        assert audit_record[3] is not None
        assert audit_record[4] == custom_note