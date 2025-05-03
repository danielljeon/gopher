/*******************************************************************************
 * @file xbee_uart.h
 * @brief XBee: abstracting Teensy 4.1 Ardunio: UART.
 *******************************************************************************
 */

#ifndef GOPHER__XBEE_HAL_UART_H
#define GOPHER__XBEE_HAL_UART_H

/** Includes. *****************************************************************/

#include <Arduino.h>

/** Definitions. **************************************************************/

#define RX_BUFFER_SIZE 256

/** Public types. *************************************************************/

/**
 * @brief Structure to manage the XBee API buffer.
 */
typedef struct {
  uint8_t *buffer; // Pointer to the buffer.
  uint16_t size;   // Total buffer size.
  uint16_t index;  // Current index in the buffer.
} xbee_api_buffer_t;

/** Public variables. *********************************************************/

extern uint8_t rx_buffer[RX_BUFFER_SIZE]; // Recive buffer.

/** Public functions. *********************************************************/

/**
 * @brief Send a message over XBee API.
 *
 * This function prepares messages in the XBee API frame format.
 *
 * @param dest_addr 64-bit address of the destination XBee device/node.
 * @param dest_net_addr 16-bit network address of the destination device.
 * @param payload Pointer to the data buffer containing the payload to be sent.
 * @param payload_size The size of the payload in bytes.
 * @param is_critical Determines if the message is critical or non-critical. If
 * set to a non-zero value, the message is marked as critical and will request
 * an acknowledgment (ACK) from the recipient. If set to zero, the message is
 * non-critical and no acknowledgment is required.
 */
void xbee_send_to(uint64_t dest_addr, const char* msg);

const uint8_t* xbee_receive_frame(uint16_t* payloadLen); 
#endif


