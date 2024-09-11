"""XBee API interacting functions."""

from digi.xbee.devices import (
    XBeeDevice,
    XBeeMessage,
    RemoteXBeeDevice,
    XBee64BitAddress,
)
from digi.xbee.models.status import TransmitStatus

from xbee_db import log_xbee_transmission, create_table


# TODO: Move to OOP for self DB init and parameter reference.
TEMP_DB_TABLE = create_table("test")


def data_receive_callback(xbee_message):
    """Handle an incoming message.

    Args:
        xbee_message: XBeeMessage object to process.
    """
    log_xbee_transmission(table=TEMP_DB_TABLE, xbee_message=xbee_message)


def transmit_status_callback(status_message):
    """Handle Transmit Status frame."""
    # Extract frame ID
    frame_id = status_message.frame_id

    # Extract delivery status
    delivery_status = status_message.transmit_status

    # Extract delivery options (optional, depending on the frame)
    receive_options = status_message.options

    print(f"Transmit Status for Frame ID {frame_id}: {delivery_status}")
    if delivery_status == TransmitStatus.SUCCESS:
        print("Message delivered successfully.")
    else:
        print(f"Delivery failed with status: {delivery_status}")


def xbee_init(port: str, baud_rate: int = 115200) -> XBeeDevice:
    """Create an XBee API instance.

    Args:
        port: COM port to use. Example: "COM1".
        baud_rate: Baud rate in integer, defaults to 115200.

    Returns:
        Instance of XBeeDevice object.

    Examples:
        >>> example = xbee_init(port="COM1", baud_rate=115200)
    """
    return XBeeDevice(port=port, baud_rate=baud_rate)


def transmit(xbee: XBeeDevice, destination_address: str, data: str):
    """Create an XBee API instance.

    Args:
        xbee: XBeeDevice instance to use.
        destination_address: Hex string of 64-bit destination address.
        data: Data to transmit.

    Examples:
        >>> example = xbee_init(port="COM10", baud_rate=115200)
        >>> transmit(xbee=example, destination_address="123456789ABCDEF0", data="data")
    """
    try:
        # if not xbee.is_open():
        xbee.open()  # Open the device if not done so already.

        # Define the remote destination XBee address.
        target_device = RemoteXBeeDevice(
            xbee, XBee64BitAddress.from_hex_string(destination_address)
        )

        # Send a message to the remote XBee device.
        xbee.send_data(remote_xbee=target_device, data=data)

    finally:
        if xbee is not None and xbee.is_open():
            xbee.close()


def xbee_start(xbee: XBeeDevice):
    """Start XBee device instance with callback configuration.

    Args:
        xbee: XBeeDevice instance to use.
    """
    try:
        # Open the device.
        xbee.open()

        # TODO: Make async/threaded for simultaneous transmissions during open.

        # Set up callback for received messages.
        xbee.add_data_received_callback(data_receive_callback)

        while True:
            pass

    finally:
        if xbee is not None and xbee.is_open():
            xbee.close()
