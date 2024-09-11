"""XBee API datalink logging DB via SQLAlchemy module."""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Table,
    MetaData,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from digi.xbee.devices import XBeeMessage

# Create SQLite database engine.
engine = create_engine("sqlite:///xbee.db", echo=True)
Base = declarative_base()
metadata = MetaData()


class XBeeTransmissionTable(Base):
    """XBee API transmission logging SQLAlchemy table.

    Columns:
        id: Primary key, auto-increment ID.
        sender_64_hardware: Sending remote device's 64-bit (hardware) address.
        sender_16_network: Sending remote device's 16-bit (network) address.
        rssi: Signal strength.
        is_broadcast: Boolean condition for direct or broadcast.
        data: Encoded data payload.
        timestamp: Timestamp (time.time()) of receipt.
    """

    __tablename__ = "xbee_transmissions"

    id = Column(Integer, autoincrement=True, primary_key=True)
    sender_64_hardware = Column(String)
    sender_16_network = Column(String)
    rssi = Column(Integer)
    is_broadcast = Column(Boolean)
    data = Column(String)
    timestamp = Column(Float)

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


def create_table(table_name: str) -> Table:
    """Dynamically create a new table.

    Args:
        table_name: Table name to put into the database.

    Returns:
        Instance of newly created sqlalchemy.sql.schema.Table object.

    Examples:
        >>> new_table_example = create_table("example_table_name")

    Notes:
        If an existing table with the same name alreay exists, the function will
        return an instance of the existing table.
    """
    table = Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("sender_64_hardware", String),
        Column("sender_16_network", String),
        Column("rssi", Integer),
        Column("is_broadcast", Boolean),
        Column("data", String),
        Column("timestamp", Float),
    )
    metadata.create_all(engine)
    return table


def new_transmission_record(
    table: XBeeTransmissionTable,
    sender_64_hardware: str,
    sender_16_network: str,
    rssi: int,
    is_broadcast: bool,
    data: str,
    timestamp: float,
):
    """Add new transmission record to a XBeeTransmissionTable.

    Args:
        table: Instance of XBeeTransmissionTable object.
        sender_64_hardware: Sending remote device's 64-bit (hardware) address.
        sender_16_network: Sending remote device's 16-bit (network) address.
        rssi: Signal strength.
        is_broadcast: Boolean condition for direct or broadcast.
        data: Encoded data payload.
        timestamp: Timestamp (time.time()) of receipt.

    Examples:
        >>> t = create_table("example_table_name")
        >>> import time
        >>> new_transmission_record(t, "sender_address", 50, True, "payload_data", time.time())
    """
    session = sessionmaker(bind=engine)()

    # Insert the record using the table object
    insert_stmt = table.insert().values(
        sender_64_hardware=sender_64_hardware,
        sender_16_network=sender_16_network,
        rssi=rssi,
        is_broadcast=is_broadcast,
        data=data,
        timestamp=timestamp,
    )
    session.execute(insert_stmt)
    session.commit()


def log_xbee_transmission(
    table: callable(XBeeTransmissionTable), xbee_message: XBeeMessage
):
    """Log transmission to the specified table class.

    Args:
        table: Instance of XBeeTransmissionTable object.
        xbee_message: XBeeMessage object.
    """
    new_transmission_record(
        table=table,
        sender_64_hardware=str(xbee_message.remote_device.get_64bit_addr()),
        sender_16_network=str(xbee_message.remote_device.get_16bit_addr()),
        rssi=int(xbee_message.remote_device.get_parameter("DB")[0]),
        is_broadcast=xbee_message.is_broadcast,
        data=xbee_message.data.decode(),
        timestamp=xbee_message.timestamp,
    )


def print_all_transmissions(table_class):
    """Read transmissions from the specified table class."""
    session = sessionmaker(bind=engine)()

    # Query table.
    transmissions = session.query(table_class).all()

    # Print.
    for t in transmissions:
        print(t)
