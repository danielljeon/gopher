/*******************************************************************************
 * @file xbee_uart.cpp
 * @brief XBee: abstracting Teensy 4.1 Arduino: UART.
 *******************************************************************************
 */

/** Includes. *****************************************************************/

#include "xbee_uart.h"

/** Definitions. **************************************************************/

#define XBEE_MAX_FRAME_SIZE 128 // Opinionated conservative value for overhead.

#define START_DELIMITER 0x7E
#define FRAME_TYPE_TX_REQUEST 0x10

#define FRAME_TYPE_TX_REQUEST 0x10 // Transmit Request frame type.
#define FRAME_ID_WITH_STATUS 0x01  // Non-zero Frame ID for ACK.
#define FRAME_ID_NO_STATUS 0x00    // Zero Frame ID, no ACK.
#define BROADCAST_RADIUS 0x00      // Maximum hops.
#define OPTIONS_WITH_ACK 0x00      // Request ACK.
#define OPTIONS_NO_ACK 0x01        // Disable ACK.

#define TRANSMIT_STATUS 0x8B // Transmit Status (0x8B) confirming delivery.

/** Teensy Arduino pin configurations. ****************************************/

HardwareSerial &XBEE_UART = Serial1;

/** Private variables. ********************************************************/

// UART (Rx) frame processing variables.
static uint8_t frame_buffer[XBEE_MAX_FRAME_SIZE];
static uint16_t length = 0;
static uint16_t bytes_read = 0;
static bool in_frame = false;

/** Public functions. *********************************************************/

void xbee_send(uint64_t destination_address, const char *message) {
  const uint16_t payload_size = strlen(message);
  uint8_t frame[XBEE_MAX_FRAME_SIZE];
  uint16_t index = 0;

  // 1. Start delimiter.
  frame[index++] = START_DELIMITER;

  // 2. Reserve two bytes for length (filled in later).
  index += 2;

  // 3. API frame header.
  frame[index++] = FRAME_TYPE_TX_REQUEST; // Frame Type.
  frame[index++] = FRAME_ID_WITH_STATUS;  // Frame ID.

  // 4. 64‑bit destination (big‑endian).
  for (int8_t i = 7; i >= 0; --i) {
    frame[index++] = (destination_address >> (i * 8)) & 0xFF;
  }

  // 5. 16‑bit network address (unknown).
  frame[index++] = 0xFF;
  frame[index++] = 0xFE;

  // 6. Broadcast radius and options.
  frame[index++] = 0x00; // Radius.
  frame[index++] = 0x00; // Options.

  // 7. RF Data payload.
  memcpy(&frame[index], message, payload_size);
  index += payload_size;

  // 8. Fill in length (number of bytes from frame[3] to frame[index‑1]).
  uint16_t data_len = index - 3;
  frame[1] = (data_len >> 8) & 0xFF;
  frame[2] = data_len & 0xFF;

  // 9. Checksum: 0xFF, (sum of all bytes from frame[3] to frame[index‑1]).
  uint8_t sum = 0;
  for (uint16_t i = 3; i < index; ++i) {
    sum += frame[i];
  }
  frame[index++] = 0xFF - sum;

  // 10. Transmit frame.
  XBEE_UART.write(frame, index);
}

const uint8_t *xbee_receive_frame(uint16_t *payload_length) {
  while (XBEE_UART.available()) {
    uint8_t b = XBEE_UART.read();

    if (!in_frame) {
      if (b == START_DELIMITER) {
        in_frame = true;
        bytes_read = 0;
        length = 0;
      }
    } else {
      // Read length MSB, LSB, then data and checksum.
      if (bytes_read == 0) {
        length = (uint16_t)b << 8;
      } else if (bytes_read == 1) {
        length |= b;
        // Enforce both upper and lower bounds.
        if (length > XBEE_MAX_FRAME_SIZE || length < 12) {
          in_frame = false;
          return nullptr;
        }
      } else {
        // Store both frame‐data and checksum.
        frame_buffer[bytes_read - 2] = b;
      }

      bytes_read++;

      // Length + 2 length‐bytes + 1 checksum = total bytes after delimiter.
      if (bytes_read == length + 3) {
        in_frame = false;

        // 1) Verify checksum.
        uint8_t sum = 0;
        for (uint16_t i = 0; i < length; ++i) {
          sum += frame_buffer[i];
        }
        uint8_t checksum = frame_buffer[length];
        if ((uint8_t)(sum + checksum) != 0xFF) { // Bad CRC.

          return nullptr;
        }

        // 2) Only accept 0x90 (RX 64‑bit).
        if (frame_buffer[0] != 0x90) {
          return nullptr;
        }

        // 3) Compute and return payload slice.
        // Header = 1 (type) + 8 (addr64) + 2 (network) + 1 (options) = 12.
        *payload_length = length - 12;
        return &frame_buffer[12];
      }
    }
  }

  return nullptr;
}
