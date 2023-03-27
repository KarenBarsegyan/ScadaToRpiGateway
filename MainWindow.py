import yaml
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QGroupBox,
    QGridLayout,
)
from PyQt6.QtCore import QSize
from Workplace import Workplace
from ProgrammerServer import ScadaServer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._config = yaml.load(open("configuration.yml"), yaml.SafeLoader)
        self.chipQty = self._config['chip_number']
        self.wpWidth = self._config['workplace_width_amount']
        self._usecase = self._config['use_case']
        # настройка главного окна
        self.setWindowTitle('Программатор SIMCOM7600')
        self.resize(QSize(1280, 720))
        self._mainWidget = QWidget()
        self.setCentralWidget(self._mainWidget)
        self._mainLayout = QGridLayout()
        self._mainWidget.setLayout(self._mainLayout)

        self._group = []      # список рабочих групп (рамок с подписью "Рабочее место №")
        self._wp = []         # список рабочих пространств для взаимодействия с модемом
        for i in range(0, self.chipQty):
            self._wp.append(Workplace(i))  # создание нового рабочего пространства
            self._group.append(QGroupBox())

        # заполнение главного окна
        self._uiJoin()

        if self._usecase == 'scada':
            self._createScadaServer()

        self.show()

    def _uiJoin(self):
        for i in range(0, self.chipQty):
            # настройка группы и добавление в неё рабочего
            # пространства (а по факту: кастомного слоя - см. класс Workplace)
            self._group[i].setTitle(f'Рабочее место №{i+1}')
            self._group[i].setLayout(self._wp[i])
            # добавление группы в главное окно
            x = int(i / self.wpWidth)
            y = int(i - int(i / self.wpWidth)*self.wpWidth)
            self._mainLayout.addWidget(self._group[i], x, y)

    def _createScadaServer(self):
        self._scada_server_thread = ScadaServer()
        self._scada_server_thread.progress.connect(self._choose_button)
        self._scada_server_thread.finished.connect(self._delete_server)
        self._scada_server_thread.start()

    def _choose_button(self, data: str):
        print("Received Data:")
        # print(data['IMEI'])

    def _delete_server(self):
        print("HEY LOL")


