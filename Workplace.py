import yaml
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import (
    Qt,
)
from WebSocketClient import WebSocketClient


class Workplace(QVBoxLayout):
    def __init__(self, wp_number):
        super().__init__()
        self._number_of_points = 0
        self._config = yaml.load(open("configuration.yml"), yaml.SafeLoader)
        self.constIp = self._config['const_ip_part']
        self.startIp = self._config['start_ip']
        self.usecase = self._config['use_case']

        self._buttonAlreadyClicked = False
        
        self._wpnumber = wp_number  # номер текущего рп
        self._uiAddWidgets()  # заполнение рабочего пространства


    def _uiAddWidgets(self):
        self._uiAddLogField()
        self._uiAddStatusField()
        self._uiAddFlashButton()

    def _uiAddLogField(self):
        self._logfield = QListWidget()
        # self._logfield.setMaximumSize(QSize(1280, 320))
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

        if self.usecase == 'human':
            self.addWidget(self._button)

    def _btnFlashClickedCallback(self):
        if not self._buttonAlreadyClicked:
            self._button.setFlat(True)
            self._buttonAlreadyClicked = True
            self._logfield.clear()
            self._status.setText('В процессе    ')
            self._number_of_points = 0
            self._status.setStyleSheet('background-color: gray')

            self._rpi_thread = WebSocketClient(f'sim76prg{self._wpnumber+1}.local')
            self._rpi_thread.progress.connect(self._show_new_log)
            self._rpi_thread.finished.connect(self._change_status)
            self._rpi_thread.ping.connect(self._ping)
            self._rpi_thread.start()


    def _show_new_log(self, log_level: str, log_msg:str):
        item = QListWidgetItem(log_msg)
        if log_level == 'LogOk':
            item.setForeground(QColor('#7fc97f')) # green
        if log_level == 'LogWarn':
            item.setForeground(QColor('#ffff99')) # yellow
        elif log_level == 'LogErr':
            item.setForeground(QColor('#f00000')) # red
            
        self._logfield.addItem(item)
        self._logfield.scrollToBottom()

    def _change_status(self, work_result:bool):
        if work_result:
            self._status.setText('Успешно')
            self._status.setStyleSheet('background-color: green')
        else:
            self._status.setText('Ошибка')
            self._status.setStyleSheet('background-color: red')

        self._buttonAlreadyClicked = False
        self._button.setFlat(False)
        del(self._rpi_thread)

    def _ping(self):
        if self._number_of_points == 0:
            self._status.setText('В процессе    ')
            self._number_of_points = 1
    
        elif self._number_of_points == 1:
            self._status.setText('В процессе .  ')
            self._number_of_points = 2

        elif self._number_of_points == 2:
            self._status.setText('В процессе .. ')
            self._number_of_points = 3 

        elif self._number_of_points == 3:
            self._status.setText('В процессе ...')
            self._number_of_points = 0