from PyQt6.QtCore import QThread, pyqtSignal
import websockets
import asyncio
import json


class WebSocketClient(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str, str)
    ping = pyqtSignal()

    def __init__(self, ip:str, parent=None):
        print('NEW WORKPLACE')
        QThread.__init__(self, parent)
        self._uri = f"ws://{ip}:8000"
        self._loop = asyncio.get_event_loop()

    def __del__(self): pass
        # print('WORKPLACE DELETED')

    async def _talk(self) -> None:
        try:
            async with websockets.connect(self._uri) as websocket:    
                ping_task = asyncio.ensure_future(self._ping(websocket))
                try:
                    await websocket.send(
                        json.dumps({'cmd': 'Start Flashing', 'msg': ''})
                    )

                    while True:
                        rx_data = json.loads(await websocket.recv())

                        if str(rx_data['cmd']).find('Log') >= 0:
                            self.progress.emit(rx_data['cmd'], rx_data['msg'])
                        elif rx_data['cmd'] == 'End Flashing':
                            if rx_data['msg'] == 'Ok':
                                self.finished.emit(True)
                            else:
                                self.finished.emit(False)
                            # print("END")
                            ping_task.cancel()
                            break
                except:
                    print("Error in recv or send")
                    self.finished.emit(False)  
                    ping_task.cancel()

        except:
            print("Error while connecting")
            self.finished.emit(False)
            

    async def _ping(self, websocket):
        while True:
            try:
                pong_waiter = await websocket.ping()
                await pong_waiter
                self.ping.emit()
            except:
                print("Ping Error")

            await asyncio.sleep(0.5)

    
    def run(self) -> None:
        asyncio.run(self._talk())    