import sys
from MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication
import json

if __name__ == '__main__':
    # data = {
    #     'sim7600prg1': {'FlashNum': 1, 'KU_num':1},
    #     'sim7600prg2': {'FlashNum': 1, 'KU_num':2},
    #     'sim7600prg3': {'FlashNum': 1, 'KU_num':3},
    #     'sim7600prg4': {'FlashNum': 1, 'KU_num':4},
    #     'sim7600prg5': {'FlashNum': 1, 'KU_num':5},
    #     'sim7600prg6': {'FlashNum': 1, 'KU_num':6},
    #     'sim7600prg7': {'FlashNum': 1, 'KU_num':7},
    #     'sim7600prg8': {'FlashNum': 1, 'KU_num':8},
    #     'sim7600prg9': {'FlashNum': 1, 'KU_num':9},
    #     'sim7600prg10': {'FlashNum': 1, 'KU_num':10}
    # }

    # with open('settings/factory_numbers', 'w') as outfile:
    #     json.dump(data, outfile)

    # with open('settings/factory_numbers') as json_file:
    #     data = json.load(json_file)
    #     print(data['sim7600prg1']['FlashNum'])

    app = QApplication(sys.argv)
    window = MainWindow()
    try:
        sys.exit(app.exec())
    except Exception as Ex:
        print(f"StartGateWay app.exec error: {Ex}")
