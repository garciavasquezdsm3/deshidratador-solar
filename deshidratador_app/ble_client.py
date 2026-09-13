import asyncio
import threading

# Intentamos importar bleak de forma segura
try:
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False

class BLEManager:
    def __init__(self, service_uuid=None, char_uuid=None):
        self.service_uuid = service_uuid
        self.char_uuid = char_uuid
        self.client = None
        self.connected = False
        self.loop = None
        self.thread = None

    def _start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, device_address=None, callback=None):
        if not BLEAK_AVAILABLE:
            print("[BLE] Advertencia: Bleak no está instalado o no es compatible en esta plataforma.")
            if callback:
                callback(False)
            return

        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._start_async_loop, daemon=True)
            self.thread.start()

        if self.loop:
            asyncio.run_coroutine_threadsafe(self._async_connect(device_address, callback), self.loop)

    async def _async_connect(self, device_address, callback):
        try:
            # Si no se pasa dirección, busca dispositivos de forma segura
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
            else:
                self.connected = False

            if callback:
                callback(self.connected)
        except Exception as e:
            print(f"[BLE Error] Falló la conexión: {e}")
            self.connected = False
            if callback:
                callback(False)

    def disconnect(self):
        if self.client and self.loop and self.connected:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
            self.connected = False