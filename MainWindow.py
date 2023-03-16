import yaml
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QGroupBox,
    QGridLayout,
)
from PyQt6.QtCore import QSize
from Workplace import Workplace


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._config = yaml.load(open("configuration.yml"), yaml.SafeLoader)
        self.chipQty = self._config['chip_number']
        self.wpWidth = self._config['workplace_width_amount']
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


