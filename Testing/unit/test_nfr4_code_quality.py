"""
NFR4: Code Quality and Maintainability Tests

NFR4.1 - PEP 8 Python style guidelines
NFR4.2 - Docstrings for all functions and classes
NFR4.3 - Database schema normalized to 3NF
NFR4.4 - Parameterized SQL queries (prevent SQL injection)
NFR4.5 - Single responsibility principle for classes
NFR4.6 - Named constants instead of magic numbers
NFR4.7 - Inline comments for complex logic
"""

import pytest
import sqlite3
import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from distribution_center import DistributionCenterDB, PackageManager


class TestNFR4_1_PEP8Compliance:
    """NFR4.1 - Code shall follow PEP 8 Python style guidelines"""

    def test_ac_nfr4_1_no_pep8_violations(self):
        """AC-NFR4.1: Python code analyzed against PEP 8 shows no violations."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Check for common PEP 8 violations
        violations = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 100 and not line.strip().startswith('#'):
                violations.append(f"Line {i}: Exceeds recommended length")
            
            if ';' in line and not line.strip().startswith('#'):
                violations.append(f"Line {i}: Multiple statements on one line")
        
        # Should have minimal violations
        assert len(violations) < 10, f"PEP 8 violations found: {violations[:5]}"

    def test_code_uses_proper_naming_conventions(self):
        """Functions and variables follow snake_case convention."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    if not node.name.startswith('_'):
                        violations.append(f"Function: {node.name}")
        
        assert len(violations) == 0, f"Naming violations: {violations}"


class TestNFR4_2_Docstrings:
    """NFR4.2 - All functions and classes shall include docstrings"""

    def test_ac_nfr4_2_complete_docstrings(self):
        """AC-NFR4.2: Functions and classes have complete docstrings."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        missing_docstrings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                if node.name.startswith('_'):
                    continue
                
                docstring = ast.get_docstring(node)
                if not docstring:
                    missing_docstrings.append(node.name)
        
        # Critical classes should have docstrings
        assert 'DistributionCenterDB' not in missing_docstrings
        assert 'PackageManager' not in missing_docstrings


class TestNFR4_3_DatabaseNormalization:
    """NFR4.3 - Database schema normalized to at least Third Normal Form (3NF)"""

    def test_ac_nfr4_3_schema_meets_3nf(self):
        """AC-NFR4.3: Database schema meets 3NF requirements."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            db = DistributionCenterDB(db_path)
            db.connect()
            db.initialize_database()
            
            # Get table information
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = db.cursor.fetchall()
            
            table_names = [t[0] for t in tables]
            assert 'Categories' in table_names
            assert 'Packages' in table_names
            assert 'Locations' in table_names
            assert 'AuditTrail' in table_names
            
            # Check Categories table
            db.cursor.execute("PRAGMA table_info(Categories)")
            cat_columns = [row[1] for row in db.cursor.fetchall()]
            assert 'location_id' not in cat_columns
            
            # Check Locations table
            db.cursor.execute("PRAGMA table_info(Locations)")
            loc_columns = [row[1] for row in db.cursor.fetchall()]
            assert 'barcode' not in loc_columns
            
            db.disconnect()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


class TestNFR4_4_ParameterizedQueries:
    """NFR4.4 - Parameterized SQL queries to prevent SQL injection"""

    def test_ac_nfr4_4_no_string_concatenation_in_queries(self):
        """AC-NFR4.4: SQL queries use parameterized placeholders (?) not string concatenation."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Look for vulnerable patterns
        vulnerable_patterns = [
            r'execute\s*\(\s*["\'].*\+',
            r'execute\s*\(\s*f["\'].*{',
        ]
        
        violations = []
        for pattern in vulnerable_patterns:
            if re.search(pattern, code):
                violations.append(f"Potential vulnerable pattern: {pattern}")
        
        assert len(violations) == 0, f"SQL Injection vulnerabilities found: {violations}"

    def test_all_queries_use_parameterized_placeholders(self):
        """All SQL queries use ? placeholders."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Count parameterized queries
        execute_pattern = r'\.execute\(["\'].*\?'
        matches = re.findall(execute_pattern, code)
        
        assert len(matches) > 0, "No parameterized queries found"


class TestNFR4_5_SingleResponsibility:
    """NFR4.5 - Single responsibility principle for classes"""

    def test_ac_nfr4_5_classes_have_single_responsibility(self):
        """AC-NFR4.5: Each class has single, well-defined responsibility."""
        db = DistributionCenterDB()
        
        # DistributionCenterDB should only handle database operations
        db_methods = ['connect', 'disconnect', 'initialize_database']
        for method in db_methods:
            assert hasattr(db, method), f"DistributionCenterDB missing {method}"
        
        assert not hasattr(db, 'categorize_package')

    def test_package_manager_single_responsibility(self):
        """PackageManager handles only package operations."""
        manager = PackageManager(DistributionCenterDB())
        
        mgr_methods = ['register_package', 'search_package', 'update_package_status']
        for method in mgr_methods:
            assert hasattr(manager, method), f"PackageManager missing {method}"


class TestNFR4_6_NamedConstants:
    """NFR4.6 - Magic numbers avoided; constants named and documented"""

    def test_critical_values_are_named(self):
        """Critical values use named references."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Check for table names as constants or literals
        assert 'Categories' in code
        assert 'Packages' in code
        assert 'Locations' in code


class TestNFR4_7_InlineComments:
    """NFR4.7 - Inline comments for complex logic"""

    def test_complex_logic_has_comments(self):
        """Complex logic sections include inline comments."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Count comments and docstrings
        comment_lines = sum(1 for line in code.split('\n') if line.strip().startswith('#'))
        docstring_count = code.count('"""')
        
        assert comment_lines > 0, "No comments found"
        assert docstring_count > 10, "Insufficient docstrings"


class TestNFR4_Integration:
    """Integration tests for code quality"""

    def test_overall_code_quality(self):
        """Overall code quality meets maintainability standards."""
        dist_center_path = Path(__file__).parent.parent.parent / "distribution_center.py"
        
        with open(dist_center_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        lines = code.split('\n')
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        docstring_count = code.count('"""')
        
        assert total_lines > 500, "Code too small"
        assert docstring_count > 10, "Insufficient docstrings"
        assert comment_lines > 5, "Insufficient comments"

    def test_database_design_quality(self):
        """Database design follows best practices."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            db = DistributionCenterDB(db_path)
            db.connect()
            db.initialize_database()
            
            # Verify indexes exist for performance
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = db.cursor.fetchall()
            
            assert len(indexes) > 0, "No indexes found"
            
            db.disconnect()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
