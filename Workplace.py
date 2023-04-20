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
from ProgrammerClient import ScadaClient


class Workplace(QVBoxLayout):
    def __init__(self, wp_number):
        super().__init__()
        self._number_of_points = 0
        self._config = yaml.load(open("configuration.yml"), yaml.SafeLoader)
        self.usecase = self._config['use_case']
        self._wpnumber = wp_number  # номер текущего рп
        self._scada_client = ScadaClient(self._wpnumber+1)

        self._uiAddWidgets()  # заполнение рабочего пространства

    def _uiAddWidgets(self):
        self._uiAddLogField()
        self._uiAddStatusField()
        self._uiAddFlashButton()
        self._create_websocket('Ping')

    def _uiAddLogField(self):
        self._logfield = QListWidget()
        self.addWidget(self._logfield)

    def _uiAddStatusField(self):
        self._status = QLabel()
        self._status.setText('Ожидание программатора')
        self._status.setStyleSheet('background-color: gray')
        self._status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font = self._status.font()
        font.setPointSize(18)
        self._status.setFont(font)
        self.addWidget(self._status)

    def _uiAddFlashButton(self):
        self._button = QPushButton('Push to flash')
        self._button.clicked.connect(self._btnFlashClickedCallback)
        self._button.setFlat(True)

        if self.usecase == 'human':
            self.addWidget(self._button)

    def _btnFlashClickedCallback(self):
        if not self._button.isFlat():
            self._button.setFlat(True)
            self._logfield.clear()
            self._create_websocket('Start')

    def _create_websocket(self, cmd):
            if cmd == 'Start':
                self._status.setText('В процессе    ')
                self._number_of_points = 0
                self._status.setStyleSheet('background-color: gray')
                
                self._rpi_thread = WebSocketClient(f'sim7600prg{self._wpnumber+1}.local', 'Start')
                self._rpi_thread.progress.connect(self._show_new_log)
                self._rpi_thread.finished.connect(self._change_status)
                self._rpi_thread.ping.connect(self._ping_callback)
                self._rpi_thread.start()

            if cmd == 'Ping':
                self._rpi_thread = WebSocketClient(f'sim7600prg{self._wpnumber+1}.local', 'Ping')
                self._rpi_thread.finished.connect(self._start_ping_callback)
                self._rpi_thread.start()

    def _scada_send(self, result: bool):
        if self.usecase == 'scada':
            self._scada_client.finished.connect(self._scada_sended_callback)
            self._scada_client.SetResult(result)
            self._scada_client.start()

    def _scada_sended_callback(self, res: bool):
        if res:
            self._show_new_log('LogOk', 'Scada Received msg Ok')
        else:
            self._show_new_log('LogErr', 'Scada did not receive msg')

    def _start_ping_callback(self, work_result:bool):
        if work_result:
            self._status.setText('Программатор готов')
            self._status.setStyleSheet('background-color: green')
            self._button.setFlat(False)

            self._scada_client.UpdateMessage('Ready To Start')
            self._scada_send(True)
        
    def _show_new_log(self, log_level: str, log_msg:str):
        item = QListWidgetItem(log_msg)
        if log_level == 'LogOk':
            item.setForeground(QColor('#7fc97f')) # green
        if log_level == 'LogWarn':
            item.setForeground(QColor('#ffff99')) # yellow
            self._scada_client.UpdateMessage(log_msg)
        elif log_level == 'LogErr':
            item.setForeground(QColor('#f00000')) # red
            self._scada_client.UpdateMessage(log_msg)

        if 'Start flashing' in log_msg:
            self._scada_client = ScadaClient(self._wpnumber+1)

        if 'FW version:' in log_msg:
            self._scada_client.SetFWVersion(log_msg[12:])
            
        self._logfield.addItem(item)
        self._logfield.scrollToBottom()

    def _change_status(self, work_result:bool):
        if work_result:
            self._scada_send(True)

            self._status.setText('Успешно')
            self._status.setStyleSheet('background-color: green')
        else:
            self._scada_send(False)

            self._status.setText('Ошибка')
            self._status.setStyleSheet('background-color: red')

        self._button.setFlat(False)
        del(self._rpi_thread)

    def _ping_callback(self):
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