import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QWidget,
)

from gopher import Gopher, BackendWorker, GopherThread
from widgets.line_graph import LineGraphWidget
from widgets.orientation import OrientationWidget


class MainWindow(QMainWindow):
    def __init__(self, gopher_instance: Gopher):
        super().__init__()
        self.setWindowTitle("Multi-Sensor App")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.orientation_button = QPushButton("Open Orientation Widget")
        self.temperature_graph_button = QPushButton(
            "Open Temperature Graph Widget"
        )
        self.layout.addWidget(self.orientation_button)
        self.layout.addWidget(self.temperature_graph_button)

        self.gopher = gopher_instance
        self.backend_worker = BackendWorker(self.gopher)
        self.backend_thread = GopherThread(self.backend_worker)
        self.backend_worker.moveToThread(self.backend_thread)

        self.orientation_widget = None
        self.graph_widget = None

        # Connect buttons
        self.orientation_button.clicked.connect(
            self.open_orientation_visualizer
        )
        self.temperature_graph_button.clicked.connect(
            self.open_temperature_graph
        )

        # Connect backend signals
        self.backend_worker.sensor_data_signal.connect(self.handle_sensor_data)

        # Start backend thread
        self.backend_thread.start()

    def handle_sensor_data(self, sensor_data):
        """Process incoming sensor data."""
        if "orientation" in sensor_data and self.orientation_widget:
            self.orientation_widget.update_orientation(
                **sensor_data["orientation"]
            )

        if "temperature" in sensor_data and self.graph_widget:
            self.graph_widget.add_data(sensor_data["temperature"])

    def open_orientation_visualizer(self):
        """Open 3D orientation visualizer."""
        self.orientation_widget = OrientationWidget("3D Orientation")
        self.orientation_widget.show()

    def open_temperature_graph(self):
        """Open temperature graph widget."""
        self.graph_widget = LineGraphWidget(
            "Temperature Over Time", "temperature"
        )
        self.graph_widget.show()

    def closeEvent(self, event):
        """Ensure backend thread stops when the application is closed."""
        self.backend_worker.stop_worker()
        self.backend_thread.quit()
        self.backend_thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialize Gopher and backend
    gopher = Gopher()
    gopher.start(db_url="sqlite:///xbee_log.db", xbee_port="COM3")

    # Initialize the main window
    window = MainWindow(gopher)
    window.show()

    sys.exit(app.exec())
