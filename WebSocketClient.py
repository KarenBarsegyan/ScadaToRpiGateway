from PyQt5.QtCore import QThread, pyqtSignal
import websockets
import asyncio
from async_timeout import timeout
import json
import logging 


logs_path = "/home/pi/GatewayLogs"
logger = logging.getLogger(__name__)
f_handler = logging.FileHandler(f'{logs_path}/{__name__}.log')
f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
logger.addHandler(f_handler)
logger.setLevel(logging.WARNING)

class WebSocketClient(QThread):
    finished = pyqtSignal()
    status = pyqtSignal(bool)
    progress = pyqtSignal(str, str)
    ping = pyqtSignal()

    def __init__(self, ip:str, system:str, parent=None):
        QThread.__init__(self, parent)
        self._uri = f"ws://{ip}:8000"
        self._ping_error = 0
        self._system = system

    def __del__(self):
        pass

    async def _talk(self) -> None:
        try:
            async with websockets.connect(self._uri) as websocket:    
                ping_task = asyncio.ensure_future(self._ping(websocket))
                while True:
                    try:
                        await websocket.send(
                            json.dumps({'cmd': 'Start Flashing', 'msg': self._system})
                        )
                        break
                    except:
                        logger.info("Exception 1")
                        await asyncio.sleep(1)

                while True:
                    if self._ping_error > 2:
                        self.progress.emit('LogErr', 'Connection Lost')
                        self.status.emit(False)
                        try:
                            ping_task.cancel()
                        except:
                            logger.info("ERROR Cancelling Ping 0")

                        break

                    try:
                        async with timeout(1):
                            rx_data = json.loads(await websocket.recv())

                        if str(rx_data['cmd']).find('Log') >= 0:
                            self.progress.emit(rx_data['cmd'], rx_data['msg'])
                        elif rx_data['cmd'] == 'End Flashing':
                            if rx_data['msg'] == 'Ok':
                                self.status.emit(True)
                            else:
                                self.status.emit(False)
                            try:
                                ping_task.cancel()
                            except:
                                logger.info("ERROR Cancelling Ping 1")
                            break

                    except asyncio.exceptions.TimeoutError: 
                        logger.info("Exception 2")
                    except:
                        logger.info("Exception 3")
                        await asyncio.sleep(1)

                    await asyncio.sleep(0)


        except asyncio.CancelledError:
            logger.info("Cancelled error in WebSocketClient _talk")
            self.progress.emit('LogErr', 'RPI connection Error')
            self.status.emit(False)   
        except:
            logger.info("Another error in WebSocketClient _talk")
            self.progress.emit('LogErr', 'RPI connection Error')
            self.status.emit(False)             

    async def _ping(self, websocket):
        try:
            while True:
                try:
                    pong_waiter = await websocket.ping()
                    async with timeout(5):
                        await pong_waiter
                    self.ping.emit()
                    self._ping_error = 0
                except asyncio.CancelledError:
                    logger.info("Cancelled error in _ping inside")
                except:
                    # print("Exception in 90")
                    self._ping_error = self._ping_error + 1

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Cancelled error in _ping")
        except:
            logger.info("Another error in _ping")

    def run(self) -> None:
        asyncio.run(self._talk())    
        try:
            self.finished.emit()  
        except Exception as ex:
            logger.info(f"Ex: {ex}") 

class WebSocketClientChecker(QThread):
    finished = pyqtSignal()
    status = pyqtSignal(bool)

    def __init__(self, ip:str, parent=None):
        QThread.__init__(self, parent)
        self._uri = f"ws://{ip}:8000"
        self._ip = ip

    def __del__(self):
        pass

    async def _talk(self) -> None:
        try:
            while True:
                try:
                    async with timeout(0.5):
                        proc = await asyncio.create_subprocess_shell(
                            f'ping -c 1 {self._ip} >/dev/null',
                            shell=True,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await proc.communicate()
                        if not stderr:
                            break
                    
                    self.status.emit(False)
                except asyncio.exceptions.TimeoutError: 
                    logger.info("Exception 4")
                    self.status.emit(False)
                except: 
                    logger.info("Exception 5")
                    self.status.emit(False)
                    await asyncio.sleep(0.5)

                await asyncio.sleep(0)
        
            while True:
                try:
                    async with websockets.connect(self._uri, open_timeout = 0.5) as websocket:  
                        await websocket.send(
                            json.dumps({'cmd': 'Are you ready', 'msg': ''})
                        )
                        rx_data = json.loads(await websocket.recv())

                        if rx_data['cmd'] == 'Ready':
                            self.status.emit(True)
                            break

                        self.status.emit(False)
                except asyncio.exceptions.TimeoutError: 
                    logger.info("Exception 6")
                    self.status.emit(False)
                except:
                    logger.info("Exception 7")
                    self.status.emit(False)
                    await asyncio.sleep(0.5)

                await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info("Cancelled error in WebSocketClientChecker _talk")
        except:
            logger.info("Another error in WebSocketClientChecker _talk")
    
    def run(self) -> None:
        asyncio.run(self._talk()) 
        try:
            self.finished.emit()  
        except Exception as ex:
            logger.info(f"Ex: {ex}") 
