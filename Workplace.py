import yaml
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QListWidget,
    QComboBox,
    QLabel,
    QTextEdit,
    QPushButton
)
from PyQt6.QtCore import (
    QThread,
    Qt,
    QSize
)
from WebSocketClient import WebSocketClient


class Workplace(QVBoxLayout):
    def __init__(self, wp_number):
        super().__init__()
        self._config = yaml.load(open("configuration.yml"), yaml.SafeLoader)
        self.constIp = self._config['const_ip_part']
        self.startIp = self._config['start_ip']

        # настройки потока для общения с RPI
        self._rpi_thread = WebSocketClient(self.constIp + str(self.startIp + wp_number))
        self._rpi_thread.progress.connect(self._show_new_log)
        self._rpi_thread.finished.connect(self._change_status)
        
        self._wpnumber = wp_number  # номер текущего рп
        self._uiAddWidgets()  # заполнение рабочего пространства


    def _uiAddWidgets(self):
        self._uiAddLogField()
        self._uiAddStatusField()
        self._uiAddFlashButton()

    def _uiAddLogField(self):
        self._logfield = QListWidget()
        self._logfield.setMaximumSize(QSize(1280, 320))
        self.addWidget(self._logfield)

    def _uiAddStatusField(self):
        self._status = QLabel()
        self._status.setText('Ожидание')
        self._status.setStyleSheet('background-color: gray')
        self._status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font = self._status.font()
        font.setPointSize(18)
        self._status.setFont(font)
        self.addWidget(self._status)

    def _uiAddFlashButton(self):
        self._button = QPushButton('Push to flash')
        self._button.clicked.connect(self._btnFlashClickedCallback)
        self.addWidget(self._button)

    def _btnFlashClickedCallback(self):
        self._logfield.clear()
        self._status.setText('В процессе...')
        self._rpi_thread.start()

    def _show_new_log(self, log_msg:str):
        self._logfield.addItem(log_msg)

    def _change_status(self, work_result:bool):
        if work_result:
            self._status.setText('Успешно')
        else:
            self._status.setText('Ошибка')