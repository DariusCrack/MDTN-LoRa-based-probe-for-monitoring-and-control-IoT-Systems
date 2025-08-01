#include <Arduino.h>

#define RX_PIN 45
#define TX_PIN 46

void setup() {
  Serial.begin(115200);
  while (!Serial) ;
  Serial1.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  Serial.println("Loopback test started");
}

void loop() {
  static unsigned long last = 0;
  // every 1 second, send “ping”
  if (millis() - last >= 1000) {
    last = millis();
    Serial1.println("ping");
    Serial.print("Sent: ping\n");
  }

  // if we got anything back, print it
  while (Serial1.available()) {
    String resp = Serial1.readStringUntil('\n');
    resp.trim();
    if (resp.length()) {
      Serial.print("Echoed: ");
      Serial.println(resp);
    }
  }
}
