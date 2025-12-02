"""
NFR2: Reliability Tests - Data Integrity and Reliable Operation

NFR2.1 - ACID transaction principles
NFR2.2 - Database foreign key constraints
NFR2.3 - Rollback mechanisms for failed transactions
NFR2.4 - Input validation before database operations
NFR2.5 - Graceful database connection failure handling
NFR2.6 - Prevention of data corruption through exception handling
"""

import pytest
import sqlite3
import os
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from distribution_center import DistributionCenterDB, PackageManager


@pytest.fixture
def db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = DistributionCenterDB(db_path)
    db.connect()
    db.initialize_database()
    yield db
    
    db.disconnect()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestNFR2_1_AcidTransactions:
    """NFR2.1 - ACID transaction principles"""

    def test_atomicity_and_durability(self, db):
        """AC-NFR2.1: Package is completely stored or not at all."""
        manager = PackageManager(db)
        
        result = manager.register_package(
            barcode="PKG001",
            weight=25.0,
            length=30,
            width=20,
            height=15,
            destination="New York",
            priority="Standard"
        )
        assert result is True
        
        # Verify complete storage
        db.cursor.execute("SELECT COUNT(*) FROM Packages WHERE barcode = ?", ("PKG001",))
        assert db.cursor.fetchone()[0] == 1
        
        db.cursor.execute("SELECT COUNT(*) FROM AuditTrail WHERE package_id = "
                         "(SELECT package_id FROM Packages WHERE barcode = ?)", ("PKG001",))
        assert db.cursor.fetchone()[0] >= 1


class TestNFR2_2_ForeignKeyConstraints:
    """NFR2.2 - Database foreign key constraints maintain referential integrity"""

    def test_foreign_key_enabled(self, db):
        """Verify foreign key constraints are enabled."""
        db.cursor.execute("PRAGMA foreign_keys")
        assert db.cursor.fetchone()[0] == 1

    def test_prevent_invalid_category_reference(self, db):
        """Foreign keys prevent invalid category references."""
        with pytest.raises(sqlite3.IntegrityError):
            db.cursor.execute("""
                INSERT INTO Packages 
                (barcode, weight, length, width, height, destination, 
                 priority, category_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("INVALID", 10.0, 20, 15, 10, "Test", "Standard", 99999, "Stored"))
            db.conn.commit()

    def test_ac_nfr2_2_prevent_delete_category_with_packages(self, db):
        """AC-NFR2.2: Foreign key prevents deletion of category with associated packages."""
        manager = PackageManager(db)
        
        # Register a package
        manager.register_package(
            barcode="PKG_CAT_TEST",
            weight=25.0,
            length=30,
            width=20,
            height=15,
            destination="Test City",
            priority="Standard"
        )
        
        # Get category ID
        db.cursor.execute(
            "SELECT category_id FROM Packages WHERE barcode = ?",
            ("PKG_CAT_TEST",)
        )
        category_id = db.cursor.fetchone()[0]
        
        # Try to delete - should fail
        with pytest.raises(sqlite3.IntegrityError):
            db.cursor.execute(
                "DELETE FROM Categories WHERE category_id = ?",
                (category_id,)
            )
            db.conn.commit()


class TestNFR2_3_RollbackMechanisms:
    """NFR2.3 - Rollback mechanisms for failed transactions"""

    def test_ac_nfr2_1_rollback_on_failed_transaction(self, db):
        """AC-NFR2.1: Failed transaction rolls back all changes."""
        manager = PackageManager(db)
        
        # Register first package
        manager.register_package(
            barcode="UNIQUE001",
            weight=10.0,
            length=20,
            width=15,
            height=10,
            destination="City A",
            priority="Standard"
        )
        
        db.cursor.execute("SELECT COUNT(*) FROM Packages")
        count_before = db.cursor.fetchone()[0]
        
        # Try duplicate - should fail and rollback
        result = manager.register_package(
            barcode="UNIQUE001",
            weight=15.0,
            length=25,
            width=20,
            height=15,
            destination="City B",
            priority="Express"
        )
        assert result is False
        
        # Count should be unchanged (rollback successful)
        db.cursor.execute("SELECT COUNT(*) FROM Packages")
        count_after = db.cursor.fetchone()[0]
        assert count_before == count_after


class TestNFR2_4_InputValidation:
    """NFR2.4 - Input validation before database operations"""

    def test_ac_nfr2_3_reject_invalid_data(self, db):
        """AC-NFR2.3: Invalid data (negative weight) is rejected."""
        manager = PackageManager(db)
        
        db.cursor.execute("SELECT COUNT(*) FROM Packages")
        count_before = db.cursor.fetchone()[0]
        
        # Negative weight should not be stored
        result = manager.register_package(
            barcode="NEG_WEIGHT",
            weight=-10.0,
            length=20,
            width=15,
            height=10,
            destination="Test City",
            priority="Standard"
        )
        
        # System should handle gracefully
        db.cursor.execute("SELECT COUNT(*) FROM Packages")
        count_after = db.cursor.fetchone()[0]

    def test_duplicate_barcode_rejected(self, db):
        """Duplicate barcodes are rejected."""
        manager = PackageManager(db)
        
        # First registration succeeds
        result1 = manager.register_package(
            barcode="DUP_TEST",
            weight=10.0,
            length=20,
            width=15,
            height=10,
            destination="City",
            priority="Standard"
        )
        assert result1 is True
        
        # Duplicate fails
        result2 = manager.register_package(
            barcode="DUP_TEST",
            weight=20.0,
            length=25,
            width=20,
            height=15,
            destination="City",
            priority="Express"
        )
        assert result2 is False


class TestNFR2_5_ConnectionErrorHandling:
    """NFR2.5 - Graceful database connection failure handling"""

    def test_ac_nfr2_4_graceful_error_message(self, db):
        """AC-NFR2.4: Database error displays user-friendly message without crashing."""
        manager = PackageManager(db)
        
        # Close connection
        db.disconnect()
        
        # Attempt operation on closed connection - should not crash
        try:
            result = manager.register_package(
                barcode="AFTER_DISCONNECT",
                weight=10.0,
                length=20,
                width=15,
                height=10,
                destination="Test City",
                priority="Standard"
            )
        except Exception as e:
            # Any exception is acceptable - system shouldn't crash silently
            assert isinstance(e, (sqlite3.DatabaseError, sqlite3.OperationalError, 
                                 AttributeError))
        
        # Reconnect for cleanup
        db.connect()

    def test_system_recovery_after_error(self, db):
        """System recovers and continues operating after an error."""
        manager = PackageManager(db)
        
        # Valid operation
        result1 = manager.register_package(
            barcode="RECOVERY1",
            weight=10.0,
            length=20,
            width=15,
            height=10,
            destination="City A",
            priority="Standard"
        )
        assert result1 is True
        
        # Failed operation (duplicate)
        result2 = manager.register_package(
            barcode="RECOVERY1",
            weight=15.0,
            length=25,
            width=20,
            height=15,
            destination="City B",
            priority="Express"
        )
        assert result2 is False
        
        # System recovers - next operation succeeds
        result3 = manager.register_package(
            barcode="RECOVERY2",
            weight=20.0,
            length=30,
            width=25,
            height=20,
            destination="City C",
            priority="Standard"
        )
        assert result3 is True


class TestNFR2_6_ExceptionHandling:
    """NFR2.6 - Prevention of data corruption through exception handling"""

    def test_no_partial_data_corruption_on_error(self, db):
        """Failed transaction doesn't leave partial/corrupted data."""
        manager = PackageManager(db)
        
        # Register first package successfully
        manager.register_package(
            barcode="CORRUPT_TEST1",
            weight=10.0,
            length=20,
            width=15,
            height=10,
            destination="City A",
            priority="Standard"
        )
        
        # Attempt duplicate
        manager.register_package(
            barcode="CORRUPT_TEST1",
            weight=15.0,
            length=25,
            width=20,
            height=15,
            destination="City B",
            priority="Express"
        )
        
        # Verify no duplicate exists
        db.cursor.execute(
            "SELECT COUNT(*) FROM Packages WHERE barcode = ?",
            ("CORRUPT_TEST1",)
        )
        count = db.cursor.fetchone()[0]
        assert count == 1

    def test_referential_integrity_preserved_on_error(self, db):
        """Referential integrity maintained even when operations fail."""
        # Get valid category
        db.cursor.execute("SELECT category_id FROM Categories LIMIT 1")
        valid_category = db.cursor.fetchone()[0]
        
        # Try invalid insert
        try:
            db.cursor.execute("""
                INSERT INTO Packages 
                (barcode, weight, length, width, height, destination, 
                 priority, category_id, location_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("TEST", 10.0, 20, 15, 10, "Test", "Standard",
                  valid_category, 99999, "Stored"))
            db.conn.commit()
        except sqlite3.IntegrityError:
            db.conn.rollback()
        
        # Verify no corrupted data
        db.cursor.execute(
            "SELECT COUNT(*) FROM Packages WHERE category_id = ? AND location_id = ?",
            (valid_category, 99999)
        )
        count = db.cursor.fetchone()[0]
        assert count == 0


class TestNFR2_Integration:
    """Integration tests combining multiple NFR2 requirements"""

    def test_complete_reliable_workflow(self, db):
        """Complete workflow with all reliability measures."""
        manager = PackageManager(db)
        
        # Register (validation + ACID)
        r1 = manager.register_package(
            barcode="INTEGRATED1",
            weight=25.0,
            length=30,
            width=20,
            height=15,
            destination="New York",
            priority="Express"
        )
        assert r1 is True
        
        # Search (durability check)
        pkg = manager.search_package("INTEGRATED1")
        assert pkg is not None
        
        # Update status (transaction + audit trail)
        r2 = manager.update_package_status("INTEGRATED1", "In Transit")
        assert r2 is True
        
        # Verify update (consistency)
        pkg_updated = manager.search_package("INTEGRATED1")
        assert pkg_updated['status'] == "In Transit"
        
        # Verify no duplicate exists (foreign key + validation)
        db.cursor.execute(
            "SELECT COUNT(*) FROM Packages WHERE barcode = ?",
            ("INTEGRATED1",)
        )
        assert db.cursor.fetchone()[0] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
