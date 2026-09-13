import asyncio
import threading

try:
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False

class BLEManager:
    def __init__(self, on_data=None, on_status=None):
        self.on_data = on_data
        self.on_status = on_status
        self.client = None
        self.connected = False
        self.loop = None
        self.thread = None

    def _start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, device_address=None):
        if not BLEAK_AVAILABLE:
            if self.on_status:
                self.on_status("Bleak no disponible en este sistema")
            return

        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._start_async_loop, daemon=True)
            self.thread.start()

        if self.loop:
            asyncio.run_coroutine_threadsafe(self._async_connect(device_address), self.loop)

    async def _async_connect(self, device_address):
        try:
            if not device_address:
                devices = await BleakScanner.discover()
                for d in devices:
                    if d.name and "Deshidratador" in d.name:
                        device_address = d.address
                        break

            if device_address:
                self.client = BleakClient(device_address)
                await self.client.connect()
                self.connected = self.client.is_connected
                if self.on_status:
                    self.on_status("Conectado" if self.connected else "Error al conectar")
            else:
                if self.on_status:
                    self.on_status("Dispositivo no encontrado")
        except Exception as e:
            self.connected = False
            if self.on_status:
                self.on_status(f"Error BLE: {e}")

    def disconnect(self):
        if self.client and self.loop and self.connected:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
            self.connected = False
            if self.on_status:
                self.on_status("Desconectado")