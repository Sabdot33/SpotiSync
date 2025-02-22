"""SpotiSync GUI Module

This module provides the graphical user interface components for the SpotiSync application.
It includes the main window, dialogs, and custom widgets.
"""

from .main import MainWindow
from .popups import show_error_message
from .pyqtSwitch import PyQtSwitch

__all__ = ['MainWindow', 'show_error_message', 'PyQtSwitch']