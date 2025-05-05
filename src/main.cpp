#include "xbee_uart.h"
#include <Arduino.h>

/** DEFINITIONS. **************************************************************/

// GPIO pins.
#define PUSH_BUTTON_PIN 4
#define TEENSY_LED_PIN 13

// UART pins.
// Peripherals driven by custom drivers have pins defined in their respective
// header files.
#define DEBUG_UART Serial

// XBee 64-bit destination address.
#define XBEE_DESTINATION 0x0013A200424974A1

/** GLOBAL VARIABLES. *********************************************************/

bool lastButtonState = HIGH;
bool currentState = HIGH;

/** SETUP. ********************************************************************/

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

/** LOOP. *********************************************************************/

void loop() {
  uint16_t payloadLen;
  // Attempt to grab a complete RX frame (API 0x90).
  const uint8_t *payload = xbee_receive_frame(&payloadLen);

  if (payload) { // Valid frame received.
    // Print it as an ASCII string.
    Serial.print("Received XBee payload (");
    Serial.print(payloadLen);
    Serial.println(" bytes):");

    // Note: payload is NOT null‑terminated, write byte‑wise.
    for (uint16_t i = 0; i < payloadLen; ++i) {
      Serial.write(payload[i]);
    }
    Serial.println();
  }

  // On push button press.
  currentState = digitalRead(PUSH_BUTTON_PIN);
  if (currentState == LOW && lastButtonState == HIGH) {
    delay(20); // Debounce.
    DEBUG_UART.println("Button pressed");

    // Transmit and check success.
    xbee_send(XBEE_DESTINATION, "test");
  }
  lastButtonState = currentState;

  // A small delay to avoid flooding the XBee Serial Rx.
  delay(1);
}
