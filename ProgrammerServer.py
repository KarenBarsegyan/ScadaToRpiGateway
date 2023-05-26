import socket
from ScadaDataTypes import ScadaData
from PyQt5.QtCore import QThread, pyqtSignal

class ScadaServer(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(ScadaData)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def __del__(self):
        self.sock.close()

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
            self.sock.bind(('0.0.0.0', 8081))
            self.sock.listen()

            while True:
                conn, addr = self.sock.accept()

                with conn:
                    while True:
                        try:
                            recv_data = conn.recv(1024)  # принимаем данные от клиента, по 1024 байт
                            if not recv_data:
                                break

                            scada_data = ScadaData()
                            scada_data.SetDataFromBytes(recv_data)

                            if scada_data.sim_data.Command == 'Start':
                                scada_data.sim_data.Message = 'Started'
                                self.progress.emit(scada_data)

                            conn.send(scada_data.GetDataInBytes())

                        except Exception as ex:
                            print(ex)
                            break

