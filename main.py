"""Main module."""

import asyncio

from digi.xbee.devices import XBeeMessage
from digi.xbee.models.status import TransmitStatus

from gopher import Gopher

TEST_LOCAL_PORT = "COM1"
TEST_DESTINATION_ADDRESS = "1234567890ABCDEF"


# Create example Rx call back function.
def on_xbee_message_received(xbee_message: XBeeMessage):
    gopher_instance.log_xbee_message(xbee_message)
    print(
        f"Message received from {xbee_message.remote_device.get_64bit_addr()}: "
        f"{xbee_message.data.decode()}"
    )


# Shutdown procedure example.
async def shutdown_example():
    await gopher_instance.shutdown()


# Create Gopher instance and start operation.
gopher_instance = Gopher()
gopher_instance.start(
    db_url="sqlite:///xbee_log.db",
    xbee_port=TEST_LOCAL_PORT,
    xbee_rx_callbacks=[on_xbee_message_received],
    xbee_tx_callbacks=[],
    xbee_baud_rate=115200,
)


async def example():
    """Example script to test basic operations."""
    await gopher_instance.open_xbee_async()

    try:
        print("Started Gopher")

        print(
            'Type "send broadcast" to send a message with ack (0x10, 0x8B '
            "response)\n"
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
                    destination=TEST_DESTINATION_ADDRESS,
                    data="Hello world with ack",
                    ack=True,
                )
                print("\tSent message with ack")

                if status.transmit_status == TransmitStatus.SUCCESS:
                    print("\t\tSuccessful ack received")
                else:
                    print("\t\tFailed ack")

            elif example_trigger == "send":
                gopher_instance.send_xbee_message(
                    destination=TEST_DESTINATION_ADDRESS,
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
    asyncio.run(example())
