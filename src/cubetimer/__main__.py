"""Main entry point for CubeTimer application."""
import sys
from PyQt6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main():
    """Run the CubeTimer application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
