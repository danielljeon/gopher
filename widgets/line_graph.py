import queue
import time

from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class LineGraphWidget(QWidget):
    def __init__(self, title, data_key):
        super().__init__()
        self.data_key = data_key
        self.data_queue = queue.Queue()
        self.data_points = []  # Stores tuples: (timestamp, value)

        # Set up the matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Value")

        # Set up the layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        self.timer = self.startTimer(100)  # Update interval in ms

    def timerEvent(self, event):
        """Fetch data from the queue and update the graph."""
        current_time = time.time()

        # Add data from the queue to the data points
        while not self.data_queue.empty():
            value = self.data_queue.get()
            self.data_points.append((current_time, value))

        # Filter data points to keep only the last 30 seconds
        self.data_points = [
            (t, v) for t, v in self.data_points if t >= current_time - 30
        ]

        # Prepare data for plotting
        if self.data_points:
            x_data = [
                t - self.data_points[0][0] for t, v in self.data_points
            ]  # Relative time
            y_data = [v for t, v in self.data_points]

            # Update the graph
            self.ax.clear()
            self.ax.plot(x_data, y_data, label=self.data_key)
            self.ax.legend(loc="upper right")
            self.ax.set_xlabel(f"Time (Last {len(x_data)} Seconds)")
            self.ax.set_ylabel("Value")
            # self.ax.set_xlim(
            #     0, min(30, x_data[-1] if x_data else 30)
            # )  # Limit to 30s
            self.canvas.draw()

    def add_data(self, value):
        """Add new data to the queue."""
        self.data_queue.put(value)
