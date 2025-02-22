import pytest
from unittest.mock import MagicMock, patch
from spotisync.gui.main import MainWindow

@pytest.fixture
def main_window():
    with patch('spotisync.gui.main.QMainWindow'):
        window = MainWindow()
        yield window

def test_main_window_init(main_window):
    # Test that the main window is initialized correctly
    assert main_window is not None
    
@patch('spotisync.gui.main.QMessageBox')
def test_error_dialog(mock_message_box, main_window):
    # Test error dialog display
    error_message = "Test error message"
    main_window.show_error_dialog(error_message)
    
    mock_message_box.critical.assert_called_once()
    args = mock_message_box.critical.call_args[0]
    assert error_message in args

@patch('spotisync.gui.main.QFileDialog')
def test_file_dialog(mock_file_dialog, main_window):
    # Test file dialog functionality
    mock_file_dialog.getExistingDirectory.return_value = "/test/path"
    
    result = main_window.get_directory()
    assert result == "/test/path"
    mock_file_dialog.getExistingDirectory.assert_called_once()