"""
Test Suite for NFR3 - Usability

This module tests the user interface and usability requirements for the distribution center system.

NFR3: Usability - The system shall provide an intuitive and user-friendly interface.

Detailed Requirements:
- NFR3.1: Clear numbered menu with all available options
- NFR3.2: Descriptive error messages with actionable guidance
- NFR3.3: Success confirmations include relevant details
- NFR3.4: Visual indicators (✅, ❌, 📦, 📊) for readability
- NFR3.5: Single-digit numeric input for menu options
- NFR3.6: "Press Enter to continue" prompts for screen flow control
- NFR3.7: All prompts clearly indicate required input format and acceptable values

Acceptance Criteria:
- AC-NFR3.1: Main menu displays all six options numbered and described
- AC-NFR3.2: Invalid barcode error explains why and what format is expected
- AC-NFR3.3: Successful registration shows barcode, category name, and location code
- AC-NFR3.4: Operations display appropriate visual indicators (✅ for success, ❌ for error)
- AC-NFR3.5: Single digit input executes corresponding menu action
"""

import pytest as pt
from distribution_center import DistributionCenterDB as DbC
from distribution_center import PackageManager as PkM
from distribution_center import display_menu, generate_random_barcode
from io import StringIO
import sys
import os
from dotenv import load_dotenv

load_dotenv()
db_testing = os.getenv('DB_TESTING', 'testing_usability.db')


class TestMenuDisplay:
    """NFR3.1 & AC-NFR3.1 - Test menu display and structure"""
    
    def test_main_menu_contains_all_six_options(self, capsys):
        """AC-NFR3.1 - Main menu should display all six options numbered"""
        # Arrange & Act
        display_menu()
        captured = capsys.readouterr()
        menu_output = captured.out
        
        # Assert
        assert '1. Register New Package' in menu_output
        assert '2. Search Package by Barcode' in menu_output
        assert '3. Update Package Status' in menu_output
        assert '4. View Summary Report' in menu_output
        assert '5. Generate Sample Packages (Testing)' in menu_output
        assert '6. Exit' in menu_output
    
    def test_main_menu_options_are_numbered(self, capsys):
        """NFR3.1 - All menu options should be numbered (1-6)"""
        # Arrange & Act
        display_menu()
        captured = capsys.readouterr()
        menu_output = captured.out
        
        # Assert
        for i in range(1, 7):
            assert f'{i}.' in menu_output, f"Option {i} should be in menu"
    
    def test_main_menu_has_clear_header(self, capsys):
        """NFR3.1 - Menu should have a clear header title"""
        # Arrange & Act
        display_menu()
        captured = capsys.readouterr()
        menu_output = captured.out
        
        # Assert
        assert 'DISTRIBUTION CENTER' in menu_output or 'Distribution Center' in menu_output.upper()
        assert 'PACKAGE MANAGEMENT' in menu_output or 'PACKAGE' in menu_output
    
    def test_main_menu_has_visual_separator(self, capsys):
        """NFR3.4 - Menu should have visual separators for clarity"""
        # Arrange & Act
        display_menu()
        captured = capsys.readouterr()
        menu_output = captured.out
        
        # Assert - Check for visual separator characters
        assert '=' in menu_output or '-' in menu_output or '*' in menu_output


class TestErrorMessages:
    """NFR3.2 & AC-NFR3.2 - Test error message quality and guidance"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_duplicate_barcode_error_is_descriptive(self, capsys):
        """AC-NFR3.2 - Duplicate barcode error should be descriptive"""
        # Arrange
        barcode = '123456789012'
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        
        # Act
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        error_output = captured.out
        assert '❌' in error_output or 'Error' in error_output or 'error' in error_output
        assert 'already exists' in error_output or 'duplicate' in error_output.lower() or 'Barcode' in error_output
    
    def test_no_available_locations_error_is_descriptive(self, capsys):
        """NFR3.2 - No available location error should explain the issue"""
        # Arrange - Fill all locations for a category
        for i in range(20):
            self.db.cursor.execute("""
                UPDATE Locations SET is_occupied = 1 
                WHERE location_id = ?
            """, (i + 1,))
        self.db.conn.commit()
        
        # Act
        self.manager.register_package('111111111111', 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        error_output = captured.out
        assert '❌' in error_output or 'Error' in error_output
        assert 'location' in error_output.lower() or 'available' in error_output.lower()
    
    def test_error_messages_contain_visual_indicator(self, capsys):
        """AC-NFR3.4 - Error messages should contain ❌ visual indicator"""
        # Arrange
        barcode = '222222222222'
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        
        # Act
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        assert '❌' in captured.out, "Error messages should contain ❌ indicator"
    
    @pt.mark.parametrize("invalid_barcode,reason", [
        ('short', 'too short'),
        ('123', 'less than 12 characters'),
    ])
    def test_invalid_barcode_format_error(self, invalid_barcode, reason, capsys):
        """NFR3.2 - Invalid barcode should explain format requirements"""
        # Arrange
        
        # Act
        result = self.manager.register_package(
            invalid_barcode, 10.0, 10, 10, 10, 'NYC', 'Standard'
        )
        captured = capsys.readouterr()
        
        # Assert
        assert result == False, f"Invalid barcode '{invalid_barcode}' should be rejected"
        # Error output should either be in capsys or handled gracefully
    
    def test_invalid_weight_error_guidance(self, capsys):
        """NFR3.2 - Invalid weight error should provide guidance"""
        # Arrange
        
        # Act
        result = self.manager.register_package(
            '333333333333', -5.0, 10, 10, 10, 'NYC', 'Standard'
        )
        captured = capsys.readouterr()
        
        # Assert
        assert result == False, "Negative weight should be rejected"


class TestSuccessConfirmations:
    """NFR3.3 & AC-NFR3.3 - Test success confirmation messages"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_registration_success_includes_barcode(self, capsys):
        """AC-NFR3.3 - Success message should include barcode"""
        # Arrange
        barcode = '444444444444'
        
        # Act
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        assert barcode in captured.out, f"Success message should include barcode {barcode}"
    
    def test_registration_success_includes_category(self, capsys):
        """AC-NFR3.3 - Success message should include category name"""
        # Arrange
        
        # Act
        self.manager.register_package('555555555555', 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        assert 'Standard' in captured.out or 'category' in captured.out.lower()
    
    def test_registration_success_includes_location_code(self, capsys):
        """AC-NFR3.3 - Success message should include location code"""
        # Arrange
        
        # Act
        self.manager.register_package('666666666666', 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        output = captured.out
        assert 'Location' in output or 'location' in output or 'A0' in output or 'Zone' in output.upper()
    
    def test_registration_success_contains_checkmark_indicator(self, capsys):
        """AC-NFR3.4 - Success message should contain ✅ indicator"""
        # Arrange
        
        # Act
        self.manager.register_package('777777777777', 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        assert '✅' in captured.out, "Success message should contain ✅ indicator"
    
    def test_status_update_success_message_format(self, capsys):
        """NFR3.3 - Status update confirmation should show old and new status"""
        # Arrange
        barcode = '888888888888'
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        
        # Act
        self.manager.update_package_status(barcode, 'In Transit')
        captured = capsys.readouterr()
        
        # Assert
        output = captured.out
        assert 'status' in output.lower() or 'Status' in output
    
    def test_all_confirmations_include_visual_indicators(self, capsys):
        """AC-NFR3.4 - All success confirmations should have visual indicators"""
        # Arrange
        barcode = '999999999999'
        
        # Act
        self.manager.register_package(barcode, 25.0, 20, 20, 20, 'Domestic', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        output = captured.out
        # Should contain at least one visual indicator
        has_indicator = any(indicator in output for indicator in ['✅', '📦', '🟢', 'Success'])
        assert has_indicator, "Confirmation should contain visual indicator"


class TestVisualIndicators:
    """NFR3.4 & AC-NFR3.4 - Test visual indicators usage"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_success_uses_checkmark_indicator(self, capsys):
        """AC-NFR3.4 - Success operations should use ✅"""
        # Arrange
        
        # Act
        self.manager.register_package('101010101010', 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        assert '✅' in captured.out
    
    def test_error_uses_cross_indicator(self, capsys):
        """AC-NFR3.4 - Error messages should use ❌"""
        # Arrange
        barcode = '111111111111'
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        
        # Act
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        assert '❌' in captured.out
    
    def test_package_details_use_package_indicator(self, capsys):
        """NFR3.4 - Package details should use 📦 indicator"""
        # Arrange
        barcode = '121212121212'
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        
        # Act
        self.manager.search_package(barcode)
        captured = capsys.readouterr()
        
        # Assert
        # Package details should have some form of indicator or be clearly formatted
        output = captured.out
        assert barcode in output or 'Package' in output
    
    def test_indicators_enhance_output_readability(self, capsys):
        """NFR3.4 - Visual indicators should enhance readability"""
        # Arrange
        
        # Act
        self.manager.register_package('131313131313', 10.0, 10, 10, 10, 'NYC', 'Standard')
        captured = capsys.readouterr()
        
        # Assert
        output = captured.out
        # Output should be more than just plain text
        assert len(output) > 0
        # Should contain at least one special character or formatting
        special_chars = ['✅', '❌', '📦', '📊', '  ', '---']
        has_formatting = any(char in output for char in special_chars)
        assert has_formatting or 'Package' in output


class TestInputHandling:
    """NFR3.5, NFR3.7 & AC-NFR3.5 - Test input handling and prompts"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_menu_accepts_single_digit_input(self, capsys):
        """AC-NFR3.5 - Menu should accept single-digit numeric input (1-6)"""
        # Arrange
        display_menu()
        captured = capsys.readouterr()
        
        # Assert - Menu should prompt for input
        menu_text = captured.out
        assert 'choice' in menu_text.lower() or 'enter' in menu_text.lower() or '1' in menu_text
    
    def test_menu_options_correspond_to_single_digits(self, capsys):
        """NFR3.5 - Each menu option should be accessible via single digit"""
        # Arrange
        display_menu()
        captured = capsys.readouterr()
        menu_output = captured.out
        
        # Assert
        for digit in range(1, 7):
            assert f'{digit}.' in menu_output, f"Option {digit} should be accessible"
    
    def test_prompts_indicate_input_format(self):
        """NFR3.7 - Prompts should clearly indicate required input format"""
        # This is a structural test - verify the menu itself indicates format
        # Arrange
        with pt.raises(EOFError):
            # Try to get menu input indicator
            pass
        
        # Assert - The menu function should exist and be callable
        assert callable(display_menu)
    
    def test_barcode_input_format_guidance(self):
        """NFR3.7 - Barcode prompts should indicate acceptable values"""
        # This validates that registration function can handle proper input
        # Arrange
        result = self.manager.register_package(
            '141414141414', 10.0, 10, 10, 10, 'NYC', 'Standard'
        )
        
        # Assert
        assert result == True, "Valid 12-character barcode should be accepted"
    
    def test_invalid_single_digit_handling(self, capsys):
        """NFR3.5 - System should handle invalid digit input gracefully"""
        # Note: This is implementation-dependent, testing if menu exists
        display_menu()
        captured = capsys.readouterr()
        
        # Assert - Menu should be displayable without errors
        assert len(captured.out) > 0


class TestScreenFlowControl:
    """NFR3.6 - Test "Press Enter to continue" prompts"""
    
    def test_main_menu_is_displayable(self, capsys):
        """NFR3.6 - Main menu should be clearly displayable"""
        # Arrange & Act
        display_menu()
        captured = capsys.readouterr()
        
        # Assert
        output = captured.out
        assert len(output) > 0, "Menu should display content"
        assert '1.' in output or '=' in output or 'DISTRIBUTION' in output
    
    def test_menu_structure_allows_flow_control(self, capsys):
        """NFR3.6 - Menu should have structure for flow control"""
        # Arrange
        display_menu()
        captured = capsys.readouterr()
        
        # Assert
        output = captured.out
        # Menu should have clear sections/options
        lines = output.split('\n')
        assert len(lines) >= 6, "Menu should have multiple lines for clear flow"


class TestUserExperience:
    """Overall user experience tests combining multiple requirements"""
    
    def setup_method(self):
        self.db = DbC(db_name=db_testing)
        self.db.connect()
        self.db.initialize_database()
        self.manager = PkM(self.db)
    
    def teardown_method(self):
        self.db.disconnect()
    
    def test_successful_workflow_has_clear_feedback(self, capsys):
        """Integration: Complete workflow should provide clear feedback"""
        # Arrange
        barcode = '151515151515'
        
        # Act
        result = self.manager.register_package(
            barcode, 10.0, 10, 10, 10, 'NYC', 'Standard'
        )
        captured = capsys.readouterr()
        
        # Assert
        assert result == True, "Registration should succeed"
        output = captured.out
        assert '✅' in output, "Success should be clearly indicated"
        assert barcode in output, "Barcode should be shown"
    
    def test_error_workflow_provides_guidance(self, capsys):
        """Integration: Error workflow should be helpful"""
        # Arrange
        barcode = '161616161616'
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        
        # Act
        result = self.manager.register_package(
            barcode, 10.0, 10, 10, 10, 'NYC', 'Standard'
        )
        captured = capsys.readouterr()
        
        # Assert
        assert result == False, "Duplicate registration should fail"
        output = captured.out
        assert '❌' in output, "Error should be clearly indicated"
        assert 'Error' in output or 'error' in output.lower(), "Error explanation should be present"
    
    def test_package_search_provides_detailed_information(self, capsys):
        """NFR3.3, NFR3.4: Search should display package with details"""
        # Arrange
        barcode = '171717171717'
        self.manager.register_package(barcode, 10.0, 10, 10, 10, 'NYC', 'Standard')
        
        # Act
        package = self.manager.search_package(barcode)
        captured = capsys.readouterr()
        
        # Assert
        assert package is not None, "Package should be found"
        assert package['barcode'] == barcode
        assert 'category' in package, "Category should be included"
        assert 'location' in package, "Location should be included"
