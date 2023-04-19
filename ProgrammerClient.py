import json
import socket
from ScadaDataTypes import ScadaData

class ScadaClient:
    def __init__(self, KU: int):
        data_dict = {
            "IMEI": "123456789",
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

    def Send(self, result):
        self._data_to_send.SetEndTime()

        if result == 'Success':
            self._data_to_send.sim_data.Result = True
        else:
            self._data_to_send.sim_data.Result = False
            self._data_to_send.sim_data.Message = result

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(('192.168.88.246', 8080))
                sock.send(self._data_to_send.GetDataInBytes())

                data_to_recv = sock.recv(1024)

                if data_to_recv == self._data_to_send.GetDataInBytes():
                    print("Send \ recv succesfully")
            except Exception as ex:
                print(ex)

    def _SendBytes(self, data_to_send) -> ScadaData:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create client socket
        sock.connect(('127.0.0.1', 8080))  # connect to server socket
        sock.send(data_to_send)  # send data
        data = sock.recv(1024)  # read server answer
        sock.close()  # close connection
        return ScadaData(**json.loads(data)) # return Answer in ScadaData format
    

if __name__ == '__main__':
    cl = ScadaClient(1)
    cl.Send('Success')
