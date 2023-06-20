import yaml
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import (
    Qt,
    QTimer
)
from WebSocketClient import *
from ProgrammerClient import ScadaClient
from ScadaDataTypes import ScadaData
import logging
import json
import subprocess

logs_path = "/home/pi/GatewayLogs"
logger = logging.getLogger(__name__)
f_handler = logging.FileHandler(f'{logs_path}/{__name__}.log')
f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
logger.addHandler(f_handler)
logger.setLevel(logging.WARNING)


class Workplace(QVBoxLayout):
    def __init__(self, wp_number):
        super().__init__()
        self._number_of_points = 0
        self._config = yaml.load(open("/home/pi/ScadaToRpiGateway/configuration.yml"), yaml.SafeLoader)
        self.usecase = self._config['use_case']
        self._wpnumber = wp_number  # номер текущего рп
        self._IMEI = ''
        self._PrgCnt = ''
        self._modemSystem = ''
        self._pingingInProc = False
        self._prg_in_proc = False
        self.canceled_flag = False
        self._firstScadaSending = True
        self._currIMEI = 0
        self._currPrgCnt = 0

        self._uiAddLogField()
        self._uiAddStatusField()
        self._uiAddFlashButton()
        self._ping_rpi()

    def _uiAddLogField(self):
        self._logfield = QListWidget()
        self.addWidget(self._logfield)

    def _uiAddStatusField(self):
        self._status = QLabel()
        self._status.setText(' --- ')
        self._status.setStyleSheet('background-color: gray')
        self._status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font = self._status.font()
        font.setPointSize(18)
        self._status.setFont(font)
        self.addWidget(self._status)

        self._isReady = QLabel()
        self._isReady.setText('Ожидание программатора')
        self._isReady.setStyleSheet('background-color: gray')
        self._isReady.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font = self._isReady.font()
        font.setPointSize(18)
        self._isReady.setFont(font)
        self.addWidget(self._isReady)

    def _uiAddFlashButton(self):
        self._button = QPushButton('Push to flash')
        self._button.clicked.connect(self._btnFlashClickedCallback)
        self._button.setFlat(True)

        if self.usecase == 'human':
            self.addWidget(self._button)

    def _create_websocket(self):
        self._prg_in_proc = True
        self._status.setText('В процессе    ')
        self._number_of_points = 0
        self._status.setStyleSheet('background-color: gray')

        factoryNum = self._getFactory()       
        self._rpi_thread = QThread()
        self._rpi_worker = WebSocketClient(f'sim7600prg{self._wpnumber+1}.local', 
                                           self._modemSystem + '#' + factoryNum)
        self._rpi_worker.moveToThread(self._rpi_thread)

        self._rpi_thread.started.connect(self._rpi_worker.run)
        self._rpi_worker.finished.connect(self._rpi_thread.quit)
        self._rpi_worker.finished.connect(self._rpi_worker.deleteLater)
        self._rpi_thread.finished.connect(self._rpi_thread.deleteLater)

        self._rpi_worker.finished.connect(self._change_rpi_worker_status)
        self._rpi_worker.progress.connect(self._show_new_log)
        self._rpi_worker.status.connect(self._change_status)
        self._rpi_worker.ping.connect(self._ping_callback)

        self._rpi_thread.start()

    def _getFactory(self) -> str:
        FlashNum = 0
        KU_num = 0

        with open('settings/factory_numbers') as json_file:
            data = json.load(json_file)
            FlashNum = data[f'sim7600prg{self._wpnumber+1}']['FlashNum']
            KU_num = data[f'sim7600prg{self._wpnumber+1}']['KU_num']
        
        FlashNum = self._dec_to_base(FlashNum)
        if len(FlashNum) == 1:
            FlashNum = "00" + FlashNum
        elif len(FlashNum) == 2:
            FlashNum = "0" + FlashNum
        elif len(FlashNum) == 3:
            FlashNum = FlashNum
        else:
            logger.error("Factory Num Error")

        KU_num = self._dec_to_base(KU_num)

        if len(KU_num) != 1:
            KU_num = 0
            logger.error("KU Num Error")

        string = ''
        with open(f'/home/pi/apt-repo/system/{self._modemSystem}/../factory.cfg') as file:
            lines = file.readlines()
            string = lines[0][:-1] + '#' + lines[1][:-5] + KU_num + FlashNum

        return string

    def _dec_to_base(self, num):
        base_num = ""
        base34 = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 
                'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 
                'W', 'X', 'Y', 'Z' ]
        
        if num == 0:
            return '0'

        while num>0:
            dig = int(num%34)
            if dig<10:
                base_num += str(dig)
            else:
                base_num += base34[dig]  #Using uppercase letters
            num //= 34
        base_num = base_num[::-1]  #To reverse the string
        return base_num

    def _updateFactory(self):
        data = []
        with open('settings/factory_numbers') as json_file:
            data = json.load(json_file)
        
        data[f'sim7600prg{self._wpnumber+1}']['FlashNum'] += 1

        with open('settings/factory_numbers', 'w') as outfile:
            json.dump(data, outfile)

    def _change_rpi_worker_status(self):
        self._prg_in_proc = False
        logger.info("Delete WS")

    def _ping_rpi(self):
        if not self._pingingInProc:
            self._scada_client_ping = ScadaClient(self._wpnumber+1)
            self._scada_client_ping.finished.connect(self._scada_sended_callback)
            
            self._pingingInProc = True

            self._rpi_ping_thread = QThread()
            self._rpi_ping_worker = WebSocketClientChecker(f'sim7600prg{self._wpnumber+1}.local')
            self._rpi_ping_worker.moveToThread(self._rpi_ping_thread)

            self._rpi_ping_thread.started.connect(self._rpi_ping_worker.run)
            self._rpi_ping_worker.finished.connect(self._rpi_ping_thread.quit)
            self._rpi_ping_worker.finished.connect(self._rpi_ping_worker.deleteLater)
            self._rpi_ping_thread.finished.connect(self._rpi_ping_thread.deleteLater)

            self._rpi_ping_worker.finished.connect(self._change_rpi_ping_worker_status)
            self._rpi_ping_worker.status.connect(self._ping_status_callback)

            self._rpi_ping_thread.start()

    def _change_rpi_ping_worker_status(self):
        self._pingingInProc = False
        logger.info("Delete WS Checker")

    def _btnFlashClickedCallback(self):
        if not self._button.isFlat():
            self._button.setFlat(True)
            self._logfield.clear()
            self._create_websocket()

    def _scada_sended_callback(self, res: bool):
        logger.info(f"Scada Sended CallBack: {self._wpnumber}")
        if res:
            self._show_new_log('LogOk', 'Scada Received msg Ok')
        else:
            self._show_new_log('LogErr', 'Scada did not receive msg')

    def _ping_status_callback(self, work_result:bool):
        logger.info(f"Ping CallBack: {self._wpnumber}")
        if work_result:
            self._isReady.setText('Программатор готов')
            self._isReady.setStyleSheet('background-color: green')
            self._button.setFlat(False)
            if self.canceled_flag:
                logger.warning(f'cancelled flad {self._wpnumber}')
                self.canceled_flag = False
                self._clear_screen()

            if self._firstScadaSending:
                self._firstScadaSending = False
                self._scada_client_ping.UpdateInfo('Ready To Start')
                if self.usecase == 'scada':
                    self._scada_client_ping.start()
        else:
            self._isReady.setText('Ожидание программатора')
            self._isReady.setStyleSheet('background-color: gray')
            self._button.setFlat(True)
        
    def _show_new_log(self, log_level: str, log_msg:str):
        item = QListWidgetItem(log_msg)
        if log_level == 'LogOk':
            item.setForeground(QColor('#7fb94f')) # green
        elif log_level == 'LogWarn':
            item.setForeground(QColor('#f0B030')) # yellow
            try:
                self._scada_client_work.UpdateInfo(log_msg)
            except: pass
        elif log_level == 'LogErr':
            item.setForeground(QColor('#f00000')) # red
            try:    
                self._scada_client_work.UpdateInfo(log_msg)
            except: pass
        if 'Start flashing' in log_msg:
            self._scada_client_work = ScadaClient(self._wpnumber+1)
            self._scada_client_work.finished.connect(self._scada_sended_callback)
            self._scada_client_work.SetIMEI(self._currIMEI)
            self._scada_client_work.SetPrgCnt(self._currPrgCnt)

        if 'FW version:' in log_msg:
            try:
                self._scada_client_work.SetFWVersion(log_msg[12:])
            except: pass
            
        self._logfield.addItem(item)
        self._logfield.scrollToBottom()

    def _clear_screen(self):
        if not self._prg_in_proc:
            logger.info(f"Clear screen {self._wpnumber}")
            self._logfield.clear()
            self._status.setText(' --- ')
            self._status.setStyleSheet('background-color: gray')
            self._firstScadaSending = True
            self._ping_rpi()

    def _remeberScadaData(self, data: ScadaData):
        self._currIMEI = data.sim_data.IMEI
        self._currPrgCnt = data.sim_data.ProgrammingsCnt

    def _change_status(self, work_result:bool):    
        logger.info(f"Change Status: {self._wpnumber}")
        if work_result:
            self._scada_client_work.SetCommand('FinishedOK')
            self._scada_client_work.SetResult(True)
            self._scada_client_work.start()

            self._updateFactory()

            self._status.setText('Успешно')
            self._status.setStyleSheet('background-color: green')
        else:
            self._scada_client_work.SetCommand('FinishedNOK')
            self._scada_client_work.SetResult(False)
            self._scada_client_work.start()

            self._status.setText('Ошибка')
            self._status.setStyleSheet('background-color: red')

        self._button.setFlat(False)

        self._ping_rpi()

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

    def remeberModemSystem(self, system: str):
        self._modemSystem = system

    def rebootRPI(self):
        if self._prg_in_proc:
            logger.warning(f"Cancel task {self._wpnumber}")
            try:
                self._rpi_thread.quit()
                self._prg_in_proc = False
            except:
                logger.error("Error in Cancel Task")
        
        self._show_new_log('LogInfo', '\nTrying to reboot...\n')
        self.canceled_flag = True

        try:
            self._proc = subprocess.Popen(
                f'sudo sshpass -p raspberry ssh pi@sim7600prg{self._wpnumber+1}.local -o StrictHostKeyChecking=no sudo reboot',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            QTimer.singleShot(4000, self._endRebootRPI) 
        except Exception as ex:
            self._show_new_log('LogErr', f'Exception: {ex}')

    def _endRebootRPI(self):
        self._clear_screen()
        try:
            out, err = self._proc.communicate(timeout=0.1)
            self._show_new_log('LogInfo', err.decode("utf-8") )
            self._show_new_log('LogOk', 'Reboot in progress' )
        except Exception as ex:
            self._show_new_log('LogErr', f'Exception: {ex}')

# if __name__ == '__main__':
#     # for i in range(, 1000010):
#     print(_getFactory())
