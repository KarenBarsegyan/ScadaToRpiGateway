import json
import socket
from ScadaDataTypes import ScadaData
from PyQt5.QtCore import QThread, pyqtSignal
import asyncio
from async_timeout import timeout
import logging
import yaml

logs_path = "/home/pi/GatewayLogs"
logger = logging.getLogger(__name__)
f_handler = logging.FileHandler(f'{logs_path}/{__name__}.log')
f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
logger.addHandler(f_handler)
logger.setLevel(logging.WARNING)


class ScadaClient(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, KU: int, parent=None):
        QThread.__init__(self, parent)
        self._KU = KU
        logger.info(f"Init client KU: {self._KU}")
        self._info = []
        self._config = yaml.load(open("/home/pi/ScadaToRpiGateway/configuration.yml"), yaml.SafeLoader)
        self._ip = self._config['gateway_client_ip']

        data_dict = {
            "IMEI": "",
            "KU": self._KU,
            "ProgrammingsCnt": 0,
            "SWVersion": "",
            "Result": False,
            "Error": "",
            "Command": "",
            "Message": "",
            "Info": ""
        }
        self._data_to_send = ScadaData(data_dict)

    def SetStartTime(self):
        self._data_to_send.SetStartTime()

    def SetFWVersion(self, SW):
        self._data_to_send.sim_data.SWVersion = SW

    def UpdateInfo(self, msg: str):
        self._info.append(msg)

    def SetResult(self, result: bool):
        self._data_to_send.sim_data.Result = result

    def SetCommand(self, command):
        self._data_to_send.sim_data.Command = command

    def SetIMEI(self, imei):
        self._data_to_send.sim_data.IMEI = imei

    def SetPrgCnt(self, prgcnt):
        self._data_to_send.sim_data.ProgrammingsCnt = prgcnt

    def GetData(self):
        data = {"IMEI": self._data_to_send.sim_data.IMEI,
                "KU_NUM": self._data_to_send.sim_data.KU,
                "Result": self._data_to_send.sim_data.Result,
                "Messages": self._info}
        return data

    async def _send(self):
        try:
            if not self._data_to_send.sim_data.StartProgramming:
                self._data_to_send.SetStartTime()

            self._data_to_send.SetEndTime()

            self._data_to_send.sim_data.Info = str(self._info)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = False
                for i in range(3):
                    try:
                        sock.connect((self._ip, 8080))
                        sock.send(self._data_to_send.GetDataInBytes())
                        data_to_recv = sock.recv(1024)
                        scada_data_recv = ScadaData()
                        scada_data_recv.SetDataFromBytes(data_to_recv)
                        logger.info(f"Finished Emit True {self._data_to_send.sim_data.KU}")
                        self.finished.emit(True)
                        result = True
                        break
                    except Exception as ex:
                        logger.info(f"Programmer cliend recv\send warn: {ex}")

                    await asyncio.sleep(0.5)

                if not result:
                    logger.info(f"Finished Emit False {self._data_to_send.sim_data.KU}")
                    self.finished.emit(False)
                    
        except Exception as ex:
            logger.error(f"Programmer Client error: {ex}")

    def run(self) -> None:
        asyncio.run(self._send())    

if __name__ == '__main__':
    cl = ScadaClient(1)
    cl.UpdateInfo("Lol")
    cl.UpdateInfo("Kek")
    cl.run()
