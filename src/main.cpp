#include <Arduino.h>
#include "xbee_uart.h"

/** DEFINITIONS. */

// GPIO pins.
#define PUSH_BUTTON_PIN 4
#define TEENSY_LED_PIN 13

// UART pins.
// Peripherals driven by custom drivers have pins defined in their respective
// header files.
#define DEBUG_UART Serial

// XBee 64-bit destination address.
#define XBEE_DESTINATION 0x0013A200424974A1

/** GLOBAL VARIABLES. */

bool lastButtonState = HIGH;
bool currentState = HIGH;

void setup() {
  /** PIN MODES. */

  // Push button.
  pinMode(PUSH_BUTTON_PIN, INPUT_PULLUP);

  // Debug LED.
  pinMode(TEENSY_LED_PIN, OUTPUT);
  digitalWrite(TEENSY_LED_PIN, LOW);

  /** INITIALIZATION FUNCTIONS. */

  // Init Debug UART.
  DEBUG_UART.begin(115200);
  DEBUG_UART.println("Started Gopher...");

  // Init XBee UART.
  XBEE_UART.begin(115200);

  DEBUG_UART.println("Teensy XBee UART ready.");
}

void loop() {
  // On push button press.
  currentState = digitalRead(PUSH_BUTTON_PIN);
  if (currentState == LOW && lastButtonState == HIGH) {
    delay(20); // Debounce.
    DEBUG_UART.println("Button pressed");

    if (digitalRead(PUSH_BUTTON_PIN) == LOW) {
      // Transmit and check success.
      xbee_send(XBEE_DESTINATION, "test");
    }
  }
  lastButtonState = currentState;
}
