"""Main module."""

import asyncio

from digi.xbee.devices import XBeeMessage
from digi.xbee.models.status import TransmitStatus
from digi.xbee.packets.common import TransmitStatusPacket

from gopher import Gopher
from orientation import run_orientation_gui

# Create Gopher instance and start operation.
gopher_instance = Gopher()
startup_status = False


# Create example Rx call back function.
def print_console_rx_callback(xbee_message: XBeeMessage):
    gopher_instance.log_xbee_message(xbee_message)
    print(
        f"Message received from {xbee_message.remote_device.get_64bit_addr()}: "
        f"{xbee_message.data.decode()}"
    )


# Shutdown procedure example.
async def shutdown_example():
    await gopher_instance.shutdown()


async def attempt_startup(com_port_number: int):
    global startup_status
    if not startup_status:
        try:
            print(f"Attempting startup with COM{com_port_number} ... ", end="")

            gopher_instance.start(
                db_url="sqlite:///xbee_log.db",
                xbee_port=f"COM{com_port_number}",
                xbee_tx_callbacks=[],
                xbee_rx_callbacks=[],
                xbee_baud_rate=115200,
            )
            await gopher_instance.open_xbee_async()
            await gopher_instance.shutdown()

            print("Success")
            startup_status = True

        except RuntimeError:
            print("Fail")


async def establish_com_port():
    for i in range(20):
        await attempt_startup(i + 1)


async def example(destination_address: str):
    """Example script to test basic operations.

    Args:
        destination_address: 64-bit hex destination address.
            Example: "1234567890ABCDEF".

    Returns:

    """
    await gopher_instance.open_xbee_async()

    try:
        print("Started Gopher")
        print()

        print(
            'Type "send broadcast" to send a broadcast message\n'
            'Type "send ack" to send a message with ack (0x10, 0x8B response)\n'
            'Type "send" to send a message without ack\n'
            'Type "read" to read all data on the database\n'
            'Type "exit" to end program\n'
        )

        example_trigger = None

        while example_trigger != "exit":

            # Example trigger and message sending.
            example_trigger = input("> ").lower().strip()

            if example_trigger == "send broadcast":
                gopher_instance.send_xbee_message_broadcast(
                    data="Hello world with broadcast",
                )

            elif example_trigger == "send ack":
                status = gopher_instance.send_xbee_message(
                    destination=destination_address,
                    data="Hello world with ack",
                    ack=True,
                )
                print("\tSent message with ack")

                if (
                    isinstance(status, TransmitStatusPacket)
                    and status.transmit_status == TransmitStatus.SUCCESS
                ):
                    print("\t\tSuccessful ack received")
                else:
                    print("\t\tFailed ack")

            elif example_trigger == "send":
                gopher_instance.send_xbee_message(
                    destination=destination_address,
                    data="Hello world",
                    ack=False,
                )
                print("\tSent message (no ack)")

            elif example_trigger == "read":
                messages = gopher_instance.get_all_xbee_messages()
                for m in messages:
                    print(f"\t\tdb: {m}")

            elif example_trigger == "exit":
                print("\tExiting programing...")
                raise KeyboardInterrupt

            await asyncio.sleep(1)  # Run async indefinitely.

    except KeyboardInterrupt:
        print("\tGopher Shutdown")
        await gopher_instance.shutdown()


if __name__ == "__main__":
    asyncio.run(establish_com_port())

    if startup_status:
        asyncio.run(run_orientation_gui(gopher_instance))
