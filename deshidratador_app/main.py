"""
Deshidratador Solar - App Android (Kivy)
------------------------------------------
Se conecta por BLE al Arduino UNO R4 WiFi y muestra temperatura, humedad,
batería y modo actual. Permite elegir el tipo de producto e iniciar/detener
el proceso, igual que el panel físico.
"""

import time

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty

from ble_client import BLEManager

# Pide permisos de Bluetooth/ubicación en Android en tiempo de ejecución.
# En escritorio (para pruebas) simplemente no hace nada.
try:
    from android.permissions import request_permissions, Permission  # type: ignore
    request_permissions([
        Permission.BLUETOOTH_SCAN,
        Permission.BLUETOOTH_CONNECT,
        Permission.ACCESS_FINE_LOCATION,
        Permission.ACCESS_COARSE_LOCATION,
    ])
except ImportError:
    pass  # no estamos en Android


KV = """
#:import utils kivy.utils

ScreenManager:
    MainScreen:

<MainScreen>:
    name: "main"
    canvas.before:
        Color:
            rgba: 0.09, 0.09, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: 16
        spacing: 12

        # ---- Pantalla estilo LCD ----
        BoxLayout:
            size_hint_y: 0.38
            canvas.before:
                Color:
                    rgba: 0.03, 0.08, 0.45, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            BoxLayout:
                orientation: "vertical"
                padding: 14
                spacing: 6

                BoxLayout:
                    size_hint_y: 0.3
                    Label:
                        text: "Deshidratador Solar"
                        color: 0.7, 0.9, 1, 1
                        font_size: "20sp"
                        bold: True
                        halign: "left"
                        text_size: self.size
                    Label:
                        text: root.status_text
                        color: (0.6, 1, 0.6, 1) if root.connected else (1, 0.5, 0.5, 1)
                        font_size: "14sp"
                        size_hint_x: 0.5
                        halign: "right"
                        text_size: self.size

                Label:
                    text: "Modo: [b]" + root.modo_actual + "[/b]     Bat: " + root.bateria + "%     " + root.hora_actual
                    markup: True
                    color: 0.7, 0.9, 1, 1
                    font_size: "16sp"
                    halign: "left"
                    text_size: self.size

                Label:
                    text: "Temp: " + root.temperatura + " °C      Humedad: " + root.humedad + " %"
                    color: 0.7, 0.9, 1, 1
                    font_size: "18sp"
                    bold: True
                    halign: "left"
                    text_size: self.size

                Label:
                    text: root.proceso_text
                    color: (0.4, 1, 0.4, 1) if root.proceso_activo else (1, 0.4, 0.4, 1)
                    font_size: "16sp"
                    bold: True
                    halign: "left"
                    text_size: self.size

        # ---- Botones de tipo de producto ----
        GridLayout:
            cols: 3
            spacing: 10
            size_hint_y: 0.32

            Button:
                text: "TOMATE"
                background_color: 0.75, 0.1, 0.1, 1
                on_release: app.set_modo("TOMATE")
            Button:
                text: "CHILE"
                background_color: 0.75, 0.1, 0.1, 1
                on_release: app.set_modo("CHILE")
            Button:
                text: "UVA"
                background_color: 0.45, 0.1, 0.55, 1
                on_release: app.set_modo("UVA")
            Button:
                text: "FRUTA"
                background_color: 0.85, 0.5, 0.05, 1
                on_release: app.set_modo("FRUTA")
            Button:
                text: "CARNE"
                background_color: 0.3, 0.32, 0.36, 1
                on_release: app.set_modo("CARNE")
            Button:
                text: "PERSONALIZADO"
                background_color: 0.3, 0.32, 0.36, 1
                font_size: "12sp"
                on_release: app.set_modo("PERSONALIZADO")

        # ---- Iniciar / Detener ----
        BoxLayout:
            spacing: 10
            size_hint_y: 0.16

            Button:
                text: "INICIAR"
                background_color: 0.1, 0.65, 0.2, 1
                font_size: "18sp"
                bold: True
                on_release: app.start_process()

            Button:
                text: "DETENER"
                background_color: 0.7, 0.1, 0.1, 1
                font_size: "18sp"
                bold: True
                on_release: app.stop_process()

        # ---- Conexión ----
        BoxLayout:
            spacing: 10
            size_hint_y: 0.14

            Button:
                text: "Conectar al Arduino"
                on_release: app.connect_ble()

            Button:
                text: "Desconectar"
                on_release: app.disconnect_ble()
"""


class MainScreen(Screen):
    status_text = StringProperty("Desconectado")
    connected = BooleanProperty(False)
    modo_actual = StringProperty("TOMATE")
    temperatura = StringProperty("--")
    humedad = StringProperty("--")
    bateria = StringProperty("--")
    hora_actual = StringProperty("")
    proceso_activo = BooleanProperty(False)
    proceso_text = StringProperty("Detenido")


class DeshidratadorApp(App):
    def build(self):
        self.ble = BLEManager(on_data=self.on_ble_data, on_status=self.on_ble_status)
        self.root_widget = Builder.load_string(KV)
        self.screen = self.root_widget.get_screen("main")
        Clock.schedule_interval(self.update_clock, 1)
        return self.root_widget

    def update_clock(self, dt):
        self.screen.hora_actual = time.strftime("%H:%M")

    # ---------- acciones de la UI ----------
    def connect_ble(self):
        self.screen.status_text = "Conectando..."
        self.ble.scan_and_connect()

    def disconnect_ble(self):
        self.ble.disconnect()

    def set_modo(self, modo: str):
        self.screen.modo_actual = modo
        self.ble.send_command(f"MODO:{modo}")

    def start_process(self):
        self.ble.send_command("START")

    def stop_process(self):
        self.ble.send_command("STOP")

    # ---------- callbacks BLE (pueden llegar de otro hilo) ----------
    @mainthread
    def on_ble_data(self, payload: dict):
        self.screen.temperatura = str(payload.get("temp", "--"))
        self.screen.humedad = str(payload.get("hum", "--"))
        self.screen.bateria = str(payload.get("bat", "--"))
        self.screen.modo_actual = payload.get("modo", self.screen.modo_actual)
        activo = payload.get("activo", False)
        self.screen.proceso_activo = activo
        self.screen.proceso_text = "En proceso" if activo else "Detenido"

    @mainthread
    def on_ble_status(self, msg: str):
        self.screen.status_text = msg
        self.screen.connected = self.ble.connected


if __name__ == "__main__":
    DeshidratadorApp().run()
