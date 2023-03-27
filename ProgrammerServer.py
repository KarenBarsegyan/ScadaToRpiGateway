import time
import socket
from ScadaDataTypes import ScadaData
from PyQt6.QtCore import QThread, pyqtSignal
import json

class ScadaServer(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def __del__(self):
        print("__DEL__")
        self.conn.close()

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # создаем сокет
        try:
            sock.bind(('192.168.4.100', 8081))  # связываем сокет с портом, где он будет ожидать сообщения
        except:
            print('Already in use')
            # sock.shutdown(1)
            sock.close()
            return 
        
        sock.listen(10)  # указываем сколько может сокет принимать соединений
        
        # try:
        while True:
            self.conn, addr = sock.accept()  # начинаем принимать соединения
            # data_to_recv.ScadaData = 
            data = self.conn.recv(1024)  # принимаем данные от клиента, по 1024 байт

            data_to_recv = ScadaData(ScadaData.SimModel(             
                IMEI = '123456789',
                KU = 1,
                SWVersion = "1.0",
                Result = True,
                Error = "",
                Command = "",
                Message = "",
                Info = ""
            ))
            data_to_recv.Data = data
            print(data_to_recv.Data)
            # self.progress.emit(str(data))
            
            self._data_to_send = ScadaData(ScadaData.SimModel(             
                IMEI = '123456789',
                KU = 1,
                SWVersion = "1.0",
                Result = True,
                Error = "",
                Command = "",
                Message = "",
                Info = ""
            ))

            self._data_to_send.SetStartTime()
            self._data_to_send.SetEndTime()

            self.conn.send(self._data_to_send.Data)  # в ответ клиенту отправляем сообщение в верхнем регистре
            # self.conn.close()
        # except:
        #     self.conn.close()  # закрываем соединение

