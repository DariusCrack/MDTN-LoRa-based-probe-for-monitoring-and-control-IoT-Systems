#include <Arduino.h>

// UART1 pins on ESP32-S3
#define UART_RX_PIN 42   // RX ← Pi TX (GPIO14, Pi pin 8)
#define UART_TX_PIN 41   // TX → Pi RX (GPIO15, Pi pin 10)

void setup() {
  // USB Serial for debug (COM port)
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  Serial.println("=== T3-S3 starting ===");

  // UART1 for Pi ↔ ESP32-S3
  Serial1.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  Serial.println("Serial1 initialized on RX=42, TX=41");
}

void loop() {
  // Check for incoming data on UART1
  if (Serial1.available()) {
    // Read until newline
    String line = Serial1.readStringUntil('\n');
    line.trim();  // remove CR/LF or whitespace

    if (line.length() > 0) {
      // 1) Print what was received
      Serial.print("Received data: ");
      Serial.println(line);

      // 2) If it was exactly "hello", respond
      if (line == "hello") {
        Serial1.println("hello buddy");
        Serial.println("Sent: hello buddy");
      }
    }
  }
  else {
    Serial.println("UART not available");
    delay(5000);
    }
}
