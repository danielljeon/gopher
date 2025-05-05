/*******************************************************************************
 * @file xbee_uart.h
 * @brief XBee: abstracting Teensy 4.1 Ardunio: UART.
 *******************************************************************************
 */

#ifndef GOPHER__XBEE_HAL_UART_H
#define GOPHER__XBEE_HAL_UART_H

/** Includes. *****************************************************************/

#include <Arduino.h>

/** Teensy Arduino pin configurations. ****************************************/

extern HardwareSerial &XBEE_UART;

/** Public functions. *********************************************************/

/**
 * @brief Send a message.
 */
void xbee_send(uint64_t dest_addr, const char *msg);

/**
 * @brief Receive a message.
 * 
 * @return Pointer to message buffer location.
 * @retval nullptr if no message available.
 */
const uint8_t *xbee_receive_frame(uint16_t *payloadLen);

#endif
