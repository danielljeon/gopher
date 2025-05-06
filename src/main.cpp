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

bool prev_button_state = HIGH;
bool button_state = HIGH;

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
FlexCAN_T4<CAN1, RX_SIZE_256, TX_SIZE_16> can_bus;

/** Private functions. ********************************************************/

/**
 * @brief CAN bus message receive logic (polling based).
 */
void can_rx(void) {
  // CAN Rx.
  CAN_message_t rx_can_msg;

  // Attempt to grab a complex CAN message.
  const int is_valid_rx_can_message = can_bus.read(rx_can_msg);

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
  uint16_t xbee_payload_length;
  // Attempt to grab a complete RX frame (API 0x90).
  const uint8_t *payload = xbee_receive_frame(&xbee_payload_length);

  if (payload) { // Valid frame received.

    // Print XBee message as an ASCII string.
    Serial.print("Received XBee payload (");
    Serial.print(xbee_payload_length);
    Serial.println(" bytes):");
    for (uint16_t i = 0; i < xbee_payload_length; ++i) {
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
  can_bus.write(tx_can_msg);
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
  can_bus.begin();
  can_bus.setBaudRate(500000);
  can_bus.enableFIFO();
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
  button_state = digitalRead(PUSH_BUTTON_PIN);
  if (button_state == LOW && prev_button_state == HIGH) {
    delay(20);                  // Debounce.
    push_button_post_actions(); // Take actions.
  }
  prev_button_state = button_state;

  delay(1); // Small delay to avoid Rx communications flooding.
}
