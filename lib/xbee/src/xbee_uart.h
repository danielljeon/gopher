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

/** Teensy Ardunio pin configurations. ****************************************/

extern HardwareSerial &XBEE_UART;

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
 */
void xbee_send(uint64_t dest_addr, const char *msg);

const uint8_t *xbee_receive_frame(uint16_t *payloadLen);

#endif
