import asyncio

from digi.xbee.devices import (
    RemoteXBeeDevice,
    TransmitOptions,
    XBeeDevice,
    XBeeMessage,
    XBee64BitAddress,
)
from digi.xbee.packets.common import TransmitStatusPacket
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base()


class XBeeTransmissionTable(Base):
    """XBee API transmission logging SQLAlchemy table."""

    __tablename__ = "xbee_transmissions"

    id = Column(Integer, autoincrement=True, primary_key=True)
    sender_64_hardware = Column(String)
    sender_16_network = Column(String)
    rssi = Column(Integer)
    is_broadcast = Column(Boolean)
    data = Column(String)
    timestamp = Column(Float)
    # TODO: Revisit this for more data log like ACK status.

    def __str__(self):
        return (
            f"id={self.id}\n"
            f"sender_64_hardware={self.sender_64_hardware}\n"
            f"sender_16_network={self.sender_16_network}\n"
            f"rssi={self.rssi}\n"
            f"is_broadcast={self.is_broadcast}\n"
            f"data={self.data}\n"
            f"timestamp={self.timestamp}"
        )


class Gopher:
    def __init__(self):
        self.__db_engine = None
        self.__db_session = None
        self.__xbee = None
        self.__xbee_callbacks = None

    def start(
        self,
        db_url: str,
        xbee_port: str,
        xbee_callbacks: list[callable],
        xbee_baud_rate: int = 115200,
    ):
        """Start up a new Gopher instance.

        Args:
            db_url: SQLAlchemy database URL to use.
            xbee_port: Port to open XBee instance through, example: 'COM1'.
            xbee_callbacks: List of function(XBeeMessage) for Rx callback.
            xbee_baud_rate: Baud rate to open XBee instance, defaults to 115200.
        """
        # Initialize objects.
        self.__xbee = XBeeDevice(port=xbee_port, baud_rate=xbee_baud_rate)
        self.__xbee_callbacks = xbee_callbacks
        self.__db_engine = create_engine(db_url)
        self.__db_session = scoped_session(sessionmaker(bind=self.__db_engine))

        Base.metadata.create_all(self.__db_engine)  # Create all tables.

    def get_db_session(self):
        """Open DB session instance."""
        return self.__db_session()

    def remove_db_session(self):
        """Remove DB session instance."""
        self.__db_session.remove()

    async def open_xbee_async(self):
        """Open XBee instance."""
        try:
            await asyncio.get_running_loop().run_in_executor(
                None, self.__xbee.open
            )

            # TODO: Add something related to ACK response (0x8B) handling.

            for callback in self.__xbee_callbacks:
                # Add callbacks.
                self.__xbee.add_data_received_callback(callback)

        except Exception as e:
            raise RuntimeError(f"Failed to open XBee async: {e}")

    async def close_xbee_async(self):
        """Close XBee instance."""
        try:
            await asyncio.get_running_loop().run_in_executor(
                None, self.__xbee.close
            )
        except Exception as e:
            raise RuntimeError(f"Failed to close XBee async: {e}")

    async def shutdown(self):
        """Shutdown Gopher internal XBee and DB instance."""
        await self.close_xbee_async()
        self.remove_db_session()

    def __write_xbee_transmission_to_db(
        self,
        sender_64_hardware: str,
        sender_16_network: str,
        rssi: int,
        is_broadcast: bool,
        data: str,
        timestamp: float,
    ):
        session = self.get_db_session()
        try:
            new_entry = XBeeTransmissionTable(
                sender_64_hardware=sender_64_hardware,
                sender_16_network=sender_16_network,
                rssi=rssi,
                is_broadcast=is_broadcast,
                data=data,
                timestamp=timestamp,
            )
            session.add(new_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def log_xbee_message(self, xbee_message: XBeeMessage):
        """Log transmission to the specified table class.

        Args:
            xbee_message: XBeeMessage object.
        """
        # TODO: Revisit this for more data log like ACK status. See table class.
        self.__write_xbee_transmission_to_db(
            sender_64_hardware=str(xbee_message.remote_device.get_64bit_addr()),
            sender_16_network=str(xbee_message.remote_device.get_16bit_addr()),
            rssi=int(xbee_message.remote_device.get_parameter("DB")[0]),
            is_broadcast=xbee_message.is_broadcast,
            data=xbee_message.data.decode(),
            timestamp=xbee_message.timestamp,
        )

    def send_xbee_message(
        self, destination: str, data: str, ack: bool = False
    ) -> TransmitStatusPacket:
        """Send an XBee API framed message.

        Args:
            destination: 64-bit hex destination address, defaults to broadcast.
            data: Data to transmit.
            ack: Set if acknowledgement is required, defaults to False.

        Returns:
            Return TransmitStatusPacket for processes like ACK processing.

        Notes:
            If ack=True, switches to use of Transmit Request (0x10), which
            expects a Transmit Status (0x8B) to be sent from the receiver to the
            sender (this class instance). Note that in the python digi-xbee
            library, ACK (0x8B) messages are handled in hardware, and will not
            be processable via the callback functions. Hence, the return here.
        """
        try:
            remote_device = RemoteXBeeDevice(
                self.__xbee, XBee64BitAddress.from_hex_string(destination)
            )

            # Ensure data is properly encoded before transmission.
            data_bytes = data.encode("utf-8")

            # Send data to the remote device with or without acknowledgment.
            if ack:
                status = self.__xbee.send_data(
                    remote_device,
                    data_bytes,
                    # Sends ack transmit status requirement by default.
                )
            else:
                status = self.__xbee.send_data(
                    remote_device,
                    data_bytes,
                    transmit_options=TransmitOptions.DISABLE_ACK.value,
                )

            return status

        except Exception as e:
            print(f"Error during transmission: {e}")
