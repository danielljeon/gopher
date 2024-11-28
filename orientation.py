import queue
import sys
import threading

import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.spatial.transform import Rotation

from gopher import *
from nerve import extract_value


def quaternion_queue_callback(
    w: float, x: float, y: float, z: float, data_queue: queue.Queue
):
    """Add quaterion orientation to data queue callback.

    Args:
        w: Real component of quaterion.
        x: i component of quaterion.
        y: j component of quaterion.
        z: k component of quaterion.
        data_queue: Pointer for queue to add to.
    """
    data_queue.put((w, x, y, z))


class QuaternionVisualizer(QMainWindow):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.timer = self.startTimer(50)  # Timer interval in ms.

        # Set up the matplotlib figure and canvas.
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Create a 3D subplot.
        self.ax = self.figure.add_subplot(111, projection="3d")

        # Call remaining configuration logic method.
        self.init()

    def init(self):
        self.setWindowTitle("Quaternion Visualizer")
        self.setGeometry(100, 100, 800, 600)

        # Set up the central widget.
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Set up the layout for matplotlib figure and canvas.
        layout.addWidget(self.canvas)

        # Configure the 3D subplot.
        self.ax.set_xlim([-1, 1])
        self.ax.set_ylim([-1, 1])
        self.ax.set_zlim([-1, 1])
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_zlabel("Z")
        self.ax.tick_params(
            labelbottom=False, labelleft=False, labelright=False, labeltop=False
        )

    def timerEvent(self, event):
        if not self.data_queue.empty():
            # Get the latest quaternion from the queue.
            w, x, y, z = self.data_queue.get()

            # Normalize the quaternion.
            norm = np.sqrt(w**2 + x**2 + y**2 + z**2)
            w, x, y, z = w / norm, x / norm, y / norm, z / norm

            # Convert quaternion to rotation matrix.
            rotation = Rotation.from_quat([x, y, z, w]).as_matrix()

            # Define the axes of the rotated frame.
            origin = np.array([0, 0, 0])
            x_axis = rotation @ np.array([1, 0, 0])
            y_axis = rotation @ np.array([0, 1, 0])
            z_axis = rotation @ np.array([0, 0, 1])

            # Update the plot.
            self.ax.clear()
            self.ax.quiver(
                *origin,
                *x_axis,
                color="r",
                length=1.0,
                normalize=True,
                label="X-axis",
            )
            self.ax.quiver(
                *origin,
                *y_axis,
                color="g",
                length=1.0,
                normalize=True,
                label="Y-axis",
            )
            self.ax.quiver(
                *origin,
                *z_axis,
                color="b",
                length=1.0,
                normalize=True,
                label="Z-axis",
            )
            self.ax.set_xlim([-1, 1])
            self.ax.set_ylim([-1, 1])
            self.ax.set_zlim([-1, 1])
            self.ax.set_xlabel("X")
            self.ax.set_ylabel("Y")
            self.ax.set_zlabel("Z")
            self.ax.tick_params(
                labelbottom=False,
                labelleft=False,
                labelright=False,
                labeltop=False,
            )
            self.ax.text2D(
                0.05,
                0.95,
                f"Quaternion:\nW={w:.2f}\nX={x:.2f}\nY={y:.2f}\nZ={z:.2f}",
                transform=self.ax.transAxes,
                fontsize=10,
                color="black",
            )

            self.canvas.draw()


def main():
    app = QApplication(sys.argv)
    data_queue = queue.Queue()

    # Create and show the visualizer.
    visualizer = QuaternionVisualizer(data_queue)
    visualizer.show()
    sys.exit(app.exec())


def simulated_main():
    def __simulated_callback(data_queue: queue.Queue):
        import time

        while True:
            # Simulate incoming quaternion data (real, i, j, k)
            w = np.random.random()
            x = np.random.random()
            y = np.random.random()
            z = np.random.random()
            quaternion_queue_callback(w, x, y, z, data_queue)
            time.sleep(0.1)

    app = QApplication(sys.argv)
    data_queue = queue.Queue()

    # Start the hardware callback thread
    callback_thread = threading.Thread(
        target=__simulated_callback, args=(data_queue,), daemon=True
    )
    callback_thread.start()

    # Create and show the visualizer.
    visualizer = QuaternionVisualizer(data_queue)
    visualizer.show()
    sys.exit(app.exec())


################################################################################

# Create Gopher instance and start operation.
gopher_instance = Gopher()
startup_status = False


def on_xbee_message_received(xbee_message: XBeeMessage, data_queue):
    message = xbee_message.data.decode()

    print(
        f"Message received from {xbee_message.remote_device.get_64bit_addr()}: "
        f"{message}"
    )

    if ",k=" in message:
        w = extract_value(message, "w")
        x = extract_value(message, "i")
        y = extract_value(message, "j")
        z = extract_value(message, "k")
        if w is not None and x is not None and y is not None and z is not None:
            w = eval(w)
            x = eval(x)
            y = eval(y)
            z = eval(z)
            quaternion_queue_callback(w, x, y, z, data_queue=data_queue)


async def xbee_test():
    # Initialize Gopher instance and open the XBee device
    await gopher_instance.open_xbee_async()

    # Create the application and data queue
    app = QApplication(sys.argv)
    data_queue = queue.Queue()

    # Add RX callback for handling incoming messages
    gopher_instance.xbee.add_data_received_callback(
        lambda xbee_message: on_xbee_message_received(xbee_message, data_queue)
    )

    # Create and show the visualizer
    visualizer = QuaternionVisualizer(data_queue)
    visualizer.show()
    sys.exit(app.exec())


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
                xbee_rx_callbacks=[
                    (
                        on_xbee_message_received,
                        [],
                        {"data_queue": queue.Queue()},
                    )
                ],
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


################################################################################

if __name__ == "__main__":
    # main()

    asyncio.run(establish_com_port())
    if startup_status:
        asyncio.run(xbee_test())
