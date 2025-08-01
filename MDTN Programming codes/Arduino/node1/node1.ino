// BEFORE STARTING!
// 1) configure ".../Arduino/libraries/MCCI_LoRaWAN_LMIC_library/project_config/lmic_project_config.h"
// 2) define the board version and model in "boards.h"
//

#include <lmic.h>
#include <hal/hal.h>
#include <Arduino.h>
#include <WiFi.h>
//#include "temperature_sensor.h"
//#include <LoRaWan.h>
#include "utilities.h"
#include <DHT.h>
//#include <Wire.h>
//#include <SPI.h>
#include <LoRa.h>  // Assuming you're using LoRa for TTN
//#include "temp_sensor.h"


#define BUILTIN_LED BOARD_LED


//
//  LoRaWAN parameters
//
static const u1_t PROGMEM APPEUI[8]={ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
void os_getArtEui (u1_t* buf) { memcpy_P(buf, APPEUI, 8);}

// This EUI must be in little-endian format. 
// For TTN issued EUIs the last bytes should be 0xD5, 0xB3, 0x70.
// This MUST be in little endian format. (lsb in TTN)
static const u1_t PROGMEM DEVEUI[8]={ 0x3D, 0xF5, 0x06, 0xD0, 0x7E, 0xD5, 0xB3, 0x70 };
void os_getDevEui (u1_t* buf) { memcpy_P(buf, DEVEUI, 8);}

// PM: This key MUST be in big endian format. (msb in TTN)
static const u1_t PROGMEM APPKEY[16] = { 0x83, 0x09, 0x80, 0x2E, 0x1F, 0x7C, 0x20, 0x7A, 0x8F, 0xFD, 0x07, 0x96, 0xEC, 0xB3, 0x4E, 0x0B };
void os_getDevKey (u1_t* buf) {  memcpy_P(buf, APPKEY, 16);}
//
//  end LoRaWAN parameters
//

static uint8_t mydata[] = "Hello, world!";
static osjob_t sendjob;

// Schedule TX every this many seconds (might become longer due to duty
// cycle limitations).
const unsigned TX_INTERVAL = 30;

// PM: Local pin mapping for the Lilygo T3S3
 #define RADIO_CS            RADIO_CS_PIN     // 7
 #define RADIO_RESET         RADIO_RST_PIN    // 8
 #define RADIO_DIO_0         RADIO_DIO0_PIN   // 9
 #define RADIO_DIO_1         RADIO_DIO1_PIN   // 33
 #define RADIO_DIO_2         LMIC_UNUSED_PIN  // void
// #define CONTROL_PIN 35
 #define DHTPIN 35
 #define DHTTYPE DHT22
 #define BATTERY_ADC_PIN 34 

 DHT dht(DHTPIN, DHTTYPE);

const lmic_pinmap lmic_pins = {
     .nss = RADIO_CS,
     .rxtx = LMIC_UNUSED_PIN,
     .rst = RADIO_RESET,
     .dio = {RADIO_DIO_0, RADIO_DIO_1, RADIO_DIO_2}  
};

// Function to simulate getting the battery level
int getBatteryLevel() {
  // Replace with actual battery level reading code
  return 80;  // Simulating 80% battery
}
int getMemoryUsage() {
  // Replace with actual battery level reading code
  return 30;  // Simulating 80% battery
}
int getCpuUsage() {
  // Replace with actual battery level reading code
  return 50;  // Simulating 80% battery
}

//TaskHandle_t Task1;


// Define GPIO pins to control
const int controllable_gpios[] = {33, 15, 16};  // Example GPIOs to control
const int num_gpios = sizeof(controllable_gpios) / sizeof(controllable_gpios[0]);

void printHex2(unsigned v) {
    v &= 0xff;
    if (v < 16)
        Serial.print('0');
    Serial.print(v, HEX);
}

void oledPrintf(int col, int row, const char* fmt, ...) {
  char msg[50];
  va_list args;
  va_start(args, fmt);
  vsprintf(msg, fmt, args);
  va_end(args);
  Serial.println(msg);

  u8g2->clearBuffer();
  u8g2->drawStr(col, row, msg);
  u8g2->sendBuffer();
}

void oledPrintfbrow(int row, const char* fmt, ...) {
  char msg[50];
  va_list args;
  va_start(args, fmt);
  vsprintf(msg, fmt, args);
  va_end(args);
  Serial.println(msg);

  u8g2->clearBuffer();
  u8g2->drawStr(0, (row+1)*10, msg);
  u8g2->sendBuffer();
}

bool isValidGPIO(uint8_t pin) {
  for (uint8_t i = 0; i < sizeof(controllable_gpios); i++) {
    if (controllable_gpios[i] == pin) return true;
  }
  return false;
}

void onEvent (ev_t ev) {
    long now = os_getTime();
    oledPrintfbrow(0, "Time %lu", now);

    switch(ev) {
        case EV_SCAN_TIMEOUT:
            oledPrintf(0, 7, "EV_SCAN_TIMEOUT");
            break;
        case EV_BEACON_FOUND:
            oledPrintf(0, 7, "EV_BEACON_FOUND");
            break;
        case EV_BEACON_MISSED:
            oledPrintf(0, 7, "EV_BEACON_MISSED");
            break;
        case EV_BEACON_TRACKED:
            oledPrintf(0, 7, "EV_BEACON_TRACKED");
            break;
        case EV_JOINING:
            oledPrintf(0, 7, "EV_JOINING");
            break;
        case EV_JOINED:
            oledPrintf(0, 7, "EV_JOINED");
            {
              u4_t netid = 0;
              devaddr_t devaddr = 0;
              u1_t nwkKey[16];
              u1_t artKey[16];
              LMIC_getSessionKeys(&netid, &devaddr, nwkKey, artKey);
              Serial.print("netid: ");
              Serial.println(netid, DEC);
              Serial.print("devaddr: ");
              Serial.println(devaddr, HEX);
              Serial.print("AppSKey: ");
              for (size_t i=0; i<sizeof(artKey); ++i) {
                if (i != 0) Serial.print("-");
                printHex2(artKey[i]);
              }
              Serial.println("");
              Serial.print("NwkSKey: ");
              for (size_t i=0; i<sizeof(nwkKey); ++i) {
                      if (i != 0) Serial.print("-");
                      printHex2(nwkKey[i]);
              }
              Serial.println();
            }
            
            // Disable link check validation (automatically enabled
            // during join, but because slow data rates change max TX
              // size, we don't use it in this example.
            LMIC_setLinkCheckMode(0);
            break;
        case EV_RFU1:
            oledPrintf(0, 7, "EV_RFU1");
            break;
        case EV_JOIN_FAILED:
            oledPrintf(0, 7, "EV_JOIN_FAILED");
            break;
        case EV_REJOIN_FAILED:
            oledPrintf(0, 7, "EV_REJOIN_FAILED");
            break;
        case EV_TXCOMPLETE:
            oledPrintf(0, 7, "EV_TXCOMPLETE");
            digitalWrite(BUILTIN_LED, LOW);
            if (LMIC.txrxFlags & TXRX_ACK) {
              oledPrintf(0, 3, "rssi:%d, snr:%1d", LMIC.rssi, LMIC.snr);
              oledPrintf(0, 6, "Received ack");
            }
            if (LMIC.dataLen) {
              oledPrintf(0, 3, "rssi:%d, snr:%1d", LMIC.rssi, LMIC.snr);
              oledPrintf(0, 6, "Received %d", LMIC.dataLen);
              Serial.print("Data:");
              for(size_t i=0; i<LMIC.dataLen; i++) {
                Serial.print(" ");
                printHex2(LMIC.frame[i + LMIC.dataBeg]);
              }
            if (LMIC.dataLen >= 2) {
              uint8_t gpio_pin = LMIC.frame[LMIC.dataBeg];
              uint8_t state = LMIC.frame[LMIC.dataBeg + 1];

              if (isValidGPIO(gpio_pin)) {
                pinMode(gpio_pin, OUTPUT);
                digitalWrite(gpio_pin, state ? HIGH : LOW);

                Serial.print("GPIO ");
                Serial.print(gpio_pin);
                Serial.print(" seteado a ");
                Serial.println(state ? "ON" : "OFF");
              } else {
                Serial.print("GPIO no válido: ");
                Serial.println(gpio_pin);
              }
            }
 
            }
            // Schedule next transmission
            os_setTimedCallback(&sendjob, os_getTime()+sec2osticks(TX_INTERVAL), do_send);
            break;
        case EV_LOST_TSYNC:
            oledPrintf(0, 7, "EV_LOST_TSYNC");
            break;
        case EV_RESET:
            oledPrintf(0, 7, "EV_RESET");
            break;
        case EV_RXCOMPLETE:
            oledPrintf(0, 7, "EV_RXCOMPLETE");
            break;
        case EV_LINK_DEAD:
            oledPrintf(0, 7, "EV_LINK_DEAD");
            break;
        case EV_LINK_ALIVE:
            oledPrintf(0, 7, "EV_LINK_ALIVE");
            break;
        case EV_SCAN_FOUND:
            oledPrintf(0, 7, "EV_SCAN_FOUND");
            break;
        case EV_TXSTART:
            oledPrintf(0, 3, "EV_TXSTART");
            break;
        case EV_TXCANCELED:
            oledPrintf(0, 7, "EV_TXCANCELED");
            break;
        case EV_RXSTART:
            oledPrintf(0, 7, "EV_RXSTART");
            break;
        case EV_JOIN_TXCOMPLETE:
            oledPrintf(0, 7, "EV_JOIN_TXCOMPLETE");
            break;
        default:
            oledPrintf(0, 7, "Unknown event %ud", ev);
            break;
    }
}


float getBatteryVoltage() {
    int raw = analogRead(BAT_ADC_PIN);
    return raw * (3.3 / 4096.0) * 2;  // Adjust for your voltage divider
}

void do_send(osjob_t* j){
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  float batteryVoltage = getBatteryVoltage();

  if (isnan(temp) || isnan(hum)) {
    Serial.println(F("❌ Error leyendo del sensor DHT22!"));
    dht.begin();
    return;
  }

  // Codificar los datos en 12 bytes: temp (4) + hum (4) + battery (4)
  uint8_t payload[12];
  memcpy(payload, &temp, sizeof(temp));               // 0–3
  memcpy(payload + 4, &hum, sizeof(hum));             // 4–7
  memcpy(payload + 8, &batteryVoltage, sizeof(batteryVoltage)); // 8–11

  // Enviar a TTN (puerto 1, no confirmado)
  if (LMIC_setTxData2(1, payload, sizeof(payload), 0) == 0) {
    Serial.print("📡 Enviando: 🌡 ");
    Serial.print(temp);
    Serial.print(" °C, 💧 ");
    Serial.print(hum);
    Serial.print(" %, 🔋 ");
    Serial.print(batteryVoltage);
    Serial.println(" V");
  } else {
    Serial.println("⚠ Error al intentar enviar los datos.");
  }
  
}

//// Function to control GPIOs
//void setGPIO(int pin, int state) {
//  for (int i = 0; i < num_gpios; i++) {
//    if (pin == controllable_gpios[i]) {
//      pinMode(pin, OUTPUT);
//      digitalWrite(pin, state);
//      return;
//    }
//  }
//  Serial2.println("{\"error\":\"INVALID_PIN\"}");  // GPIO is not controllable
//}
//
//// Function to reset Node 1
//void resetNode() {
//  Serial.println("[Node 1] Resetting device...");
//  // Add reset logic here (e.g., restarting the device)
//  ESP.restart();  // Restart the device
//  Serial2.println("{\"status\":\"RESETTING\"}");  // Inform Controler of the reset
//}

void setup () {
  Serial.begin (115200);
  Serial.println (F ("Starting"));
  initBoard ();
  delay (1500);  // When the power is turned on, a delay is required.
  oledPrintfbrow (2, "Hola! Viva LoRaWAN");
  // LMIC init
  os_init ();
  // Reset the MAC state. Session and pending data transfers will be discarded.
  Serial.println("LMIC reset...");
  LMIC_reset ();
  Serial.println("Setting ADR...");
  LMIC_setAdrMode (false);
  dht.begin();
  // Start job (sending automatically starts OTAA too)
  do_send (&sendjob);
  pinMode (BUILTIN_LED, OUTPUT);
  digitalWrite (BUILTIN_LED, LOW);
  
  
  // Start UART Control Task on Core 1
  xTaskCreatePinnedToCore(
    taskUARTControl,   // Task function
    "UARTControl",     // Task name
    4096,              // Stack size
    NULL,              // Task parameters
    1,                 // Task priority
    NULL, //&Task1,    // Task handle
    1                  // Core 1
  );
  Serial.println("[System] Setup complete. Main loop on Core 0, UART control on Core 1.");
  delay(2000);  // Allow the system to stabilize
// Initialize GPIOs as OUTPUT
  for (int i = 0; i < num_gpios; i++) {
    pinMode(controllable_gpios[i], OUTPUT);
    digitalWrite(controllable_gpios[i], LOW);  // Initialize all to LOW
  }
  
  // Initialize UART2 (assuming you are using pins 45 (TX) and 46 (RX))
  Serial2.begin(115200, SERIAL_8N1, 45, 46);
}


// --- UART CONTROL TASK ---
void taskUARTControl(void *pvParameters) {
  Serial2.begin(115200, SERIAL_8N1, 45, 46); //
  Serial.println("[UART Task] UART2 initialized on GPIO45 TX / GPIO46 RX");
  while (true) {
    String metrics = getSystemMetrics();
    // Serial.println(metrics);  // Print the metrics as a JSON string
    if (Serial2.available()) {
      Serial.println("UART Available");
      String input = Serial2.readStringUntil('\n');// Read incoming data until newline
      input.trim(); // Remove leading/trailing whitespace
      // Serial.println("[UART Task] Received command: " + input);
      // Process the command
      if (input.startsWith("SET_GPIO")) {
        int pin, state;
        int matched = sscanf(input.c_str(), "SET_GPIO %d %d", &pin, &state);

        // Check if the command is valid
        if (matched == 2) {
          // Check if the pin is valid
          bool validPin = false;
          for (int i = 0; i < num_gpios; i++) {
            if (pin == controllable_gpios[i]) {
              validPin = true;
              break;
            }
          }

          if (validPin) {
            // Set the GPIO to the requested state (HIGH or LOW)
            digitalWrite(pin, state == 1 ? HIGH : LOW);
            Serial2.println("{\"status\":\"OK\"}");  // Acknowledge the command
          } else {
            Serial2.println("{\"error\":\"INVALID_PIN\"}");  // Invalid pin number
          }
        } else {
          Serial2.println("{\"error\":\"INVALID_COMMAND\"}");  // Invalid command format
        }
      } else if (input.startsWith("GET_METRICS")) {
        // Respond with system metrics
        String metrics = getSystemMetrics();
        Serial2.println(metrics);
        } else {
          Serial2.println("{\"error\":\"UNKNOWN_COMMAND\"}");  // Unknown command
        } //else if (input.startsWith("RESET")) {
          //resetNode();  // Reset the Node
    }
   yield();
   delay(10); 
  }
} 
float readInternalTemperature() {
  // Read the raw value from the internal temperature sensor (GPIO34 as ADC)
  int raw = analogRead(34);  // ADC1 Channel 4 (GPIO34)
  
  // Convert the raw value to voltage
  float voltage = raw * (3.3 / 4095.0);  // Convert raw ADC value to voltage
  
  // Convert voltage to temperature (°C)
  // The ESP32 internal temperature sensor gives an approximate range of 0-100°C
  float temperature = (voltage - 0.5) * 100;  // Convert voltage to temperature in Celsius
  return temperature;
}
// --- BATTERY VOLTAGE READING FUNCTION USING ADC ---
float readBatteryVoltage() {
  int raw = analogRead(BAT_ADC_PIN);  // Read ADC value from the battery pin
  float voltage = raw * (3.3 / 4095.0);  // Convert raw ADC value to voltage
  // Adjust with a voltage divider if necessary
  return voltage;  // Return the battery voltage in volts
}

 // --- SYSTEM METRICS FUNCTION ---
String getSystemMetrics() {
  // Reading the ESP32 Free heap memory
  uint32_t freeHeap = ESP.getFreeHeap();
  
  // Reading the ESP32 internal temperature using the temperature sensor
  float temp = readInternalTemperature();  // Read internal temperature

  // Reading the System uptime
  uint32_t uptime = millis() / 1000;  // System uptime in seconds

  // Battery Voltage
  float batteryVoltage2 = readBatteryVoltage();

  // Wifi Signal Strength (RSSI)
  int32_t rssi = WiFi.RSSI();


  String json = "{";
  json += "\"cpu\":" + String((float)ESP.getCpuFreqMHz()) + ",";  // CPU frequency
  json += "\"mem\":" + String(freeHeap) + ",";  // Free heap memory
  json += "\"temp\":" + String(temp)+ ",";  // Temperature in Celsius
  json += "\"uptime\":" + String(uptime)+ ",";  // System uptime in seconds
  json += "\"batt\":" + String(batteryVoltage2)+ ",";  // Battery Voltage
  json += "\"rssi\":" + String(rssi);  // Wi-Fi signal strength (RSSI)
  json += "}";

  return json;
}

void loop () {

  os_runloop_once ();
    if (Serial.available()) {
    String command = Serial.readString();  // Read incoming request

    // If the request is "REQUEST_METRICS", send back the metrics
    if (command == "REQUEST_METRICS") {
      // Get system metrics
      Serial.println("Request received, sending metrics..."); 
      int batteryLevel = getBatteryLevel();
      int memoryUsage = getMemoryUsage();
      int cpuUsage = getCpuUsage();

      // Send metrics back in the format 'battery_level, memory_usage, cpu_usage'
      Serial.println(String(batteryLevel) + "," + String(memoryUsage) + "," + String(cpuUsage));
    }
   } 
   yield();
   delay(1);  // Very short delay to yield CPU
}
