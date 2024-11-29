"""Orientation related GUI and callbacks."""

import queue
import sys

import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from digi.xbee.devices import XBeeMessage
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.spatial.transform import Rotation

from gopher import Gopher
from nerve import extract_value


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
                0,
                0.8,
                f"Quaternion:\nW={w:.3f}\nX={x:.3f}\nY={y:.3f}\nZ={z:.3f}",
                transform=self.ax.transAxes,
                fontsize=12,
                color="black",
            )

            self.canvas.draw()

    def quaternion_queue_callback(self, w: float, x: float, y: float, z: float):
        """Add quaterion orientation to data queue callback.

        Args:
            w: Real component of quaterion.
            x: i component of quaterion.
            y: j component of quaterion.
            z: k component of quaterion.
        """
        self.data_queue.put((w, x, y, z))


def orientation_rx_callback(
    xbee_message: XBeeMessage, quaterion_visualizer: QuaternionVisualizer
):
    message = xbee_message.data.decode()
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
            quaterion_visualizer.quaternion_queue_callback(w, x, y, z)


async def run_orientation_gui(gopher_instance: Gopher):
    # Initialize Gopher instance and open the XBee device
    await gopher_instance.open_xbee_async()

    # Create the application and data queue.
    app = QApplication(sys.argv)
    data_queue = queue.Queue()

    # Create the visualizer.
    visualizer = QuaternionVisualizer(data_queue)

    # Add RX callback for handling incoming messages.
    gopher_instance.xbee.add_data_received_callback(
        lambda xbee_message: orientation_rx_callback(xbee_message, visualizer)
    )

    # Start visualizer.
    visualizer.show()
    sys.exit(app.exec())
