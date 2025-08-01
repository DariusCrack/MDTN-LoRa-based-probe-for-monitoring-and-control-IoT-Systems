#define LED_PIN_CORE_0 15  // LED pin for Core 0 (or any available pin)
#define LED_PIN_CORE_1 33  // LED pin for Core 1 (or any available pin)

void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  
  // Initialize LED pins
  pinMode(LED_PIN_CORE_0, OUTPUT);
  pinMode(LED_PIN_CORE_1, OUTPUT);

  // Print initial message
  Serial.println("Setup complete. Running on Core 0 and Core 1...");

  // Start UART task on Core 1
  xTaskCreatePinnedToCore(
    taskUARTControl,   // Task function
    "UARTControl",     // Task name
    4096,              // Stack size
    NULL,              // Task parameters
    1,                 // Task priority (lower value means higher priority)
    NULL,              // Task handle
    1                  // Core 1
  );

  // Blink LED to indicate setup completion
  digitalWrite(LED_PIN_CORE_0, HIGH);
  delay(500);
  digitalWrite(LED_PIN_CORE_1, LOW);
  delay(500);
}

void taskUARTControl(void *pvParameters) {
  // Task running on Core 1
  while (true) {
    // Check which core is running the code
    if (xPortGetCoreID() == 1) {
      digitalWrite(LED_PIN_CORE_1, HIGH);  // Turn on LED for Core 1
      delay(1000);  // Delay to simulate main loop execution
      digitalWrite(LED_PIN_CORE_0, LOW);   // Turn off LED for Core 0
      Serial.println("Running on Core 1");
    }
    else {
      Serial.println("Core doesn't exist"); 
    }
  }
}

void loop() {
  // Task running on Core 0
  if (xPortGetCoreID() == 0) {
    digitalWrite(LED_PIN_CORE_0, HIGH);  // Turn on LED for Core 0
    delay(1000);  // Delay to simulate main loop execution
    digitalWrite(LED_PIN_CORE_1, LOW);   // Turn off LED for Core 1
    Serial.println("Running on Core 0");
    delay(1000);
  }
  else {
    Serial.println("Doesn't exist");
    }
  delay(1000);
 
}
