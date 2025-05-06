/*******************************************************************************
 * @file xbee_uart.h
 * @brief XBee: abstracting Teensy 4.1 Arduino: UART.
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
 * @brief Transmit an XBee API 0x10 (Transmit Request) frame over UART.
 *
 * @param dest_addr  64-bit address of the target XBee module.
 * @param msg        Null‑terminated C‑string containing the ASCII payload.
 */
void xbee_send(uint64_t destination_address, const char *message);

/**
 * @brief Receive a 0x90 (64‑bit) RX frame and return pointer to payload.
 *
 * @param payloadLen  Output: number of bytes in the payload.
 * @return Pointer to payload start (in internal buffer), or nullptr if no
 *         complete valid frame is available.
 */
const uint8_t *xbee_receive_frame(uint16_t *payload_length);

#endif
