from PyQt6.QtCore import QThread, pyqtSignal
import websockets
import asyncio
from async_timeout import timeout
import json
import os


class WebSocketClient(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str, str)
    ping = pyqtSignal()

    def __init__(self, ip:str, cmd:str, parent=None):
        QThread.__init__(self, parent)
        self._uri = f"ws://{ip}:8000"
        self._ip = ip
        self._loop = asyncio.get_event_loop()
        self._cmd = cmd
        self._ping_error = 0

    def __del__(self):
        pass

    async def _talk(self) -> None:
        if self._cmd == 'Start':
            try:
                async with websockets.connect(self._uri) as websocket:    
                    ping_task = asyncio.ensure_future(self._ping(websocket))
                    try:
                        await websocket.send(
                            json.dumps({'cmd': 'Start Flashing', 'msg': ''})
                        )

                        while True:

                            if self._ping_error > 5:
                                return

                            try:
                                async with timeout(3):
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

                            except asyncio.exceptions.TimeoutError: pass
                            
                    except:
                        print("Error in recv or send")
                        self.finished.emit(False)  
                        ping_task.cancel()
            except:
                print("Error while connecting")
                self.finished.emit(False)

        if self._cmd == 'Ping':
            while True:
                try:
                    proc = await asyncio.create_subprocess_shell(
                        f'ping -c 1 {self._ip} >/dev/null',
                        shell=True,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    if not stderr:
                        break

                except: pass

                await asyncio.sleep(1)
        
            while True:
                try:
                    async with websockets.connect(self._uri, open_timeout = 0.5) as websocket:  
                        await websocket.send(
                            json.dumps({'cmd': 'Are you ready', 'msg': ''})
                        )
                        rx_data = json.loads(await websocket.recv())

                        if rx_data['cmd'] == 'Ready':
                            self.finished.emit(True)
                            break
                except asyncio.exceptions.TimeoutError: 
                    pass
                except:
                    pass

                await asyncio.sleep(3)

    async def _ping(self, websocket):
        while True:
            try:
                pong_waiter = await websocket.ping()
                await pong_waiter
                self.ping.emit()
                self._ping_error = 0
            except:
                self._ping_error = self._ping_error + 1
                print("Ping Error")

            await asyncio.sleep(0.5)

    
    def run(self) -> None:
        asyncio.run(self._talk())    