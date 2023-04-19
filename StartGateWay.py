import sys
import logging
import yaml
from ProgrammerServer import ScadaServer
from ProgrammerClient import ScadaClient
from WebSocketClient import WebSocketClient
from MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
