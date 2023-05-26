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
    QComboBox
)
from PyQt5.QtCore import (
    Qt,
    QSize,
    QTimer,
    QThread,
    pyqtSignal
)
from Workplace import Workplace
from ProgrammerServer import ScadaServer
from ScadaDataTypes import ScadaData
import subprocess
import os


class RebootRPI(QThread):
    finished = pyqtSignal()

    def __init__(self, chipQty):
        super().__init__()
        self.chipQty = chipQty

    def run(self):
        for i in range (self.chipQty):
            try:
                subprocess.run(
                    f'sshpass -p raspberry ssh pi@sim7600prg{i+1}.local -o StrictHostKeyChecking=no sudo reboot',
                    shell=True,
                    capture_output=True,
                    timeout=0.1
                )
            except Exception as ex:
                pass

        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._config = yaml.load(open("/home/pi/ScadaToRpiGateway/configuration.yml"), yaml.SafeLoader)
        self.chipQty = self._config['chip_number']
        self.wpWidth = self._config['workplace_width_amount']
        self._usecase = self._config['use_case']

        self.setWindowTitle('Программатор SIMCOM7600')
        self.resize(QSize(720, 720))
        self._mainWidget = QWidget()
        self.setCentralWidget(self._mainWidget)
        self._mainLayout = QGridLayout()
        self._generalLayout = QVBoxLayout()

        self._settingsLayout = QHBoxLayout()
        self._simprgVersionWidget = QLineEdit(f"")
        self._simprgVersionWidget.setReadOnly(True)
        self._simprgVersionWidget.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._modemSystemWidgetStr = QLineEdit(f"Modem System: ")
        self._modemSystemWidgetStr.setReadOnly(True)
        self._modemSystemWidgetStr.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._modemSystemWidget = QComboBox()
        self._modemSystemWidget.textActivated.connect(self._updateModemSystem)

        self._reloadButton = QPushButton("Reload Systems Lists")
        self._reloadButton.clicked.connect(self._btnReloadClickedCallback)

        self._reloadPRIsButton = QPushButton("Reboot Raspberries")
        self._reloadPRIsButton.clicked.connect(self._btnReloadRPIsClickedCallback)

        self._clearButton = QPushButton("Clear Screen and Update Statuses")
        self._clearButton.clicked.connect(self._btnClearClickedCallback)

        self._settingsLayout.addWidget(self._simprgVersionWidget)
        self._settingsLayout.addWidget(self._modemSystemWidgetStr)
        self._settingsLayout.addWidget(self._modemSystemWidget)
        self._settingsLayout.addWidget(self._reloadButton)
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

        self._btnReloadClickedCallback()

        
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
            self._scada_server_thread.finished.connect(self._delete_server)
            self._scada_server_thread.start()

    def _choose_wp(self, data: ScadaData):
        wp_num = int(data.sim_data.KU)-1
        self._wp[wp_num]._remeberScadaData(data)
        self._wp[wp_num]._btnFlashClickedCallback()

    def _btnReloadClickedCallback(self):   
        if not self._reloadButton.isFlat():
            self._reloadButton.setFlat(True)

            with open(r'/home/pi/apt-repo/dists/stable/main/binary-all/Packages', 'r') as file:
                for content in file.readlines():
                    if 'Version' in content:
                        self._simprgVersionWidget.setText(f"Flasher Version: {content[8:]}")
                        break
            
            self._modemSystemWidget.clear()
            for file in os.listdir(r'/home/pi/apt-repo/system/'):
                self._modemSystemWidget.addItem(file)

            self._updateModemSystem(self._modemSystemWidget.currentText())
            
            QTimer.singleShot(100, self._btnReloadClickedCallbackTimeout) 

    
    def _btnReloadClickedCallbackTimeout(self):   
        self._reloadButton.setFlat(False)

    def _updateModemSystem(self, item):
        for wp_num in range(0, self.chipQty):
            self._wp[wp_num].remeberModemSystem(item)

    def _btnReloadRPIsClickedCallback(self):
        if not self._reloadPRIsButton.isFlat():
            self._reloadPRIsButton.setFlat(True)

            for wp_num in range(0, self.chipQty):
                self._wp[wp_num].cancel_task()

            self.reboot = RebootRPI(self.chipQty)
            self.reboot.finished.connect(self._btnReloadRPIsClickedCallbackThread)
            self.reboot.start()        

    def _btnReloadRPIsClickedCallbackThread(self):
        QTimer.singleShot(5000, self._btnReloadRPIsClickedCallbackTimeout) 

    def _btnReloadRPIsClickedCallbackTimeout(self):
        for wp_num in range(0, self.chipQty):
            self._wp[wp_num].clear_screen()

        self._reloadPRIsButton.setFlat(False)

    def _btnClearClickedCallback(self):
        if not self._clearButton.isFlat():
            self._clearButton.setFlat(True)
            for wp_num in range(0, self.chipQty):
                self._wp[wp_num].clear_screen()

            QTimer.singleShot(100, self._btnClearClickedCallbackTimeout) 

    def _btnClearClickedCallbackTimeout(self):
        self._clearButton.setFlat(False)

