import json
from typing import Union
from pydantic import BaseModel
import time

class ScadaData:
    class SimModel(BaseModel):
        IMEI                : str = ''
        KU                  : int = 0
        ProgrammingsCnt     : int = 0
        SWVersion           : str = ''
        StartProgramming    : str = ''
        EndProgramming      : str = ''
        Result              : bool = False
        Error               : str = ''
        Command             : str = ''
        Message             : str = ''
        Info                : str = ''

    def __init__(self, dataToSet = None):
        if not dataToSet == None:
            self.sim_data = ScadaData.SimModel(**dataToSet)

    def GetDataInBytes(self) -> bytes:
        return bytes(self.sim_data.json().encode('ascii'))
    
    def SetDataFromBytes(self, dataToSet: bytes):
        self.sim_data = ScadaData.SimModel(**json.loads(dataToSet))

    def set_data(self, input_data: str):
        self.sim_data = input_data

    def SetStartTime(self):
        time_string = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        time_string = time_string[:-2] + ':' + time_string[-2:]
        self.sim_data.StartProgramming = time_string

    def SetEndTime(self):
        time_string = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        time_string = time_string[:-2] + ':' + time_string[-2:]
        self.sim_data.EndProgramming = time_string
        