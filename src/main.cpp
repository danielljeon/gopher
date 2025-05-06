#include "can_gopher.h"
#include "xbee_uart.h"
#include <Arduino.h>
#include <FlexCAN_T4.h>

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

// CAN.
FlexCAN_T4<CAN1, RX_SIZE_256, TX_SIZE_16> CANbus;

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
  // CAN Rx.
  CAN_message_t rx_can_msg;

  // Attempt to grab a complex CAN message.
  const int is_valid_rx_can_message = CANbus.read(rx_can_msg);

  if (is_valid_rx_can_message) { // Valid CAN message received.
    // Print it as an ASCII string.
    Serial.print("Received CAN message (");
    Serial.print(rx_can_msg.id);
    Serial.print(", ");
    Serial.print(rx_can_msg.len);
    Serial.println(" bytes): ");

    for (uint16_t i = 0; i < rx_can_msg.len; ++i) {
      Serial.print(rx_can_msg.buf[i]);
      Serial.print(" ");
    }
    Serial.println();

    // float values[<MESSAGE_SIGNAL_COUNT_DETERMINED_MANUALLY_FROM_CAN_ID>];
    // decode_ExMessage(frame.data.bytes, values);
  }

  // XBee Rx.
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

    // Send CAN message.
    CAN_message_t tx_can_msg;
    tx_can_msg.id = CAN_GOPHER_COMMAND_A_FRAME_ID;
    can_gopher_command_a_t signal_values[4] = {1, 2, 3, 4};
    uint8_t tx_data[8];
    int dlc =
        can_gopher_command_a_pack(tx_data, signal_values, sizeof(tx_data));
    // Error check `dlc > 0` should be true for a valid message.
    memcpy(tx_can_msg.buf, tx_data, sizeof(tx_data));
    CANbus.write(tx_can_msg);
  }
  lastButtonState = currentState;

  // A small delay to avoid flooding the XBee Serial Rx.
  delay(1);
}
