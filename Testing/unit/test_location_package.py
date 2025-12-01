import pytest as pt
import os
import string
import distribution_center as dc
from dotenv import load_dotenv


load_dotenv()
db_testing = os.getenv('DB_TESTING')

class TestLocation:

    def setup_method(self):
        self.db = dc.DistributionCenterDB(db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.pkg = dc.PackageManager(self.db)
    
    def teardown_method(self):
        self.db.disconnect()

    @pt.mark.parametrize("weight, priority, destiny, wanted",[
        (6, 'standard', 'Durango', 'A'),
        (1, 'standard', 'Durarngo', 'C'),
        (51, 'standard', 'Durango', 'D'),
        (100, 'express', 'Durango', 'B'),
        (100, 'standard', 'international', 'E'),
        (100, 'standard', 'Mexico, Rusia, Japan', 'E')
    ])
    def test_category_location(self, weight, priority, wanted, destiny):
        #arrange
        barcode: str = '277647365462'
        weight: int = weight
        length: int = 10
        width: int = 10
        height: int = 10
        destiny: str = destiny
        priority: str = priority

        #act
        self.pkg.register_package(barcode, weight, length, width, height, destiny, priority)
        location_id = self.db.cursor.execute(
            """
            SELECT location_id from Packages where barcode = ?
            """,
            (barcode,)
        ).fetchone()
        zone_pattern = wanted + '%'
        location = self.db.cursor.execute(
            f"""
            SELECT * from Locations 
            WHERE location_id = ? AND zone LIKE ?
            """,
            (location_id[0], zone_pattern, )
        ).fetchone()
        location_zone = location[1]

        #assert
        assert location is not None
        assert location_zone.startswith(wanted)
    
    def test_no_location_available(self):
        #arrange
        weight: int = 1
        length: int = 10
        width: int = 10
        height: int = 10
        destiny: str = 'Durango'
        priority: str = 'standard'

        #act
        for i in range(20):
            barcode: str = dc.generate_random_barcode()
            self.pkg.register_package(barcode, weight, length, width, height, destiny, priority)
            category_id = self.db.cursor.execute(
                """
                SELECT category_id FROM Packages where barcode = ?
                """,
                (barcode, )
            ).fetchone()
        location = self.pkg.find_available_location(category_id[0])

        #assert
        assert location is None
    
    def test_concurrency_register(self):
        #arrange
        weight: int = 1
        length: int = 10
        width: int = 10
        height: int = 10
        destiny: str = 'Durango'
        priority: str = 'standard'

        #act
        barcode_1: str = dc.generate_random_barcode()
        register_1 = self.pkg.register_package(barcode_1, weight, length, width, height, destiny, priority)        

        barcode_2: str = dc.generate_random_barcode()
        register_2 = self.pkg.register_package(barcode_2, weight, length, width, height, destiny, priority)
        
        query = """
            SELECT location_id
            FROM Packages
            WHERE barcode = ?
            """
        package_1 = self.db.cursor.execute(
            query,
            (barcode_1, )
        ).fetchone()[0]

        package_2 = self.db.cursor.execute(
            query,
            (barcode_2, )
        ).fetchone()[0]

        #assert
        assert package_1 != package_2
    
    def test_flag_is_ocuppied(self):
        #arrange
        barcode: str = '277647365462'
        weight: int = 1
        length: int = 10
        width: int = 10
        height: int = 10
        destiny: str = 'Durango'
        priority: str = 'standard'

        #act
        self.pkg.register_package(barcode, weight, length, width, height, destiny, priority)
        location_id = self.db.cursor.execute(
            """
            SELECT location_id
            FROM Packages
            WHERE barcode = ?
            """,
            (barcode,)
        ).fetchone()[0]
        occupied_status = self.db.cursor.execute(
            """
            SELECT is_occupied
            FROM Locations
            WHERE location_id = ?
            """,
            (location_id, )
        ).fetchone()[0]

        #assert
        assert occupied_status == 1

    def test_mmark_as_occupied(self):
        #arrange
        barcode: str = '277647365462'
        weight: int = 1
        length: int = 10
        width: int = 10
        height: int = 10
        destiny: str = 'Durango'
        priority: str = 'standard'
        new_status: str = 'Delivered' 

        #act
        self.pkg.register_package(barcode, weight, length, width, height, destiny, priority)
        location_id = self.db.cursor.execute(
            """
            SELECT location_id
            FROM Packages
            WHERE barcode = ?
            """,
            (barcode,)
        ).fetchone()[0]

        self.pkg.update_package_status(barcode, new_status)

        occupied_status = self.db.cursor.execute(
            """
            SELECT is_occupied
            FROM Locations
            WHERE location_id = ?
            """,
            (location_id, )
        ).fetchone()[0]

        #assertation_id = ?
        assert occupied_status == 0
    
    def test_return_only_available_locations(self):
        #arrange
        category_id = 1

        #act
        location_id = self.pkg.find_available_location(category_id)
        is_occupied = self.db.cursor.execute(
            """
            SELECT is_occupied
            FROM Locations
            WHERE location_id = ?
            """,
            (location_id, )
        ). fetchone()

        #assert
        assert is_occupied[0] == 0 
    
    @pt.mark.parametrize('wanted',(
        ('A'),
        ('B'),
        ('C'),
        ('D'),
        ('E')
    ))
    def test_total_zones(self, wanted):
        #arrange
        
        #act
        locations = self.db.cursor.execute(
            """
            SELECT zone
            FROM Locations
            WHERE zone = ?
            """,
            (wanted, )
        ).fetchall()
        total_zones: int = 0
        for zone in locations:
            if zone[0] == wanted:
                total_zones += 1

        #assert
        assert (100 / total_zones) == 5 
    
    @pt.mark.parametrize('wanted',(
        ('A'),
        ('B'),
        ('C'),
        ('D'),
        ('E')
    ))
    def test_total_zone_location(self, wanted):
        #arrange

        #act
        locations = self.db.cursor.execute(
            """
            SELECT zone
            FROM Locations
            WHERE zone = ?
            """,
            (wanted, )
        ).fetchall()
        total_zones: int = 0
        for zone in locations:
            if zone[0] == wanted:
                total_zones += 1

        #assert
        assert total_zones == 20

    @pt.mark.parametrize('zone',[
        ('A'),
        ('B'),
        ('C'),
        ('D'),
        ('E')
    ])
    def test_db_location_specifications(self, zone):
        #arrange
        zone_pattern: str = f'{zone}0%'
        shelf_pattern: str = f'{zone}01-%'

        #act
        aisles = self.db.cursor.execute(
            """
            SELECT *
            FROM Locations
            WHERE location_code LIKE ?
            """,
            (zone_pattern, )
        ).fetchall()
        shelfs = self.db.cursor.execute(
            """
            SELECT *
            FROM Locations
            WHERE location_code LIKE ?
            """,
            (shelf_pattern, )
        ).fetchall()
        total_aisles: int = len(aisles) // 4
        total_shelfs: int = len(shelfs)

        #assert
        assert total_aisles == 5
        assert total_shelfs == 4
    