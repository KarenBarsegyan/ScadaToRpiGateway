import sys
from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication
import os

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
