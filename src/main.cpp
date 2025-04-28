#include <Arduino.h>
#include "xbee_uart.h"

const int buttonPin = 4; // Pushbutton
bool lastButtonState = HIGH;



void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(33, OUTPUT);     // Debug LED
  digitalWrite(33, LOW);

  Serial.begin(115200);      // USB debug output
  Serial.println("Test");
  Serial1.begin(115200);   // XBee UART

  Serial.println("Teensy XBee TX ready.");
}

void loop() {
  bool currentState = digitalRead(buttonPin);

  if (currentState == LOW && lastButtonState == HIGH) {
    delay(20);  // Debounce
    if (digitalRead(buttonPin) == LOW) {
      digitalWrite(33, HIGH);

      // ⬇️ Replace this with your XCTU-connected XBee address
      uint64_t dest = 0x0013A200424974A1; // XBee address

      xbee_send_to(dest, "test");

      delay(500); // Give the radio time
      digitalWrite(33, LOW);
    }
  }

  lastButtonState = currentState;
}
