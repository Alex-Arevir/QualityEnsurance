import sys, os, time

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from distribution_center import DistributionCenterDB, PackageManager, generate_random_barcode

DB_TEST_NAME = "scalability_lab.db"

class TestScalability:
    """
    NFR-5 Scalability Test
    """

    def setup_method(self):
        """Prepare a clean environment."""
        self.db_path = os.path.join(current_dir, DB_TEST_NAME)
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
        
        self.db = DistributionCenterDB(db_name=self.db_path)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PackageManager(self.db)
    
    def teardown_method(self):
        self.db.disconnect()

    def _register_varied_packages(self, count):
        """Helper to fill all zones."""
        registered = 0
        for i in range(count):
            barcode = generate_random_barcode()
            strategy = i % 5 
            w, l, h, wid = 10.0, 10, 10, 10
            dest, prio = "City", "Standard"

            if strategy == 1: prio = "Express"
            elif strategy == 2: w = 1.0
            elif strategy == 3: w = 60.0
            elif strategy == 4: dest = "City, Country, Int"

            if self.manager.register_package(barcode, w, l, wid, h, dest, prio):
                registered += 1
        return registered

    # ===========================================================================
    # ST-01: Volume Load Latency
    # ===========================================================================
    def test_st01_volume_load_latency(self):
        print("\n[ST-01] Testing Latency...")
        start_time = time.time()
        self._register_varied_packages(50)
        total_time = time.time() - start_time
        avg_time_ms = (total_time / 50) * 1000
        print(f"\t-> Avg Time: {avg_time_ms:.2f}ms")
        
        assert avg_time_ms < 10, f"FAIL: Latency too high! Got {avg_time_ms:.2f}ms, expected < 10ms"

    # ===========================================================================
    # ST-02: Warehouse Saturation Point (Scalability Check)
    # ===========================================================================
    def test_st02_warehouse_scalability(self):
        print("\n[ST-02] Testing Unlimited Scalability...")
        
        target_growth = 200
        registered = self._register_varied_packages(target_growth)
        print(f"\t-> Registered: {registered}/{target_growth}")
        
        assert registered >= target_growth, \
            f"System capped at {registered} items. Violation of NFR-5 (Future Growth)."

    # ===========================================================================
    # ST-03: Audit Log Integrity
    # ===========================================================================
    def test_st03_audit_log_integrity(self):
        print("\n[ST-03] Testing Log Consistency...")
        self._register_varied_packages(50)
        self.db.cursor.execute("SELECT COUNT(*) FROM AuditTrail")
        audit_count = self.db.cursor.fetchone()[0]
        
        assert audit_count == 50, f"BUG: Data Loss in Logs! Expected 50, got {audit_count}"

    # ===========================================================================
    # ST-04: Search Performance Under Load
    # ===========================================================================
    def test_st04_search_performance_under_load(self):
        print("\n[ST-04] Testing Search Speed...")
        self._register_varied_packages(100)
        target_bc = generate_random_barcode()
        registered = self.manager.register_package(target_bc, 10.0, 10, 10, 10, "City", "Standard")

        assert registered is True, "FAIL: Cannot insert new item to search. DB Full."
        
        start_time = time.time()
        self.manager.search_package(target_bc)
        search_time_ms = (time.time() - start_time) * 1000
        
        assert search_time_ms < 50, f"FAIL: Search slow! {search_time_ms}ms"

    # ===========================================================================
    # ST-05: Resource Reclamation Cycle
    # ===========================================================================
    def test_st05_resource_reclamation_cycle(self):
        print("\n[ST-05] Testing Memory Leaks/Reclamation...")

        self._register_varied_packages(100)
        self.db.cursor.execute("UPDATE Packages SET status='Delivered' WHERE category_id=4 LIMIT 5")
        self.db.conn.commit()
        
        barcodes = [row[0] for row in self.db.cursor.execute("SELECT barcode FROM Packages LIMIT 5").fetchall()]
        for bc in barcodes:
            self.manager.update_package_status(bc, "Delivered")
            
        reclaimed = 0
        for _ in range(5):
            if self.manager.register_package(generate_random_barcode(), 10.0, 10, 10, 10, "City", "Express"):
                reclaimed += 1
        
        assert reclaimed == 5, f"FAIL: Rigidity detected. Deleted 5 items but could only reuse {reclaimed} slots for different category."

    # ===========================================================================
    # ST-06: History Reporting Stress
    # ===========================================================================
    def test_st06_history_reporting_stress(self):
        print("\n[ST-06] Testing Report Gen...")
        bc = generate_random_barcode()
        self.manager.register_package(bc, 10.0, 10, 10, 10, "City", "Standard")

        for _ in range(100):
            self.manager.update_package_status(bc, "In Transit")

        start_time = time.time()
        self.manager.get_summary_report()
        gen_time = time.time() - start_time
        
        assert gen_time < 0.05, f"FAIL: Reporting sluggish under load. {gen_time:.4f}s"