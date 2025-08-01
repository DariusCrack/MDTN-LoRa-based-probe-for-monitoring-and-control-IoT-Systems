// BEFORE STARTING!
// 1) configure ".../Arduino/libraries/MCCI_LoRaWAN_LMIC_library/project_config/lmic_project_config.h"
// 2) define the board version and model in "boards.h"
//

#include <lmic.h>
#include <hal/hal.h>
#include <Arduino.h>
//#include <LoRaWan.h>
#include "utilities.h"
#include <DHT.h>
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
 #define RADIO_CS            RADIO_CS_PIN 		// 7
 #define RADIO_RESET         RADIO_RST_PIN		// 8
 #define RADIO_DIO_0         RADIO_DIO0_PIN		// 9
 #define RADIO_DIO_1         RADIO_DIO1_PIN		// 33
 #define RADIO_DIO_2         LMIC_UNUSED_PIN 	// void
// #define CONTROL_PIN 35
 #define DHTPIN 35
 #define DHTTYPE DHT22
 DHT dht(DHTPIN, DHTTYPE);
 const uint8_t validGPIOs[] = {0, 12, 15, 16, 18, 33, 34, 35, 36, 37, 39, 40, 41, 42, 45, 46, 47, 48};


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

// Function to simulate getting memory usage (in bytes)
int getMemoryUsage() {
  // Replace with actual memory usage reading code
  return 1024;  // Simulating 1024 bytes of memory used
}

// Function to simulate getting CPU usage
int getCpuUsage() {
  // Replace with actual CPU usage reading code
  return 35;  // Simulating 35% CPU usage
}



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
  for (uint8_t i = 0; i < sizeof(validGPIOs); i++) {
    if (validGPIOs[i] == pin) return true;
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
    return;
  }

  // Codificar los datos en 12 bytes: temp (4) + hum (4) + battery (4)
  uint8_t payload[12];
  memcpy(payload, &temp, sizeof(temp));               // 0–3
  memcpy(payload + 4, &hum, sizeof(hum));             // 4–7
  memcpy(payload + 8, &batteryVoltage, sizeof(batteryVoltage)); // 8–11

  // Enviar a TTN (puerto 1, no confirmado)
  if (LMIC_setTxData2(1, payload, sizeof(payload), 0) == 0) {
    Serial.print("📡 Enviando: 🌡️ ");
    Serial.print(temp);
    Serial.print(" °C, 💧 ");
    Serial.print(hum);
    Serial.print(" %, 🔋 ");
    Serial.print(batteryVoltage);
    Serial.println(" V");
  } else {
    Serial.println("⚠️ Error al intentar enviar los datos.");
  }
}

void setup () {
  Serial.begin (115200);
  Serial.println (F ("Starting"));

  initBoard ();
  delay (1500);  // When the power is turned on, a delay is required.

  oledPrintfbrow (2, "Hola! Viva LoRaWAN");
  
//  pinMode(37, OUTPUT);
//  digitalWrite(37, HIGH);  // Encender el LED al iniciar
  

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
}
