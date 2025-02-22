import sys
from PyQt5.QtWidgets import QApplication
from .core.logging_config import setup_logging

def main():
    app = QApplication(sys.argv)
    from .gui.main import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
