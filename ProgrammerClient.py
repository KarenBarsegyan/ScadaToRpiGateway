import json
import socket
from ScadaDataTypes import ScadaData
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
from async_timeout import timeout

class ScadaClient(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, KU: int, parent=None):
        QThread.__init__(self, parent)

        self._messgae = []

        data_dict = {
            "IMEI": "",
            "KU": KU,
            "SWVersion": "",
            "Result": True,
            "Error": "",
            "Command": "",
            "Message": "",
            "Info": ""
        }
        self._data_to_send = ScadaData(data_dict)

        self._data_to_send.SetStartTime()

    def SetFWVersion(self, SW):
        self._data_to_send.sim_data.SWVersion = SW

    def UpdateMessage(self, msg: str):
        self._messgae.append(msg)

    def SetResult(self, result: bool):
        self._data_to_send.sim_data.Result = result

    async def _send(self):
        self._data_to_send.SetEndTime()

        self._data_to_send.sim_data.Message = str(self._messgae)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = False
            for i in range(5):
                try:
                    sock.connect(('192.168.88.246', 8080))
                    sock.send(self._data_to_send.GetDataInBytes())

                    data_to_recv = sock.recv(1024)

                    scada_data_recv = ScadaData()
                    scada_data_recv.SetDataFromBytes(data_to_recv)

                    if scada_data_recv.GetDataInBytes() == self._data_to_send.GetDataInBytes():
                        self.finished.emit(True)
                        result = True
                        break
                except Exception as ex:
                    print(ex)

                await asyncio.sleep(1)

            if not result:
                self.finished.emit(False)

    def run(self) -> None:
        asyncio.run(self._send())    

if __name__ == '__main__':
    cl = ScadaClient(1)
    cl.run()
