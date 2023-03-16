from PyQt6.QtCore import QObject, QThread, QRunnable, pyqtSignal
import websockets
import asyncio
# from pydantic import BaseModel
from typing import Union
import json

# class PayLoad(BaseModel):
#     cmd: str
#     log: Union[str, None] = None


class WebSocketClient(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str)

    def __init__(self, ip:str, parent=None):
        QThread.__init__(self, parent)
        self._uri = f"ws://{ip}:8000"

    async def _talk(self) -> None:
        async with websockets.connect(self._uri, ping_timeout = 120) as websocket:          
            await websocket.send(
                json.dumps({'cmd': 'Start Flashing', 'log': ''})
            )

            while True:
                rx_data = json.loads(await websocket.recv())

                # await websocket.send(
                #     json.dumps({'cmd': 'Pong', 'log': ''})
                # )
                # if rx_data['cmd'] == 'Ping':
                #     print("Ping!!!")

                if rx_data['cmd'] == 'Log':
                    self.progress.emit(rx_data['log'])
                elif rx_data['cmd'] == 'End Flashing':
                    break

            self.finished.emit(True)

            # self.finished.emit(False)
        
    
    def run(self) -> None:
        asyncio.run(self._talk())