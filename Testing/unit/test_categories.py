"""
Test Suite for FR2 - Package Categorization System

This module tests the package categorization functionality according to:
- FR2.1: Five predefined categories (Standard, Express, Fragile, Heavy, International)
- FR2.2: Automatic category assignment rules
- FR2.3: Category information storage
- FR2.4: Retrieval of packages by category
- FR2.5: Unique zone designations (A, B, C, D, E)

Test Coverage:
- AC2.1 to AC2.7: Acceptance Criteria for categorization
"""

import pytest as pt
from distribution_center import DistributionCenterDB as DbC
from distribution_center import PackageManager as PkM
import os
from dotenv import load_dotenv

load_dotenv()
db_testing = os.getenv('DB_TESTING', 'testing_categories.db')


class TestCategoryDefinitions:
    """FR2.1 - Test five predefined categories exist with correct properties"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_standard_category_exists(self):
        """FR2.3 - Standard category should exist with correct properties"""
        # Arrange & Act
        self.db.cursor.execute(
            "SELECT category_name, description, zone, max_weight, priority_level FROM Categories WHERE category_id = 1"
        )
        result = self.db.cursor.fetchone()
        
        # Assert
        assert result is not None, "Standard category (id=1) should exist"
        category_name, description, zone, max_weight, priority_level = result
        assert category_name == 'Standard'
        assert zone == 'A'
        assert max_weight == 30.0
        assert priority_level == 3
    
    def test_express_category_exists(self):
        """FR2.3 - Express category should exist with correct properties"""
        # Arrange & Act
        self.db.cursor.execute(
            "SELECT category_name, description, zone, max_weight, priority_level FROM Categories WHERE category_id = 2"
        )
        result = self.db.cursor.fetchone()
        
        # Assert
        assert result is not None, "Express category (id=2) should exist"
        category_name, description, zone, max_weight, priority_level = result
        assert category_name == 'Express'
        assert zone == 'B'
        assert max_weight == 25.0
        assert priority_level == 1
    
    def test_fragile_category_exists(self):
        """FR2.3 - Fragile category should exist with correct properties"""
        # Arrange & Act
        self.db.cursor.execute(
            "SELECT category_name, description, zone, max_weight, priority_level FROM Categories WHERE category_id = 3"
        )
        result = self.db.cursor.fetchone()
        
        # Assert
        assert result is not None, "Fragile category (id=3) should exist"
        category_name, description, zone, max_weight, priority_level = result
        assert category_name == 'Fragile'
        assert zone == 'C'
        assert max_weight == 20.0
        assert priority_level == 2
    
    def test_heavy_category_exists(self):
        """FR2.3 - Heavy category should exist with correct properties"""
        # Arrange & Act
        self.db.cursor.execute(
            "SELECT category_name, description, zone, max_weight, priority_level FROM Categories WHERE category_id = 4"
        )
        result = self.db.cursor.fetchone()
        
        # Assert
        assert result is not None, "Heavy category (id=4) should exist"
        category_name, description, zone, max_weight, priority_level = result
        assert category_name == 'Heavy'
        assert zone == 'D'
        assert max_weight == 100.0
        assert priority_level == 4
    
    def test_international_category_exists(self):
        """FR2.3 - International category should exist with correct properties"""
        # Arrange & Act
        self.db.cursor.execute(
            "SELECT category_name, description, zone, max_weight, priority_level FROM Categories WHERE category_id = 5"
        )
        result = self.db.cursor.fetchone()
        
        # Assert
        assert result is not None, "International category (id=5) should exist"
        category_name, description, zone, max_weight, priority_level = result
        assert category_name == 'International'
        assert zone == 'E'
        assert max_weight == 50.0
        assert priority_level == 2
    
    def test_zone_uniqueness(self):
        """FR2.5 - Each category shall have unique zone designation (A, B, C, D, E)"""
        # Arrange & Act
        self.db.cursor.execute(
            "SELECT zone FROM Categories ORDER BY category_id"
        )
        zones = [row[0] for row in self.db.cursor.fetchall()]
        
        # Assert
        assert zones == ['A', 'B', 'C', 'D', 'E'], "Zones should be unique: A, B, C, D, E"
        assert len(zones) == len(set(zones)), "All zones should be unique"


class TestAutomaticCategorization:
    """FR2.2 - Test automatic category assignment based on rules"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_ac2_1_express_priority_categorization(self):
        """AC2.1 - Priority="Express" → Express category (id=2)"""
        # Arrange
        weight, length, width, height = 10.0, 10, 10, 10
        destination, priority = 'New York', 'Express'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 2, f"Expected category_id=2, got {category_id}"
        assert category_name == 'Express', f"Expected 'Express', got {category_name}"
    
    def test_ac2_2_heavy_weight_categorization(self):
        """AC2.2 - Weight=60kg, Priority="Standard" → Heavy category (id=4)"""
        # Arrange
        weight, length, width, height = 60.0, 30, 30, 30
        destination, priority = 'Domestic City', 'Standard'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 4, f"Expected category_id=4 (Heavy), got {category_id}"
        assert category_name == 'Heavy', f"Expected 'Heavy', got {category_name}"
    
    def test_ac2_3_fragile_weight_categorization(self):
        """AC2.3 - Weight=3kg, Priority="Standard" → Fragile category (id=3)"""
        # Arrange
        weight, length, width, height = 3.0, 5, 5, 5
        destination, priority = 'Boston', 'Standard'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 3, f"Expected category_id=3 (Fragile), got {category_id}"
        assert category_name == 'Fragile', f"Expected 'Fragile', got {category_name}"
    
    def test_ac2_4_international_destination_categorization(self):
        """AC2.4 - Destination="London, UK, International" → International category (id=5)"""
        # Arrange
        weight, length, width, height = 15.0, 20, 20, 20
        destination, priority = 'London, UK, International', 'Standard'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 5, f"Expected category_id=5 (International), got {category_id}"
        assert category_name == 'International', f"Expected 'International', got {category_name}"
    
    def test_ac2_5_standard_categorization(self):
        """AC2.5 - Weight=25kg, Priority="Standard", domestic → Standard category (id=1)"""
        # Arrange
        weight, length, width, height = 25.0, 20, 20, 20
        destination, priority = 'Los Angeles', 'Standard'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 1, f"Expected category_id=1 (Standard), got {category_id}"
        assert category_name == 'Standard', f"Expected 'Standard', got {category_name}"
    
    def test_ac2_6_priority_order_express_over_heavy(self):
        """AC2.6 - Express priority takes precedence over Heavy weight"""
        # Arrange - Package with both Express priority AND heavy weight
        weight, length, width, height = 100.0, 50, 50, 50  # Would be Heavy
        destination, priority = 'Paris', 'Express'  # But is Express
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert - Should prioritize Express over Heavy
        assert category_id == 2, f"Expected category_id=2 (Express), got {category_id}"
        assert category_name == 'Express'
    
    def test_ac2_6_priority_order_international_over_heavy(self):
        """AC2.6 - International takes precedence over Heavy weight"""
        # Arrange - Heavy package to international destination
        weight, length, width, height = 75.0, 40, 40, 40  # Would be Heavy
        destination, priority = 'Japan, Germany, USA', 'Standard'  # International
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert - Should prioritize International over Heavy
        assert category_id == 5, f"Expected category_id=5 (International), got {category_id}"
        assert category_name == 'International'
    
    def test_ac2_6_priority_order_international_over_fragile(self):
        """AC2.6 - International takes precedence over Fragile"""
        # Arrange - Light package to international destination
        weight, length, width, height = 2.0, 5, 5, 5  # Would be Fragile
        destination, priority = 'Paris, London', 'Standard'  # International
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert - Should prioritize International over Fragile
        assert category_id == 5, f"Expected category_id=5 (International), got {category_id}"
        assert category_name == 'International'
    
    @pt.mark.parametrize("weight", [50.1, 75.0, 100.0, 150.0])
    def test_heavy_weight_threshold(self, weight):
        """FR2.2 - Weight > 50.0 kg should be Heavy category"""
        # Arrange
        destination, priority = 'Domestic', 'Standard'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 4, f"Weight {weight}kg should be Heavy (id=4)"
        assert category_name == 'Heavy'
    
    @pt.mark.parametrize("weight", [0.1, 1.0, 3.5, 4.9])
    def test_fragile_weight_threshold(self, weight):
        """FR2.2 - Weight < 5.0 kg should be Fragile category"""
        # Arrange
        destination, priority = 'Domestic', 'Standard'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 3, f"Weight {weight}kg should be Fragile (id=3)"
        assert category_name == 'Fragile'
    
    @pt.mark.parametrize("destination", [
        'Paris, France, Italy',
        'Tokyo, Japan, South Korea',
        'Mexico, China, USA',
        'International',
        'london, uk, international'
    ])
    def test_international_destination_detection(self, destination):
        """FR2.2 - Destination with multiple commas or 'international' keyword"""
        # Arrange
        weight, priority = 20.0, 'Standard'
        
        # Act
        category_id, category_name = self.manager.categorize_package(
            weight, priority, destination
        )
        
        # Assert
        assert category_id == 5, f"Destination '{destination}' should be International"
        assert category_name == 'International'


class TestPackageRetrievalByCategory:
    """FR2.4 - Test retrieval of packages within specific category"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_retrieve_standard_packages(self):
        """AC2.7 - Query for Standard category packages should return all matching packages"""
        # Arrange - Register multiple Standard packages
        barcodes = ['111111111111', '222222222222', '333333333333']
        for barcode in barcodes:
            self.manager.register_package(
                barcode, 25.0, 20, 20, 20, 'Domestic', 'Standard'
            )
        
        # Act
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM Packages 
            WHERE category_id = 1
        """)
        count = self.db.cursor.fetchone()[0]
        
        # Assert
        assert count >= 3, f"Expected at least 3 Standard packages, got {count}"
    
    def test_retrieve_express_packages(self):
        """AC2.7 - Query for Express category packages"""
        # Arrange - Register Express packages
        barcodes = ['444444444444', '555555555555']
        for barcode in barcodes:
            self.manager.register_package(
                barcode, 10.0, 15, 15, 15, 'NYC', 'Express'
            )
        
        # Act
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM Packages 
            WHERE category_id = 2
        """)
        count = self.db.cursor.fetchone()[0]
        
        # Assert
        assert count >= 2, f"Expected at least 2 Express packages, got {count}"
    
    def test_retrieve_fragile_packages(self):
        """AC2.7 - Query for Fragile category packages"""
        # Arrange - Register Fragile packages
        barcodes = ['666666666666', '777777777777']
        for barcode in barcodes:
            self.manager.register_package(
                barcode, 3.0, 10, 10, 10, 'Miami', 'Standard'
            )
        
        # Act
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM Packages 
            WHERE category_id = 3
        """)
        count = self.db.cursor.fetchone()[0]
        
        # Assert
        assert count >= 2, f"Expected at least 2 Fragile packages, got {count}"
    
    def test_retrieve_heavy_packages(self):
        """AC2.7 - Query for Heavy category packages"""
        # Arrange - Register Heavy packages
        barcodes = ['888888888888', '999999999999']
        for barcode in barcodes:
            self.manager.register_package(
                barcode, 75.0, 60, 60, 60, 'Seattle', 'Standard'
            )
        
        # Act
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM Packages 
            WHERE category_id = 4
        """)
        count = self.db.cursor.fetchone()[0]
        
        # Assert
        assert count >= 2, f"Expected at least 2 Heavy packages, got {count}"
    
    def test_retrieve_international_packages(self):
        """AC2.7 - Query for International category packages"""
        # Arrange - Register International packages
        barcodes = ['101010101010', '121212121212']
        for barcode in barcodes:
            self.manager.register_package(
                barcode, 20.0, 25, 25, 25, 'Paris, France, USA', 'Standard'
            )
        
        # Act
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM Packages 
            WHERE category_id = 5
        """)
        count = self.db.cursor.fetchone()[0]
        
        # Assert
        assert count >= 2, f"Expected at least 2 International packages, got {count}"
    
    def test_retrieve_packages_by_category_with_details(self):
        """AC2.7 - Query should return package details with category"""
        # Arrange - Register a package
        barcode = '131313131313'
        self.manager.register_package(
            barcode, 25.0, 20, 20, 20, 'Domestic', 'Standard'
        )
        
        # Act
        self.db.cursor.execute("""
            SELECT p.barcode, c.category_name, p.weight, p.destination
            FROM Packages p
            JOIN Categories c ON p.category_id = c.category_id
            WHERE p.barcode = ?
        """, (barcode,))
        result = self.db.cursor.fetchone()
        
        # Assert
        assert result is not None
        pkg_barcode, category_name, weight, destination = result
        assert pkg_barcode == barcode
        assert category_name == 'Standard'
        assert weight == 25.0
        assert destination == 'Domestic'


class TestCategoryZoneAssociation:
    """FR2.5 - Test zone designation for each category"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_zones_created_for_all_categories(self):
        """FR2.5 - Zones should be created for each category"""
        # Arrange & Act
        self.db.cursor.execute("""
            SELECT category_id, category_name, zone FROM Categories
            ORDER BY category_id
        """)
        results = self.db.cursor.fetchall()
        
        # Assert
        expected = [
            (1, 'Standard', 'A'),
            (2, 'Express', 'B'),
            (3, 'Fragile', 'C'),
            (4, 'Heavy', 'D'),
            (5, 'International', 'E')
        ]
        assert results == expected, f"Expected zones {expected}, got {results}"
    
    def test_locations_exist_in_each_zone(self):
        """FR2.5 - Locations should exist in each zone"""
        # Arrange & Act
        self.db.cursor.execute("""
            SELECT DISTINCT zone FROM Locations
            ORDER BY zone
        """)
        zones = [row[0] for row in self.db.cursor.fetchall()]
        
        # Assert
        assert 'A' in zones
        assert 'B' in zones
        assert 'C' in zones
        assert 'D' in zones
        assert 'E' in zones
    
    @pt.mark.parametrize("zone,expected_count", [
        ('A', 20),  # 5 aisles * 4 shelves
        ('B', 20),
        ('C', 20),
        ('D', 20),
        ('E', 20)
    ])
    def test_locations_created_per_zone(self, zone, expected_count):
        """FR2.5 - Each zone should have locations created"""
        # Arrange & Act
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM Locations WHERE zone = ?
        """, (zone,))
        count = self.db.cursor.fetchone()[0]
        
        # Assert
        assert count == expected_count, f"Zone {zone} should have {expected_count} locations, got {count}"
