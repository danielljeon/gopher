/*******************************************************************************
 * @file main.cpp
 * @brief Main logic for Gopher.
 *******************************************************************************
 */

/** Includes. *****************************************************************/

#include "can_gopher.h"
#include "configurations.h"
#include "xbee_uart.h"
#include <Arduino.h>
#include <FlexCAN_T4.h>
#include <SD.h>

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
#ifdef GOPHER_DEBUG_SERIAL
#define DEBUG_UART Serial
#endif

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
#ifdef GOPHER_DEBUG_SERIAL
    DEBUG_UART.print("Received CAN message (");
    DEBUG_UART.print(rx_can_msg.id);
    DEBUG_UART.print(", ");
    DEBUG_UART.print(rx_can_msg.len);
    DEBUG_UART.println(" bytes): ");
    for (uint16_t i = 0; i < rx_can_msg.len; ++i) {
      DEBUG_UART.print(rx_can_msg.buf[i]);
      DEBUG_UART.print(" ");
    }
    DEBUG_UART.println(); // Next line.
#endif
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
#ifdef GOPHER_DEBUG_SERIAL
    DEBUG_UART.print("Received XBee payload (");
    DEBUG_UART.print(xbee_payload_length);
    DEBUG_UART.println(" bytes):");

    for (uint16_t i = 0; i < xbee_payload_length; ++i) {
      // Note: payload is NOT null‑terminated, write byte‑wise.
      DEBUG_UART.write(payload[i]);
    }
    DEBUG_UART.println(); // Next line.
#endif
  }
}

/**
 * @brief Post push button press logic.
 */
void push_button_post_actions(void) {
  CAN_message_t tx_can_msg;

// Debug message.
#ifdef GOPHER_DEBUG_SERIAL
  DEBUG_UART.println("Button pressed");
#endif

  // Send XBee message.
  xbee_send(XBEE_DESTINATION_64, "test");

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
#ifdef GOPHER_DEBUG_SERIAL
  DEBUG_UART.begin(115200);
  DEBUG_UART.println("Started Gopher...");
#endif

  // Init SDIO.
  if (!SD.begin(BUILTIN_SDCARD)) {
#ifdef GOPHER_DEBUG_SERIAL
    DEBUG_UART.println("SD not detected!");
#endif
  } else {
#ifdef GOPHER_DEBUG_SERIAL
    DEBUG_UART.println("SD ready.");
#endif
  }

  // Init SD card write.
  File data_file = SD.open("log.txt", FILE_WRITE);
  if (data_file) {
    data_file.println("Logging started"); // Write to SD.
    data_file.close();
#ifdef GOPHER_DEBUG_SERIAL
    DEBUG_UART.println("Wrote to log.txt.");
#endif
  } else {
#ifdef GOPHER_DEBUG_SERIAL
    DEBUG_UART.println("Error opening log.txt.");
#endif
  }

  // Init CAN bus.
  can_bus.begin();
  can_bus.setBaudRate(500000);
  can_bus.enableFIFO();
#ifdef GOPHER_DEBUG_SERIAL
  DEBUG_UART.println("CAN bus ready.");
#endif

  // Init XBee UART.
  XBEE_UART.begin(115200);
#ifdef GOPHER_DEBUG_SERIAL
  DEBUG_UART.println("Teensy XBee UART ready.");
#endif
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
