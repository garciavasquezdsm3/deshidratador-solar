"""
Deshidratador Solar - App Android (Kivy)
----------------------------------------
"""

import asyncio
import threading
import time
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.utils import platform

# Pide permisos de Android en tiempo de ejecución
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission  # type: ignore
        request_permissions([
            Permission.BLUETOOTH_SCAN,
            Permission.BLUETOOTH_CONNECT,
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
        ])
    except Exception:
        pass

# Import de BLE
try:
    from ble_client import BLEManager
except ImportError:
    from ble_client import BLEClient as BLEManager

KV = """
ScreenManager:
    MainScreen:

<MainScreen>:
    name: "main"
    BoxLayout:
        orientation: "vertical"
        padding: 15
        spacing: 10

        Label:
            text: "DESHIDRATADOR SOLAR BLE"
            font_size: "22sp"
            bold: True
            size_hint_y: None
            height: "40dp"

        GridLayout:
            cols: 2
            spacing: 10
            size_hint_y: 0.4

            Button:
                text: "Conectar BLE"
                on_press: app.connect_ble()
            Button:
                text: "Desconectar"
                on_press: app.disconnect_ble()

        BoxLayout:
            orientation: "vertical"
            spacing: 5
            Label:
                text: "Estado BLE: " + app.ble_status
                font_size: "16sp"
            Label:
                text: "Temperatura: " + app.temp_val
                font_size: "18sp"
            Label:
                text: "Humedad: " + app.hum_val
                font_size: "18sp"

        Button:
            text: "Iniciar Deshidratado" if not app.proceso_activo else "Detener Deshidratado"
            size_hint_y: None
            height: "50dp"
            on_press: app.toggle_proceso()
"""

class MainScreen(Screen):
    pass

class DeshidratadorApp(App):
    ble_status = StringProperty("Desconectado")
    temp_val = StringProperty("-- °C")
    hum_val = StringProperty("-- %")
    proceso_activo = BooleanProperty(False)

    def build(self):
        try:
            self.ble = BLEManager(on_data=self.on_ble_data, on_status=self.on_ble_status)
        except TypeError:
            self.ble = BLEManager()

        return Builder.load_string(KV)

    def connect_ble(self):
        self.ble_status = "Buscando..."
        if hasattr(self.ble, 'connect'):
            self.ble.connect()

    def disconnect_ble(self):
        if hasattr(self.ble, 'disconnect'):
            self.ble.disconnect()
        self.ble_status = "Desconectado"

    def toggle_proceso(self):
        self.proceso_activo = not self.proceso_activo

    @mainthread
    def on_ble_status(self, status):
        self.ble_status = str(status)

    @mainthread
    def on_ble_data(self, data):
        # Procesa la trama que llegue por BLE
        pass

if __name__ == '__main__':
    DeshidratadorApp().run()