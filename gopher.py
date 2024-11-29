"""Gopher application backend with PySide Integration."""

from queue import Queue

from PySide6.QtCore import QObject, QThread, Signal
from digi.xbee.devices import XBeeDevice, XBeeMessage
from digi.xbee.serial import FlowControl
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from nerve import extract_value

Base = declarative_base()


class Gopher:
    """Gopher backend class for XBee and database interactions."""

    def __init__(self):
        self.xbee = None
        self.__db_engine = None
        self.__db_session = None

    def start(self, db_url: str, xbee_port: str, xbee_baud_rate: int = 115200):
        """Initialize and start the XBee and database."""
        self.__db_engine = create_engine(db_url)
        self.__db_session = scoped_session(sessionmaker(bind=self.__db_engine))
        Base.metadata.create_all(self.__db_engine)

        self.xbee = XBeeDevice(
            port=xbee_port,
            baud_rate=xbee_baud_rate,
            flow_control=FlowControl.HARDWARE_RTS_CTS,
        )
        self.xbee.open()

    def stop(self):
        """Stop the Gopher backend."""
        if self.xbee and self.xbee.is_open():
            self.xbee.close()
        self.__db_session.remove()


class BackendWorker(QObject):
    """Backend worker to process XBee messages in a separate thread."""

    sensor_data_signal = Signal(dict)  # Emit all sensor data as a dictionary.

    def __init__(self, gopher: Gopher):
        super().__init__()
        self.gopher = gopher
        self.running = True
        self.data_queues = {
            "temperature": Queue(),
            "pressure": Queue(),
            "orientation": Queue(),
        }

    def start_worker(self):
        """Set up XBee callbacks."""
        self.gopher.xbee.add_data_received_callback(self.handle_xbee_message)

    def handle_xbee_message(self, xbee_message: XBeeMessage):
        """Process incoming XBee message and update queues."""
        try:
            data = xbee_message.data.decode()
            sensor_data = {}

            if ",k=" in data:
                w = extract_value(data, "w")
                x = extract_value(data, "i")
                y = extract_value(data, "j")
                z = extract_value(data, "k")
                if all(v is not None for v in [w, x, y, z]):
                    orientation = {
                        "w": float(w),
                        "x": float(x),
                        "y": float(y),
                        "z": float(z),
                    }
                    self.data_queues["orientation"].put(orientation)
                    sensor_data["orientation"] = orientation

            if ",baro=" in data:
                temperature = extract_value(data, "temp")
                pressure = extract_value(data, "baro")
                self.data_queues["temperature"].put(temperature)
                self.data_queues["pressure"].put(pressure)
                sensor_data["temperature"] = temperature
                sensor_data["pressure"] = pressure

            if sensor_data:
                self.sensor_data_signal.emit(sensor_data)
        except Exception as e:
            print(f"Error processing XBee message: {e}")

    def stop_worker(self):
        """Stop the backend worker."""
        self.running = False
        self.gopher.stop()


class GopherThread(QThread):
    """Thread to run the Gopher backend."""

    def __init__(self, backend_worker: BackendWorker):
        super().__init__()
        self.backend_worker = backend_worker

    def run(self):
        """Run the backend worker."""
        self.backend_worker.start_worker()
