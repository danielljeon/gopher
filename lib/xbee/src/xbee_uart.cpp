/*******************************************************************************
 * @file xbee_uart.cpp
 * @brief XBee: abstracting Teensy 4.1 Ardunio: UART.
 *******************************************************************************
 */

/** Includes. *****************************************************************/

#include "xbee_uart.h"

/** Definitions. **************************************************************/

#define XBEE_TX_BUFFER_SIZE 128 // Opinionated conservative value for overhead.

#define START_DELIMITER 0x7E
#define FRAME_TYPE_TX_REQUEST 0x10

#define FRAME_TYPE_TX_REQUEST 0x10 // Transmit Request frame type.
#define FRAME_ID_WITH_STATUS 0x01  // Non-zero Frame ID for ACK.
#define FRAME_ID_NO_STATUS 0x00    // Zero Frame ID, no ACK.
#define BROADCAST_RADIUS 0x00      // Maximum hops.
#define OPTIONS_WITH_ACK 0x00      // Request ACK.
#define OPTIONS_NO_ACK 0x01        // Disable ACK.

#define TRANSMIT_STATUS 0x8B // Transmit Status (0x8B) confirming delivery.

static HardwareSerial &XBEE_HUART = Serial1;

/** Public variables. *********************************************************/

uint8_t rx_buffer[RX_BUFFER_SIZE];

/** Private variables. ********************************************************/

volatile uint16_t rx_read_index = 0; // Points to where the CPU has processed.

// XBee API frame reading state machine for UART (Rx) usage.
typedef enum {
  WAIT_START_DELIMITER,
  WAIT_LENGTH_HIGH,
  WAIT_LENGTH_LOW,
  WAIT_FRAME_DATA
} frame_state_t;

// Create state machine instance.
frame_state_t frame_state = WAIT_START_DELIMITER;

// UART (Rx) frame processing variables.
uint8_t frame_buffer[XBEE_TX_BUFFER_SIZE];
uint16_t frame_length = 0;
uint16_t frame_index = 0;


// ===== INTERNAL STATE =====

#define MAX_FRAME_SIZE 128

static uint8_t frameBuffer[MAX_FRAME_SIZE];
static uint16_t length = 0;
static uint16_t bytesRead = 0;
static bool inFrame = false;

/** Private functions. ********************************************************/

/**
 * @brief Function to add the start delimiter.
 */
void add_start_delimiter(xbee_api_buffer_t *api_buf) {
  if (api_buf->index < api_buf->size) {
    api_buf->buffer[api_buf->index++] = START_DELIMITER;
  }
}

/**
 * @brief Function to initialize the API buffer.
 */
void init_xbee_api_buffer(xbee_api_buffer_t *api_buf, uint8_t *buf,
                          const uint16_t size) {
  api_buf->buffer = buf;
  api_buf->size = size;
  api_buf->index = 0;

  // Add start delimiter and increment buffer index.
  add_start_delimiter(api_buf);

  // Increment the index by 2 to reserve space for length (will be set by
  // update length).
  api_buf->index += 2;
}

/**
 * @brief Function to update the length.
 *
 * @note Must be called after the frame is complete.
 */
void update_length(const xbee_api_buffer_t *api_buf) {
  const uint16_t length =
      api_buf->index - 3; // Length is total bytes after length field.
                          // Excludes start delimiter and length.
  api_buf->buffer[1] = (length >> 8) & 0xFF; // High byte.
  api_buf->buffer[2] = length & 0xFF;        // Low byte.
}

/**
 * @brief Function to add a single byte of frame data.
 */
void add_byte(xbee_api_buffer_t *api_buf, const uint8_t byte) {
  if (api_buf->index < api_buf->size) {
    api_buf->buffer[api_buf->index++] = byte;
  }
}

/**
 * @brief Function to add multiple bytes (for payloads).
 */
void add_bytes(xbee_api_buffer_t *api_buf, const uint8_t *data,
               const uint16_t length) {
  for (uint16_t i = 0; i < length && api_buf->index < api_buf->size; ++i) {
    api_buf->buffer[api_buf->index++] = data[i];
  }
}

/**
 * @brief Function to calculate and add the checksum.
 */
void add_checksum(xbee_api_buffer_t *api_buf) {
  uint8_t checksum = 0;
  // Checksum is calculated from frame data (from index 3 to end of the frame).
  for (uint16_t i = 3; i < api_buf->index; ++i) {
    checksum += api_buf->buffer[i];
  }
  checksum = 0xFF - checksum;  // XBee checksum formula.
  add_byte(api_buf, checksum); // Add the checksum at the end of the frame.
}

/**
 * @brief Function to finalize the frame (update length and checksum).
 */
void finalize_api_frame(xbee_api_buffer_t *api_buf) {
  update_length(api_buf); // Update the length in the header.
  add_checksum(api_buf);  // Add the checksum to the end.
}

/**
 *@brief Processing frames with 0x8B transmit status header.
 *
 * @param frame Full XBee API frame with 0x8B transmit status header.
 */
void handle_transmit_status(const uint8_t *frame) {
  // Extract frame type byte.
  const uint8_t delivery_status = frame[5];

  if (delivery_status == 0x00) {
    // Success.
    // TODO: Process success.
  } else {
    // Failure.
    // TODO: Process failure, retry/log the error.
  }
}

/**
 * @brief Process complete Rx XBee API frames.
 *
 * @param frame Full XBee API frame.
 * @param length Length of the XBee API frame.
 */
void process_complete_frame(const uint8_t *frame, uint16_t length) {
  // Ensure length is at least 1 to have a checksum byte.
  if (length < 1) {
    return; // Invalid frame length.
  }

  // Calculate checksum over frame data (excluding checksum).
  uint8_t checksum = 0;
  for (uint16_t i = 0; i < length - 1; ++i) {
    checksum += frame[i];
  }
  checksum = 0xFF - checksum;

  // Compare calculated checksum to received checksum.
  if (checksum != frame[length - 1]) {
    // Checksum error, discard frame.
    return;
  }

  const uint8_t frame_type = frame[0];
  if (frame_type == TRANSMIT_STATUS) {
    handle_transmit_status(frame);
  } else {
    // TODO: Handle other frame types if necessary.
  }
}

/**
 * @brief Process incoming data bytes of XBee API frames via UART.
 *
 * @param byte Data byte of XBee API frame.
 */
void handle_incoming_byte(uint8_t byte) {
  switch (frame_state) {
  case WAIT_START_DELIMITER:
    if (byte == START_DELIMITER) {
      frame_index = 0;
      frame_length = 0;
      frame_state = WAIT_LENGTH_HIGH;
    }
    break;

  case WAIT_LENGTH_HIGH:
    frame_length = byte << 8;
    frame_state = WAIT_LENGTH_LOW;
    break;

  case WAIT_LENGTH_LOW:
    frame_length |= byte;
    if (frame_length > XBEE_TX_BUFFER_SIZE) {
      // Invalid frame length, reset state.
      frame_state = WAIT_START_DELIMITER;
    } else {
      frame_state = WAIT_FRAME_DATA;
    }
    break;

  case WAIT_FRAME_DATA:
    if (frame_index < frame_length + 1) { // + 1 for checksum.
      frame_buffer[frame_index++] = byte;
      if (frame_index == frame_length + 1) {
        // Frame complete, process it.
        process_complete_frame(frame_buffer, frame_length + 1);
        frame_state = WAIT_START_DELIMITER;
      }
    } else {
      // Buffer overflow, reset state.
      frame_state = WAIT_START_DELIMITER;
    }
    break;
  }
}

/**
 * @breif Parse data for 0x8B Transmit Status frames and other messages.
 *
 * @param data Received data.
 * @param length Length of data.
 */
void process_data(const uint8_t *data, uint16_t length) {
  for (uint16_t i = 0; i < length; ++i) {
    uint8_t data_byte = data[(rx_read_index + i) % RX_BUFFER_SIZE];

    // Process the byte (e.g., part of an XBee API frame).
    handle_incoming_byte(data_byte);
  }

  // Update the read index.
  rx_read_index = (rx_read_index + length) % RX_BUFFER_SIZE;
}

/** Public functions. *********************************************************/

void xbee_send_to(uint64_t dest_addr, const char* msg) {
  const uint16_t payload_size = strlen(msg);
  const uint16_t max_frame_size = 128;
  uint8_t frame[max_frame_size];
  uint16_t index = 0;

  // Frame delimiter
  frame[index++] = 0x7E;

  // Reserve length bytes
  frame[index++] = 0x00;
  frame[index++] = 0x00;

  // Frame Type: TX Request
  frame[index++] = 0x10;
  frame[index++] = 0x01;

  // 64-bit dest address (big-endian)
  for (int i = 7; i >= 0; i--) {
    frame[index++] = (dest_addr >> (i * 8)) & 0xFF;
  }

  // 16-bit network address (unknown)
  frame[index++] = 0xFF;
  frame[index++] = 0xFE;

  // Broadcast radius + options
  frame[index++] = 0x00;
  frame[index++] = 0x00;

  // Payload
  for (uint16_t i = 0; i < payload_size; i++) {
    frame[index++] = msg[i];
  }

  // Length
  uint16_t length = index - 3;
  frame[1] = (length >> 8) & 0xFF;
  frame[2] = length & 0xFF;

  // Checksum
  uint8_t checksum = 0;
  for (uint16_t i = 3; i < index; i++) {
    checksum += frame[i];
  }
  checksum = 0xFF - checksum;
  frame[index++] = checksum;

  // Send
  Serial1.write(frame, index);
  Serial.println("Frame sent to XBee.");  // Debug message via USB
}


// ===== RECEIVE FUNCTION =====

const uint8_t* xbee_receive_frame(uint16_t* payloadLen) {
  while (Serial1.available()) {
    uint8_t b = Serial1.read();

    if (!inFrame) {
      if (b == 0x7E) {
        inFrame = true;
        bytesRead = 0;
        length = 0;
      }
    } else {
      if (bytesRead == 0) {
        length = b << 8;
      } else if (bytesRead == 1) {
        length |= b;
        if (length > MAX_FRAME_SIZE) {
          inFrame = false;
          return nullptr;
        }
      } else {
        frameBuffer[bytesRead - 2] = b;
      }

      bytesRead++;

      if (bytesRead == length + 3) {
        inFrame = false;

        if (length < 1 || frameBuffer[0] != 0x90) return nullptr;

        *payloadLen = length - 12 - 1; // exclude header and checksum
        return &frameBuffer[12];       // pointer to payload start
      }
    }
  }

  return nullptr;
}