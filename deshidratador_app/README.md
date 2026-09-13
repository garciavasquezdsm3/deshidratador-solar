# Deshidratador Solar — App Android + Arduino UNO R4 WiFi (BLE)

## 1. Arduino

1. Abre `arduino/DeshidratadorSolar_BLE.ino` en el Arduino IDE.
2. Selecciona la placa **Arduino UNO R4 WiFi** (Herramientas > Placa).
3. Instala la librería **ArduinoBLE** (Herramientas > Administrar Librerías > buscar "ArduinoBLE").
4. Ajusta los pines/sensores reales en la parte de arriba del sketch (temperatura, humedad, batería, relevador del motor).
5. Sube el sketch. Abre el Monitor Serial (9600 baudios) para confirmar que dice
   `Deshidratador Solar - BLE listo. Esperando conexion...`

## 2. App Android (Kivy)

Los archivos `main.py`, `ble_client.py` y `buildozer.spec` ya están listos.
Los UUIDs en `ble_client.py` coinciden con los del sketch — no los cambies
a menos que también los cambies en el `.ino`.

### Compilar el APK

Buildozer solo compila en **Linux** (o WSL en Windows). Pasos:

```bash
# 1. Instala buildozer (una sola vez, en tu máquina Linux/WSL)
pip install --user buildozer cython

# Dependencias del sistema (Ubuntu/Debian)
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 2. Dentro de la carpeta del proyecto (donde está buildozer.spec)
buildozer -v android debug
```

La primera compilación tarda bastante (descarga el Android SDK/NDK).
El APK queda en `bin/deshidratadorsolar-0.1-arm64-v8a-debug.apk`.

Instálalo en el celular:

```bash
adb install bin/deshidratadorsolar-*-debug.apk
```

### Probar antes en la PC (opcional)

Puedes correr `main.py` directo en tu computadora para probar la lógica
(necesitas Bluetooth en la PC y `pip install kivy bleak`):

```bash
pip install kivy bleak
python main.py
```

En Android, `pyjnius`/`android.permissions` solo existen dentro del APK
empacado, por eso el código los importa con `try/except` para no romper
en escritorio.

## 3. Cómo funciona la conexión

- El Arduino anuncia un servicio BLE llamado **"DeshidratadorSolar"**.
- La app escanea, se conecta, y se suscribe a notificaciones de la
  característica de **datos** (temperatura, humedad, batería, modo, estado).
- Al tocar un botón de producto (TOMATE, CHILE, UVA, FRUTA, CARNE,
  PERSONALIZADO) o INICIAR/DETENER, la app escribe un comando en la
  característica de **comandos** (`MODO:TOMATE`, `START`, `STOP`, etc.)
  y el Arduino responde actualizando su estado.

## 4. Android 12+ (permisos en tiempo real)

Android 12+ requiere que el usuario acepte permisos de Bluetooth y
ubicación la primera vez que abre la app (ya están declarados en
`buildozer.spec` y se piden en `main.py` con `request_permissions`).
Si el escaneo no encuentra el dispositivo, revisa que el usuario haya
aceptado esos permisos en Ajustes > Apps > Deshidratador Solar > Permisos.
