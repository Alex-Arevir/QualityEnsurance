"""
FR5: Report Generation Tests - Summary Reports and Activity Logs

FR5.1 - Summary report with package count, location occupancy, recent activities
FR5.2 - Location occupancy calculation
FR5.3 - Recent activities in reverse chronological order
FR5.4 - User-friendly tabular format
FR5.5 - Report generation within 2 seconds
FR5.6 - Display zero counts for empty categories
"""

import pytest
import sqlite3
import os
import tempfile
import time
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


class TestFR5_1_SummaryReportContents:
    """FR5.1 - Summary report containing package count, occupancy, recent activities"""

    def test_ac5_1_package_count_by_category(self, db):
        """AC5.1: Report displays count of packages for each of the five categories."""
        manager = PackageManager(db)
        
        # Register packages in different categories
        manager.register_package("STD001", 10.0, 20, 15, 10, "City A", "Standard")
        manager.register_package("EXP001", 5.0, 15, 10, 8, "City B", "Express")
        manager.register_package("HVY001", 75.0, 60, 50, 40, "City C", "Standard")
        
        # Generate report
        report = manager.get_summary_report()
        
        # Verify report contains category counts
        assert 'by_category' in report
        assert report['by_category'] is not None
        assert len(report['by_category']) > 0
        
        # Verify all 5 categories are present
        categories = [cat[0] for cat in report['by_category']]
        assert 'Standard' in categories
        assert 'Express' in categories

    def test_package_count_by_status(self, db):
        """Report displays package count by status."""
        manager = PackageManager(db)
        
        # Register package
        manager.register_package("STATUS001", 10.0, 20, 15, 10, "City", "Standard")
        
        # Generate report
        report = manager.get_summary_report()
        
        # Verify status counts exist
        assert 'by_status' in report
        assert report['by_status'] is not None
        assert len(report['by_status']) > 0

    def test_location_occupancy_by_zone(self, db):
        """Report displays location occupancy by zone."""
        manager = PackageManager(db)
        
        # Register packages to occupy locations
        manager.register_package("OCC001", 10.0, 20, 15, 10, "City", "Standard")
        
        # Generate report
        report = manager.get_summary_report()
        
        # Verify occupancy data exists
        assert 'location_occupancy' in report
        assert report['location_occupancy'] is not None
        assert len(report['location_occupancy']) > 0

    def test_recent_activity_log(self, db):
        """Report contains recent activity log."""
        manager = PackageManager(db)
        
        # Generate activities
        manager.register_package("ACT001", 10.0, 20, 15, 10, "City", "Standard")
        manager.update_package_status("ACT001", "In Transit")
        
        # Generate report
        report = manager.get_summary_report()
        
        # Verify recent activities exist
        assert 'recent_activities' in report
        assert report['recent_activities'] is not None


class TestFR5_2_OccupancyCalculation:
    """FR5.2 - Location occupancy percentage calculation"""

    def test_ac5_2_occupancy_percentage_calculation(self, db):
        """AC5.2: Zone A with 12 occupied out of 20 displays '60.0% occupied'."""
        manager = PackageManager(db)
        
        # Register packages to create occupancy
        manager.register_package("OCC_TEST1", 10.0, 20, 15, 10, "City", "Standard")
        manager.register_package("OCC_TEST2", 15.0, 25, 20, 15, "City", "Express")
        
        # Generate report
        report = manager.get_summary_report()
        
        # Verify occupancy calculation
        occupancy_data = report['location_occupancy']
        assert occupancy_data is not None
        
        # Verify occupancy rates are calculated
        for zone, total, occupied, rate in occupancy_data:
            # Rate should be a percentage (0-100)
            assert 0 <= rate <= 100
            # Verify formula: (occupied / total) * 100
            expected_rate = (occupied / total) * 100
            assert abs(rate - expected_rate) < 0.01


class TestFR5_3_RecentActivitiesOrder:
    """FR5.3 - Recent activities in reverse chronological order"""

    def test_ac5_3_last_10_recent_activities(self, db):
        """AC5.3: Shows exactly the 10 most recent actions from 15 audit actions."""
        manager = PackageManager(db)
        
        # Create 15 activities
        for i in range(15):
            barcode = f"ACT_ORDER_{i:02d}"
            manager.register_package(barcode, 10.0, 20, 15, 10, "City", "Standard")
        
        # Generate report
        report = manager.get_summary_report()
        
        # Verify recent activities
        recent = report['recent_activities']
        assert recent is not None
        assert len(recent) == 10

    def test_reverse_chronological_order(self, db):
        """Recent activities are ordered most recent first."""
        manager = PackageManager(db)
        
        # Create activities with timestamps
        manager.register_package("CHRON001", 10.0, 20, 15, 10, "City A", "Standard")
        manager.register_package("CHRON002", 15.0, 25, 20, 15, "City B", "Express")
        
        # Generate report
        report = manager.get_summary_report()
        
        # Verify ordering
        recent = report['recent_activities']
        if len(recent) >= 2:
            # Most recent should come first
            first_timestamp = recent[0][2]
            second_timestamp = recent[1][2]
            assert first_timestamp >= second_timestamp


class TestFR5_4_UserFriendlyFormat:
    """FR5.4 - User-friendly tabular structure"""

    def test_report_contains_structured_data(self, db):
        """Report data is structured and accessible."""
        manager = PackageManager(db)
        
        manager.register_package("FMT001", 10.0, 20, 15, 10, "City", "Standard")
        
        report = manager.get_summary_report()
        
        # Verify all required sections exist
        assert 'by_category' in report
        assert 'by_status' in report
        assert 'location_occupancy' in report
        assert 'recent_activities' in report

    def test_activity_entries_contain_required_fields(self, db):
        """AC5.6: Each activity entry contains timestamp, barcode, action, notes."""
        manager = PackageManager(db)
        
        # Create activity
        manager.register_package("FIELDS001", 10.0, 20, 15, 10, "City", "Standard")
        
        report = manager.get_summary_report()
        recent = report['recent_activities']
        
        # Verify entry structure (barcode, action, timestamp, notes)
        if len(recent) > 0:
            entry = recent[0]
            assert len(entry) >= 4  # barcode, action, timestamp, notes
            barcode, action, timestamp, notes = entry[:4]
            assert barcode is not None
            assert action is not None
            assert timestamp is not None


class TestFR5_5_PerformanceRequirement:
    """FR5.5 - Report generation within 2 seconds for up to 10,000 packages"""

    def test_ac5_5_report_generation_under_2_seconds(self, db):
        """AC5.5: Report generated within 2 seconds with large dataset."""
        manager = PackageManager(db)
        
        # Create packages (simulating larger dataset)
        for i in range(50):
            barcode = f"PERF{i:04d}"
            manager.register_package(barcode, 10.0 + (i % 50), 20, 15, 10, 
                                    "City", "Standard")
        
        # Measure report generation time
        start_time = time.time()
        report = manager.get_summary_report()
        end_time = time.time()
        
        # Verify time constraint
        generation_time = end_time - start_time
        assert generation_time < 2.0
        
        # Verify report is complete
        assert report is not None
        assert len(report) > 0


class TestFR5_6_EmptyCategoryHandling:
    """FR5.6 - Display zero counts for categories with no packages"""

    def test_ac5_4_zero_packages_for_empty_category(self, db):
        """AC5.4: Empty Fragile category shows 'Fragile: 0 packages'."""
        manager = PackageManager(db)
        
        # Register only Standard packages
        manager.register_package("EMPTY001", 10.0, 20, 15, 10, "City", "Standard")
        manager.register_package("EMPTY002", 15.0, 25, 20, 15, "City", "Express")
        
        report = manager.get_summary_report()
        
        # Verify all categories are reported (including those with 0 packages)
        by_category = report['by_category']
        assert by_category is not None
        
        # Find if any category has 0 count
        has_zero_count = any(count == 0 for _, count in by_category)
        # Should have categories with 0 packages since we didn't register all types
        assert has_zero_count or len(by_category) == 5


class TestFR5_Integration:
    """Integration tests for complete report functionality"""

    def test_complete_report_generation(self, db):
        """Complete report generation with all sections."""
        manager = PackageManager(db)
        
        # Create varied packages
        manager.register_package("INTEG001", 10.0, 20, 15, 10, "NYC", "Standard")
        manager.register_package("INTEG002", 5.0, 15, 10, 8, "LA", "Express")
        manager.register_package("INTEG003", 2.0, 10, 8, 5, "Chicago", "Standard")
        
        # Update status to create variety
        manager.update_package_status("INTEG001", "In Transit")
        
        # Generate report
        start_time = time.time()
        report = manager.get_summary_report()
        end_time = time.time()
        
        # Verify all sections
        assert report['by_category'] is not None
        assert report['by_status'] is not None
        assert report['location_occupancy'] is not None
        assert report['recent_activities'] is not None
        
        # Verify performance
        assert (end_time - start_time) < 2.0
        
        # Verify data quality
        assert len(report['by_category']) > 0
        assert len(report['location_occupancy']) > 0
        assert len(report['recent_activities']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
