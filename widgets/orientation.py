import queue

from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.spatial.transform import Rotation


class OrientationWidget(QWidget):
    def __init__(self, title):
        super().__init__()
        self.data_queue = queue.Queue()
        self.timer = self.startTimer(10)  # Update interval in ms.

        # Set up the matplotlib figure and canvas.
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.title = title

        # Set up the layout.
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.ax.set_xlim([-1, 1])
        self.ax.set_ylim([-1, 1])
        self.ax.set_zlim([-1, 1])

    def timerEvent(self, event):
        if not self.data_queue.empty():
            w, x, y, z = self.data_queue.get()

            # Normalize quaternion.
            norm = (w**2 + x**2 + y**2 + z**2) ** 0.5
            w, x, y, z = w / norm, x / norm, y / norm, z / norm

            # Convert quaternion to rotation matrix.
            rotation = Rotation.from_quat([x, y, z, w]).as_matrix()
            origin = [0, 0, 0]
            x_axis = rotation @ [1, 0, 0]
            y_axis = rotation @ [0, 1, 0]
            z_axis = rotation @ [0, 0, 1]

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
            self.ax.set_title(self.title)

            self.canvas.draw()

    def update_orientation(self, w, x, y, z):
        """Add quaternion orientation to data queue callback."""
        self.data_queue.put((w, x, y, z))
