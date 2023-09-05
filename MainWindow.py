import yaml
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QGroupBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QCheckBox
)
from PyQt5.QtCore import (
    Qt,
    QSize,
    QTimer,
)
from Workplace import Workplace
from ProgrammerServer import ScadaServer
from ScadaDataTypes import ScadaData
import os
from FileBrowser import FileBrowser
import json
import logging

logs_path = "/home/pi/GatewayLogs"
logger = logging.getLogger(__name__)
f_handler = logging.FileHandler(f'{logs_path}/{__name__}.log')
f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
logger.addHandler(f_handler)
logger.setLevel(logging.WARNING)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self._config = yaml.load(open("/home/pi/ScadaToRpiGateway/configuration.yml"), yaml.SafeLoader)
        self.chipQty = self._config['chip_number']
        self.wpWidth = self._config['workplace_width_amount']
        self._usecase = self._config['use_case']
        self.firstChoice = True
        self._firstTimeType = True
        self._firstTimePerformCheck = True

        self.setWindowTitle('SIMCOM7600 Programmer')
        self._mainWidget = QWidget()
        self.setCentralWidget(self._mainWidget)
        self._mainLayout = QGridLayout()
        self._generalLayout = QVBoxLayout()

        self._settingsLayout = QHBoxLayout()
        self._simprgVersionWidget = QLineEdit(f"")
        self._simprgVersionWidget.setReadOnly(True)
        self._simprgVersionWidget.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._simprgVersionWidget.setMaximumWidth(200)
        self._simprgVersionWidget.setMaximumWidth(500)

        self._modemSystemChoice = FileBrowser('Choose Modem System: ')
        self._modemSystemChoice.setDefaultDir(r'/home/pi/apt-repo/system/')
        self._modemSystemChoice.setCallBack(self._systemChoosenCallback)

        modemTypeLabel = QLabel("Modem Type: ")

        self._modemTypeChoice = QLineEdit(f"")
        self._modemTypeChoice.setReadOnly(True)
        self._modemTypeChoice.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._modemTypeChoice.setMaximumWidth(120)
        self._modemTypeChoice.setMaximumWidth(500)

        spaceLabel = QLabel("")
        spaceLabel.setMinimumWidth(50)
        spaceLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._performTests = QCheckBox()
        self._performTests.setText(f"Perform Tests")
        self._performTests.stateChanged.connect(self._performTestsChanged)

        self._reloadPRIsButton = QPushButton("Reboot Raspberries")
        self._reloadPRIsButton.clicked.connect(self._btnReloadRPIsClickedCallback)

        self._clearButton = QPushButton("Clear Screen and Update Statuses")
        self._clearButton.clicked.connect(self._btnClearClickedCallback)

        self._settingsLayout.addWidget(self._simprgVersionWidget)
        self._settingsLayout.addWidget(self._modemSystemChoice)
        self._settingsLayout.addWidget(spaceLabel)
        self._settingsLayout.addWidget(modemTypeLabel)
        self._settingsLayout.addWidget(self._modemTypeChoice)
        self._settingsLayout.addWidget(spaceLabel)
        self._settingsLayout.addWidget(self._performTests)
        self._settingsLayout.addWidget(spaceLabel)
        self._settingsLayout.addWidget(self._reloadPRIsButton)
        self._settingsLayout.addWidget(self._clearButton)

        self._generalLayout.addLayout(self._settingsLayout)
        self._generalLayout.addLayout(self._mainLayout)

        self._mainWidget.setLayout(self._generalLayout)
        self.showMaximized()

        self._group = []      # список рабочих групп (рамок с подписью "Рабочее место №")
        self._wp = []         # список рабочих пространств для взаимодействия с модемом
        for i in range(0, self.chipQty):
            self._wp.append(Workplace(i))  # создание нового рабочего пространства
            self._group.append(QGroupBox())

        # заполнение главного окна
        self._uiJoin()

        self._systemChoosenCallback()
        self._performTestsChanged()
        
        self._createScadaServer()
        
        self.show()

    def _uiJoin(self):
        for i in range(0, self.chipQty):
            # настройка группы и добавление в неё рабочего
            # пространства (а по факту: кастомного слоя - см. класс Workplace)
            self._group[i].setTitle(f'Рабочее место №{i+1}')
            self._group[i].setAlignment(Qt.AlignCenter)
            self._group[i].setLayout(self._wp[i])
            # добавление группы в главное окно
            x = int(i / self.wpWidth)
            y = int(i - int(i / self.wpWidth)*self.wpWidth)
            self._mainLayout.addWidget(self._group[i], x, y)

    def _createScadaServer(self):
        if self._usecase == 'scada':
            self._scada_server_thread = ScadaServer()
            self._scada_server_thread.progress.connect(self._choose_wp)
            self._scada_server_thread.start()

    def _choose_wp(self, data: ScadaData):
        try:
            wp_num = int(data.sim_data.KU)-1
            self._wp[wp_num]._remeberScadaData(data)
            self._wp[wp_num]._btnFlashClickedCallback()
        except Exception as ex:
            logger.error(f"_choose_wp error: {ex}")


    def _systemChoosenCallback(self):  
        try:
            with open(r'/home/pi/apt-repo/dists/stable/main/binary-all/Packages', 'r') as file:
                for content in file.readlines():
                    if 'Version' in content:
                        self._simprgVersionWidget.setText(f"Flasher Version: {content[8:]}")
                        break
            
            if self.firstChoice:
                self.firstChoice = False

                homedir = r'/home/pi/apt-repo/system/'
                res_paths = []
                for paths, dirs, files in os.walk(homedir):
                    res_paths.append(paths.replace(homedir, ''))

                with open(r'/home/pi/GateWaySettings/FW_version_choice') as file:
                    previos_choice = file.readline()

                    if previos_choice in res_paths:
                        self._modemSystemChoice.setPath(previos_choice)

                    elif len(res_paths) > 0:
                        self._modemSystemChoice.setPath(res_paths[0])
            
            with open(r'/home/pi/GateWaySettings/FW_version_choice', 'w') as file:
                file.write(self._modemSystemChoice.getPath())

            if os.path.isfile(f'/home/pi/apt-repo/system/{self._modemSystemChoice.getPath()}/../factory.cfg'):
                if not os.path.isfile(f'/home/pi/apt-repo/system/{self._modemSystemChoice.getPath()}/../prg_cnt'):
                    data = {}
                    for wp_num in range(0, self.chipQty):
                        data[f'sim7600prg{wp_num+1}'] = 0

                    with open(f'/home/pi/apt-repo/system/{self._modemSystemChoice.getPath()}/../prg_cnt', 'w') as outfile:
                        json.dump(data, outfile)

            modemTypeStr = self._modemSystemChoice.getPath()
            modemTypeStr = modemTypeStr[:modemTypeStr.index('/')]
            modemTypeStr = modemTypeStr[7:]

            if modemTypeStr == 'simple':
                self._modemType = 'Simple'
                self._modemTypeChoice.setText('Simple with factory')
            elif modemTypeStr == 'retro':
                self._modemType = 'Retrofit'
                self._modemTypeChoice.setText('Retrofit NO factory')
            else:
                self._modemType = ''
                self._modemTypeChoice.setText('Wrong Folder Name')

            if self._modemType != '':
                for wp_num in range(0, self.chipQty):
                    self._wp[wp_num].remeberModemSystem(self._modemSystemChoice.getPath())
                    self._wp[wp_num].remeberModemType(self._modemType)
        
        except Exception as ex:
            logger.error(f"_systemChoosenCallback error: {ex}")


    def _btnReloadRPIsClickedCallback(self):
        try:
            if not self._reloadPRIsButton.isFlat():
                self._reloadPRIsButton.setFlat(True)

                for wp_num in range(0, self.chipQty):
                    self._wp[wp_num].rebootRPI()    

            QTimer.singleShot(5000, self._btnReloadRPIsClickedCallbackTimeout) 

        except Exception as ex:
            logger.error(f"_btnReloadRPIsClickedCallback error: {ex}")

    def _btnReloadRPIsClickedCallbackTimeout(self):
        self._reloadPRIsButton.setFlat(False)

    def _btnClearClickedCallback(self):
        try:
            if not self._clearButton.isFlat():
                self._clearButton.setFlat(True)
                for wp_num in range(0, self.chipQty):
                    self._wp[wp_num]._clear_screen()

                QTimer.singleShot(100, self._btnClearClickedCallbackTimeout) 
        
        except Exception as ex:
            logger.error(f"_btnClearClickedCallback error: {ex}")

    def _btnClearClickedCallbackTimeout(self):
        self._clearButton.setFlat(False)

    def _performTestsChanged(self):
        try:
            if self._firstTimePerformCheck:
                self._firstTimePerformCheck = False
                with open(r'/home/pi/GateWaySettings/perform_check') as file:
                    if file.readline() == '1':
                        self._performTests.setChecked(True)  
                    else:
                        self._performTests.setChecked(False)  

            with open(r'/home/pi/GateWaySettings/perform_check', 'w') as file:
                if self._performTests.isChecked():
                    file.write('1')
                else:
                    file.write('0')

            for wp_num in range(0, self.chipQty):
                self._wp[wp_num].remeberPerformCheck(self._performTests.isChecked())

        except Exception as ex:
            logger.error(f"_performTestsChanged error: {ex}")

