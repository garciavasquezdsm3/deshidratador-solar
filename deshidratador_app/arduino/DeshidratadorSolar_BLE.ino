/*
  Deshidratador Solar - Firmware BLE para Arduino UNO R4 WiFi
  ------------------------------------------------------------
  Requiere la librería "ArduinoBLE" (Herramientas > Administrar Librerías).
  Placa: Arduino UNO R4 WiFi (tiene módulo BLE integrado).

  Expone un servicio BLE con:
    - Característica de DATOS (notify): manda un JSON con temperatura,
      humedad, batería, modo actual y si el proceso está activo.
    - Característica de COMANDOS (write): recibe órdenes desde el celular
      ("START", "STOP", "MODO:TOMATE", "MODO:CHILE", etc.)
*/

#include <ArduinoBLE.h>

// --- UUIDs del servicio y características (deben coincidir con la app) ---
#define SERVICE_UUID     "19B10000-E8F2-537E-4F6C-D104768A1214"
#define DATA_CHAR_UUID   "19B10001-E8F2-537E-4F6C-D104768A1214"
#define CMD_CHAR_UUID    "19B10002-E8F2-537E-4F6C-D104768A1214"

BLEService dehydratorService(SERVICE_UUID);
BLEStringCharacteristic dataCharacteristic(DATA_CHAR_UUID, BLERead | BLENotify, 120);
BLEStringCharacteristic cmdCharacteristic(CMD_CHAR_UUID, BLEWrite, 30);

// --- Pines (ajusta según tu montaje real) ---
const int PIN_TEMP         = A0;
const int PIN_HUM          = A1;
const int PIN_BATTERY      = A2;
const int PIN_RELAY_MOTOR  = 2;
const int PIN_LED_RUN      = 3;

String modoActual = "TOMATE";
bool procesoActivo = false;
unsigned long ultimoEnvio = 0;
const unsigned long INTERVALO_ENVIO = 2000; // ms entre lecturas enviadas

void setup() {
  Serial.begin(9600);

  pinMode(PIN_RELAY_MOTOR, OUTPUT);
  pinMode(PIN_LED_RUN, OUTPUT);
  digitalWrite(PIN_RELAY_MOTOR, LOW);
  digitalWrite(PIN_LED_RUN, LOW);

  if (!BLE.begin()) {
    Serial.println("Error iniciando BLE!");
    while (1);
  }

  BLE.setLocalName("DeshidratadorSolar");
  BLE.setAdvertisedService(dehydratorService);

  dehydratorService.addCharacteristic(dataCharacteristic);
  dehydratorService.addCharacteristic(cmdCharacteristic);
  BLE.addService(dehydratorService);

  cmdCharacteristic.setEventHandler(BLEWritten, onCommandReceived);
  dataCharacteristic.writeValue("{}");

  BLE.advertise();
  Serial.println("Deshidratador Solar - BLE listo. Esperando conexion...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Conectado a: ");
    Serial.println(central.address());
    digitalWrite(PIN_LED_RUN, HIGH); // opcional: indicador de conexion

    while (central.connected()) {
      unsigned long ahora = millis();
      if (ahora - ultimoEnvio >= INTERVALO_ENVIO) {
        ultimoEnvio = ahora;
        enviarDatos();
      }
    }

    Serial.println("Celular desconectado");
    if (!procesoActivo) digitalWrite(PIN_LED_RUN, LOW);
  }
}

void enviarDatos() {
  float temperatura = leerTemperatura();
  float humedad = leerHumedad();
  int bateria = leerBateria();

  String json = "{";
  json += "\"temp\":" + String(temperatura, 1) + ",";
  json += "\"hum\":" + String(humedad, 1) + ",";
  json += "\"bat\":" + String(bateria) + ",";
  json += "\"modo\":\"" + modoActual + "\",";
  json += "\"activo\":" + String(procesoActivo ? "true" : "false");
  json += "}";

  dataCharacteristic.writeValue(json);
  Serial.println(json);
}

void onCommandReceived(BLEDevice central, BLECharacteristic characteristic) {
  String comando = cmdCharacteristic.value();
  Serial.print("Comando recibido: ");
  Serial.println(comando);

  if (comando == "START") {
    procesoActivo = true;
    digitalWrite(PIN_RELAY_MOTOR, HIGH);
  } else if (comando == "STOP") {
    procesoActivo = false;
    digitalWrite(PIN_RELAY_MOTOR, LOW);
  } else if (comando.startsWith("MODO:")) {
    modoActual = comando.substring(5);
  }

  enviarDatos(); // confirma el estado inmediatamente
}

float leerTemperatura() {
  int lectura = analogRead(PIN_TEMP);
  float voltaje = lectura * (5.0 / 1023.0);
  // Ejemplo genérico para sensor tipo LM35 (ajusta a tu sensor real)
  float tempC = voltaje * 100.0;
  return tempC;
}

float leerHumedad() {
  int lectura = analogRead(PIN_HUM);
  return map(lectura, 0, 1023, 0, 100);
}

int leerBateria() {
  int lectura = analogRead(PIN_BATTERY);
  float voltaje = lectura * (5.0 / 1023.0) * 2.0; // ajusta el divisor a tu circuito
  int porcentaje = (int)((voltaje - 3.0) / (4.2 - 3.0) * 100.0);
  porcentaje = constrain(porcentaje, 0, 100);
  return porcentaje;
}
