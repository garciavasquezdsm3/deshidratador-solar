"""
ble_client.py
--------------
Maneja la conexión Bluetooth Low Energy (BLE) con el Arduino UNO R4 WiFi
usando la librería `bleak` (funciona en Windows/Linux/macOS y también en
Android cuando se empaqueta con python-for-android / buildozer).

Corre su propio event loop de asyncio en un hilo aparte para no bloquear
la interfaz de Kivy, y se comunica con la UI mediante callbacks.
"""

import asyncio
import json
import threading

from bleak import BleakClient, BleakScanner

# Deben coincidir EXACTO con los UUIDs definidos en el sketch de Arduino
SERVICE_UUID = "19b10000-e8f2-537e-4f6c-d104768a1214"
DATA_CHAR_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"
CMD_CHAR_UUID = "19b10002-e8f2-537e-4f6c-d104768a1214"

DEVICE_NAME = "DeshidratadorSolar"


class BLEManager:
    def __init__(self, on_data=None, on_status=None):
        """
        on_data(dict)   -> se llama cuando llega un nuevo paquete de datos
        on_status(str)  -> se llama con mensajes de estado/errores
        """
        self.on_data = on_data
        self.on_status = on_status
        self.client = None
        self.connected = False

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    # ---------- infraestructura del hilo asyncio ----------
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _submit(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def _status(self, msg: str):
        if self.on_status:
            self.on_status(msg)

    # ---------- API pública (llamar desde la UI) ----------
    def scan_and_connect(self):
        self._submit(self._scan_and_connect())

    def send_command(self, command: str):
        if self.client and self.connected:
            self._submit(self._send_command(command))
        else:
            self._status("No conectado: no se pudo enviar el comando")

    def disconnect(self):
        if self.client:
            self._submit(self._disconnect())

    # ---------- corrutinas internas ----------
    async def _scan_and_connect(self):
        self._status("Buscando Deshidratador Solar...")
        try:
            device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
            if device is None:
                self._status("No se encontró el dispositivo. ¿Está encendido y cerca?")
                return

            self._status(f"Conectando a {device.address}...")
            self.client = BleakClient(device, disconnected_callback=self._on_disconnect)
            await self.client.connect()
            self.connected = True
            self._status("Conectado ✔")

            await self.client.start_notify(DATA_CHAR_UUID, self._notification_handler)
        except Exception as e:
            self.connected = False
            self._status(f"Error de conexión: {e}")

    def _notification_handler(self, sender, data: bytearray):
        try:
            payload = json.loads(data.decode("utf-8"))
            if self.on_data:
                self.on_data(payload)
        except Exception as e:
            self._status(f"Error leyendo datos: {e}")

    def _on_disconnect(self, client):
        self.connected = False
        self._status("Dispositivo desconectado")

    async def _send_command(self, command: str):
        try:
            await self.client.write_gatt_char(CMD_CHAR_UUID, command.encode("utf-8"))
        except Exception as e:
            self._status(f"Error enviando comando: {e}")

    async def _disconnect(self):
        try:
            if self.client:
                await self.client.disconnect()
        except Exception:
            pass
        self.connected = False
        self._status("Desconectado")
