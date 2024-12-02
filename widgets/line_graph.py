import time

import matplotlib.ticker as mticker
from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from gopher import MaxSizeQueue


class LineGraphWidget(QWidget):
    def __init__(self, title, data_key):
        super().__init__()
        self.data_key = data_key
        self.data_queue = MaxSizeQueue(maxsize=50)
        self.data_points = []  # Stores tuples: (timestamp, value).

        # Set up the matplotlib figure and canvas.
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.title = title

        # Set up the layout.
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        self.timer = self.startTimer(10)  # Update interval in ms.

    def timerEvent(self, event):
        """Fetch data from the queue and update the graph."""
        current_time = time.time()

        # Add data from the queue to the data points.
        while not self.data_queue.empty():
            value = self.data_queue.get()
            self.data_points.append((current_time, value))

        # Filter data points to keep only the last 30 seconds.
        self.data_points = [
            (t, v) for t, v in self.data_points if t >= current_time - 30
        ]

        # Prepare data for plotting.
        if self.data_points:
            x_data = [t - self.data_points[0][0] for t, v in self.data_points]
            y_data = [v for t, v in self.data_points]

            # Update the graph.
            self.ax.clear()
            self.ax.plot(x_data, y_data, label=self.data_key)
            self.ax.set_title(self.title)
            self.ax.legend(loc="upper right")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Value")

            # Auto-scale both axes.
            self.ax.relim()  # Recalculate limits based on data.
            self.ax.autoscale(enable=True, axis="both")  # Auto-scale both axes.

            # Control tick frequency for the X-axis.
            self.ax.xaxis.set_major_locator(
                mticker.MaxNLocator(nbins=10)
            )  # Max 10 ticks on X-axis.
            self.ax.yaxis.set_major_locator(
                mticker.MaxNLocator(nbins=5)
            )  # Max 5 ticks on Y-axis.

            self.canvas.draw()

    def add_data(self, value):
        """Add new data to the queue."""
        self.data_queue.put(value)
