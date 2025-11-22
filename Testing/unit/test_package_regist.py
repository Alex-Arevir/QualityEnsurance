import pytest as pt
from distribution_center import DistributionCenterDB as DbC
from distribution_center import PackageManager as PkM
import os
import random
import string
from dotenv import load_dotenv

load_dotenv()
db_testing = os.getenv('DB_TESTING')

class TestPackageManager:

    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)

    def teardown_method(self):
        self.db.disconnect()

    def test_new_package_barcode_12_characters(self):
        # Arrange
        barcode: str = '127654636453'

        # Act
        result = self.manager.register_package(barcode, 1, 10, 10, 10, 'Durango', 'standard')
        pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == True
        assert pkg is not None

    def test_register_existing_barcode(self):
        # Arrange
        barcode: str = '093940305971'

        # Act
        pkg1_result = self.manager.register_package(barcode, 1, 10, 10, 10, 'Durango', 'standard')
        pkg1 = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()
        pkg2_result = self.manager.register_package(barcode, 1, 10, 10, 10, 'Durango', 'standard')
        pkg2 = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert pkg1_result == True
        assert pkg1 is not None
        assert pkg2_result == False
        assert pkg2 is not None

    def test_new_package_barcode_less_than_12_characters(self):
        # Arrange
        barcode: str = '1746235'

        # Act
        result = self.manager.register_package(barcode, 1, 10, 10, 10, 'Durango', 'Standard')
        not_pkg = self.db.cursor.execute("SELECT barcode FROM packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == False
        assert not_pkg is None

    def test_new_package_barcode_numeric(self):
        # Arrange
        barcode: str = '241536476534'

        # Act
        result = self.manager.register_package(barcode, 1, 10, 10, 10, 'Durango', 'Standard')
        pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == True
        assert pkg is not None

    def test_new_package_barcode_alphanumeric(self):
        # Arrange
        barcode: str = '8q41e647a534'

        # Act
        result = self.manager.register_package(barcode, 1, 10, 10, 10, 'Durango', 'Standard')
        not_pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == False
        assert not_pkg is None

    def test_new_package_attribute_equal_zero(self):
        # Arrange
        barcode: str = '778374655412'
        weight: int = 0

        # Act
        result = self.manager.register_package(barcode, weight, 10, 10, 10, 'Durango', 'Standard')
        not_pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == False
        assert not_pkg is None

    def test_new_package_attribute_less_than_zero(self):
        # Arrange
        barcode: str = '1092212987'
        weight: int = -4

        # Act
        result = self.manager.register_package(barcode, weight, 10, 10, 10, 'Durango', 'Standard')
        not_pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == False
        assert not_pkg is None

    def test_new_package_numeric_destination(self):
        # Arrange
        barcode: str = '277654362546'
        destination: str = '1324423'

        # Act
        result = self.manager.register_package(barcode, 0, 10, 10, 10, destination, 'Standard')
        not_pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == False
        assert not_pkg is None
    
    def test_new_package_correct_type_attribute(self):
        # Arrange
        barcode: str = '188776453625'
        weight: float = 10
        length: float = 10
        width: float = 10
        height: float = 10
        destination: str = 'Durango'
        priority: str = 'Standard'

        # Act
        result = self.manager.register_package(barcode, weight, length, width, height, destination, priority)
        pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == True
        assert pkg is not None

    def test_new_package_incorrect_type_attribute(self):
        # Arrange
        barcode: str = '266478900987'
        weight: str = 'twenty'
        length: float = 10
        width: float = 10
        height: float = 10
        destination: str = 'Durango'
        priority: str = 'Standard'

        # Act
        result = self.manager.register_package(barcode, weight, length, width, height, destination, priority)
        not_pkg = self.db.cursor.execute("SELECT barcode FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == False
        assert not_pkg is None

    @pt.mark.parametrize("weight, expected", [
        (1, 'Fragile'),
        (4.5, 'Fragile'),
    ])

    def test_categorize_fragile_category(self, weight, expected):
        # Arrange

        # Act
        result = self.manager.categorize_package(weight, 'Standard', 'Durango')

        # Assert
        assert result[1] == expected

    @pt.mark.parametrize("weight, expected", [
        (11129, 'Heavy'),
        (66, 'Heavy'),
    ])
    def test_categorize_heavy_category(self, weight, expected):
        # Arrange

        # Act
        result = self.manager.categorize_package(weight, 'Standard', 'Durango')

        # Assert
        assert result[1] == expected

    @pt.mark.parametrize("weight, expected", [
        (292, 'Express'),
        (8, 'Express'),
    ])
    def test_categorize_express_category(self, weight, expected):
        # Arrange

        # Act
        result = self.manager.categorize_package(weight, 'Express', 'Durango')

        # Assert
        assert result[1] == expected

    @pt.mark.parametrize("weight, expected, destiny", [
        (1, 'International', 'Mexico, China, USA'),
        (4, 'International', 'international'),
    ])
    def test_categorize_international_category(self, weight, expected, destiny):
        # Arrange

        # Act
        result = self.manager.categorize_package(weight, 'Standard' , destiny)

        # Assert
        assert result[1] == expected

    @pt.mark.parametrize("weight, expected", [
        (9, 'Standard'),
        (8, 'Standard'),
    ])
    def test_categorize_standard_category(self, weight, expected):
        # Arrange

        # Act
        result = self.manager.categorize_package(weight, 'Standard', 'Durango')

        # Assert
        assert result[1] == expected

    def test_available_location_space(self):
        # Arrange
        global location

        # Act
        location = self.manager.find_available_location(1)

        # Assert
        assert location is not None

    def test_unavailable_location_space(self):
        # Arrange
        global location

        # Act
        for i in range(21):
            self.db.cursor.execute('''
                UPDATE Locations SET is_occupied = 1 
                WHERE location_id = ?''', (i,))
        location = self.manager.find_available_location(1)

        # Assert
        assert location is None

    def test_registration_with_timestamp(self):
        # Arrange
        barcode: str = '888888776898'
        weight: float = 10
        length: float = 10
        width: float = 10
        height: float = 10
        destination: str = 'Durango'
        priority: str = 'Standard'

        # Act
        result = self.manager.register_package(barcode, weight, length, width, height, destination, priority)
        pkg = self.db.cursor.execute("SELECT received_at FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == True
        assert pkg is not None

    def test_registration_status_received(self):
        # Arrange
        barcode: str = '000999876542'
        weight: float = 10
        length: float = 10
        width: float = 10
        height: float = 10
        destination: str = 'Durango'
        priority: str = 'Standard'

        # Act
        result = self.manager.register_package(barcode, weight, length, width, height, destination, priority)
        pkg = self.db.cursor.execute("SELECT status FROM Packages WHERE barcode=?", (barcode,)).fetchone()

        # Assert
        assert result == True
        assert pkg[0] == 'Received'