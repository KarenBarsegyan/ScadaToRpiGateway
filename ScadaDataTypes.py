import json
from typing import Union
from pydantic import BaseModel
import time

class ScadaData:
    class SimModel(BaseModel):
        IMEI                : str
        KU                  : int
        SWVersion           : str
        StartProgramming    : str = ''
        EndProgramming      : str = ''
        Result              : bool
        Error               : str
        Command             : str
        Message             : str
        Info                : str

    def __init__(self, data: SimModel):
        self._sim_data = self.SimModel(             
                IMEI = '123456789',
                KU = 1,
                SWVersion = "1.0",
                Result = True,
                Error = "",
                Command = "",
                Message = "",
                Info = ""
            )

    @property
    def Data(self) -> bytes:
        print("getter")
        return bytes(self._sim_data.json().encode('ascii'))
    
    @Data.setter
    def Data(self, dataToSet: bytes):
        print("Setter")
        self._sim_data = json.loads(dataToSet)

    def SetStartTime(self):
        time_string = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        time_string = time_string[:-2] + ':' + time_string[-2:]
        self._sim_data.StartProgramming = time_string

    def SetEndTime(self):
        time_string = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        time_string = time_string[:-2] + ':' + time_string[-2:]
        self._sim_data.EndProgramming = time_string