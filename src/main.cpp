/*******************************************************************************
 * @file main.cpp
 * @brief Main logic for Gopher.
 *******************************************************************************
 */

/** Includes. *****************************************************************/

#include "can_gopher.h"
#include "xbee_uart.h"
#include <Arduino.h>
#include <FlexCAN_T4.h>

/** Public variables. *********************************************************/

bool lastButtonState = HIGH;
bool currentState = HIGH;

/** Teensy Arduino pin configurations. ****************************************/

// Peripherals driven by custom drivers have pins defined in their respective
// header files.

// GPIO pins.
#define PUSH_BUTTON_PIN 4
#define TEENSY_LED_PIN 13

// UART pins.
#define DEBUG_UART Serial

// XBee 64-bit destination address.
#define XBEE_DESTINATION 0x0013A200424974A1

// CAN.
FlexCAN_T4<CAN1, RX_SIZE_256, TX_SIZE_16> CANbus;

/** Private functions. ********************************************************/

/**
 * @brief CAN bus message receive logic (polling based).
 */
void can_rx(void) {
  // CAN Rx.
  CAN_message_t rx_can_msg;

  // Attempt to grab a complex CAN message.
  const int is_valid_rx_can_message = CANbus.read(rx_can_msg);

  if (is_valid_rx_can_message) { // Valid CAN message received.

    // Print CAN message information.
    Serial.print("Received CAN message (");
    Serial.print(rx_can_msg.id);
    Serial.print(", ");
    Serial.print(rx_can_msg.len);
    Serial.println(" bytes): ");
    for (uint16_t i = 0; i < rx_can_msg.len; ++i) {
      Serial.print(rx_can_msg.buf[i]);
      Serial.print(" ");
    }
    Serial.println(); // Next line.
  }
}

/**
 * @brief XBee message receive logic (polling based).
 */
void xbee_rx(void) {
  uint16_t payloadLen;
  // Attempt to grab a complete RX frame (API 0x90).
  const uint8_t *payload = xbee_receive_frame(&payloadLen);

  if (payload) { // Valid frame received.

    // Print XBee message as an ASCII string.
    Serial.print("Received XBee payload (");
    Serial.print(payloadLen);
    Serial.println(" bytes):");
    for (uint16_t i = 0; i < payloadLen; ++i) {
      // Note: payload is NOT null‑terminated, write byte‑wise.
      Serial.write(payload[i]);
    }
    Serial.println(); // Next line.
  }
}

/**
 * @brief Post push button press logic.
 */
void push_button_post_actions(void) {
  CAN_message_t tx_can_msg;

  // Debug message.
  DEBUG_UART.println("Button pressed");

  // Send XBee message.
  xbee_send(XBEE_DESTINATION, "test");

  // Form CAN message.
  tx_can_msg.id = CAN_GOPHER_COMMAND_A_FRAME_ID;
  can_gopher_command_a_t signal_values[4] = {1, 2, 3, 4};
  uint8_t tx_data[8];
  int dlc = can_gopher_command_a_pack(tx_data, signal_values, sizeof(tx_data));
  // TODO: Error check `dlc > 0` should be true for a valid message.
  memcpy(tx_can_msg.buf, tx_data, sizeof(tx_data));

  // Send CAN message.
  CANbus.write(tx_can_msg);
}

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

  // Init CAN bus.
  CANbus.begin();
  CANbus.setBaudRate(500000);
  CANbus.enableFIFO();
  DEBUG_UART.println("CAN bus ready.");

  // Init XBee UART.
  XBEE_UART.begin(115200);
  DEBUG_UART.println("Teensy XBee UART ready.");
}

/** LOOP. *********************************************************************/

void loop() {
  // Incoming communications.
  can_rx();  // Handle CAN bus receive.
  xbee_rx(); // Handle XBee receive.

  // On push button press.
  currentState = digitalRead(PUSH_BUTTON_PIN);
  if (currentState == LOW && lastButtonState == HIGH) {
    delay(20);                  // Debounce.
    push_button_post_actions(); // Take actions.
  }
  lastButtonState = currentState;

  delay(1); // Small delay to avoid Rx communications flooding.
}
