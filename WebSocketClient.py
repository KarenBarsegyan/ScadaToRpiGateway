from PyQt6.QtCore import QThread, pyqtSignal
import websockets
import asyncio
import json


class WebSocketClient(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str)
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
                try:
                    await websocket.send(
                        json.dumps({'cmd': 'Start Flashing', 'msg': ''})
                    )

                    while True:
                        rx_data = json.loads(await websocket.recv())

                        if rx_data['cmd'] == 'Ping':
                            self.ping.emit()

                        if rx_data['cmd'] == 'Log':
                            self.progress.emit(rx_data['msg'])
                        elif rx_data['cmd'] == 'End Flashing':
                            if rx_data['msg'] == 'Ok':
                                self.finished.emit(True)
                            else:
                                self.finished.emit(False)
                            # print("END")
                            break
                except:
                    print("Error in recv or send")
                    self.finished.emit(False)  

        except:
            print("Error while connecting")
            self.finished.emit(False)
        
    
    def run(self) -> None:
        # print('lol')
        asyncio.run(self._talk())

        # self._loop.create_task(self._talk())

        # try:
        #     self._loop.run_until_complete()
        # except:
        #     pass

        # print('kek')

    # def stop(self) -> None:
    #     self._loop.stop()        