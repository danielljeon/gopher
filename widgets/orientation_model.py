import numpy as np
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtGui import QVector3D, QColor, QQuaternion
from PySide6.QtWidgets import QVBoxLayout, QWidget
from scipy.spatial.transform import Rotation

from gopher import MaxSizeQueue


class OrientationModelWidget(QWidget):
    def __init__(self, title, model_file_path):
        super().__init__()
        self.reference_quaternion = None  # Store the reference quaternion.

        self.data_queue = MaxSizeQueue(maxsize=50)
        self.timer = self.startTimer(1)  # Update interval in ms

        self.title = title
        self.model_file_path = model_file_path

        # Set up the 3D view
        self.view = Qt3DExtras.Qt3DWindow()
        self.view.defaultFrameGraph().setClearColor(
            QColor(50, 50, 50)
        )  # Dark gray background
        self.container = self.createWindowContainer(self.view)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.container)

        # # Quaternion display label  # TODO
        # self.quaternion_label = QLabel("Quaternion: N/A")
        # self.layout.addWidget(self.quaternion_label)
        #
        # # Camera orientation display label
        # self.camera_label = QLabel("Camera: N/A")
        # self.layout.addWidget(self.camera_label)

        # Scene setup
        self.root_entity = Qt3DCore.QEntity()

        # Model setup
        self.model_entity = Qt3DCore.QEntity(self.root_entity)
        # self.mesh = self.load_model()  # Load in the model # TODO
        self.mesh = Qt3DExtras.QCuboidMesh()
        self.model_entity.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial(self.model_entity)
        self.material.setAmbient(QColor(200, 200, 200))  # Soft gray ambient.
        self.material.setDiffuse(QColor(255, 255, 255))  # Diffuse light.
        self.material.setSpecular(QColor(255, 255, 255))  # Specular highlights.
        self.model_entity.addComponent(self.material)

        self.transform = Qt3DCore.QTransform()
        self.model_entity.addComponent(self.transform)

        # Add lighting.
        ambient_light = Qt3DCore.QEntity(self.root_entity)
        ambient_light_component = Qt3DRender.QEnvironmentLight()
        ambient_light.addComponent(ambient_light_component)

        # Camera setup
        self.camera = self.view.camera()
        self.camera.lens().setPerspectiveProjection(45.0, 16 / 10, 0.1, 1000.0)
        self.camera.setPosition(QVector3D(0, 5, 5))
        self.camera.setViewCenter(QVector3D(0, 0, 0))

        # Camera controller for orbiting
        self.cam_controller = Qt3DExtras.QOrbitCameraController(
            self.root_entity
        )
        # self.cam_controller.setLinearSpeed(50.0)  # Speed of movement.
        # self.cam_controller.setLookSpeed(180.0)  # Speed of rotation.
        self.cam_controller.setCamera(self.camera)

        # Set root entity
        self.view.setRootEntity(self.root_entity)

        self.add_axes()

    def add_axes(self):
        # X-axis (Red)
        x_axis_entity = Qt3DCore.QEntity(self.root_entity)
        x_axis_mesh = Qt3DExtras.QCylinderMesh()
        x_axis_mesh.setRadius(0.5)  # Thin cylinder
        x_axis_mesh.setLength(100.0)  # Length of the axis
        x_axis_material = Qt3DExtras.QPhongMaterial()
        x_axis_material.setDiffuse(QColor(255, 0, 0))  # Red
        x_axis_transform = Qt3DCore.QTransform()
        x_axis_transform.setRotation(
            QQuaternion.fromAxisAndAngle(QVector3D(0, 0, 1), 90)
        )  # Align with X-axis
        x_axis_transform.setTranslation(
            QVector3D(1.0, 0, 0)
        )  # Offset along the X-axis
        x_axis_entity.addComponent(x_axis_mesh)
        x_axis_entity.addComponent(x_axis_material)
        x_axis_entity.addComponent(x_axis_transform)

        # Y-axis (Green)
        y_axis_entity = Qt3DCore.QEntity(self.root_entity)
        y_axis_mesh = Qt3DExtras.QCylinderMesh()
        y_axis_mesh.setRadius(0.02)
        y_axis_mesh.setLength(2.0)
        y_axis_material = Qt3DExtras.QPhongMaterial()
        y_axis_material.setDiffuse(QColor(0, 255, 0))  # Green
        y_axis_transform = Qt3DCore.QTransform()
        y_axis_transform.setTranslation(
            QVector3D(0, 1.0, 0)
        )  # Offset along the Y-axis
        y_axis_entity.addComponent(y_axis_mesh)
        y_axis_entity.addComponent(y_axis_material)
        y_axis_entity.addComponent(y_axis_transform)

        # Z-axis (Blue)
        z_axis_entity = Qt3DCore.QEntity(self.root_entity)
        z_axis_mesh = Qt3DExtras.QCylinderMesh()
        z_axis_mesh.setRadius(0.02)
        z_axis_mesh.setLength(2.0)
        z_axis_material = Qt3DExtras.QPhongMaterial()
        z_axis_material.setDiffuse(QColor(0, 0, 255))  # Blue
        z_axis_transform = Qt3DCore.QTransform()
        z_axis_transform.setRotation(
            QQuaternion.fromAxisAndAngle(QVector3D(1, 0, 0), 90)
        )  # Align with Z-axis
        z_axis_transform.setTranslation(
            QVector3D(0, 0, 1.0)
        )  # Offset along the Z-axis
        z_axis_entity.addComponent(z_axis_mesh)
        z_axis_entity.addComponent(z_axis_material)
        z_axis_entity.addComponent(z_axis_transform)

    def timerEvent(self, event):
        if not self.data_queue.empty():
            w, x, y, z = self.data_queue.get()

            # Normalize quaternion
            norm = (w**2 + x**2 + y**2 + z**2) ** 0.5
            if norm == 0:
                print("Invalid quaternion, skipping update.")
                return
            w, x, y, z = w / norm, x / norm, y / norm, z / norm

            # Set reference quaternion if not already set
            if self.reference_quaternion is None:
                self.reference_quaternion = [w, x, y, z]
                print(f"Reference quaternion set: {self.reference_quaternion}")
                return

            # Calculate relative quaternion
            reference = Rotation.from_quat(self.reference_quaternion)
            current = Rotation.from_quat([x, y, z, w])
            relative_rotation = current * reference.inv()

            # Update the transformation
            try:
                rotation_matrix = relative_rotation.as_matrix()
                self.update_transform(rotation_matrix)
            except Exception as e:
                print(f"Error in timerEvent: {e}")

    def update_orientation(self, w, x, y, z):
        """Add quaternion orientation to data queue callback."""
        self.data_queue.put((w, x, y, z))

    def load_model(self):
        """Load an OBJ or STL model."""
        mesh = Qt3DRender.QMesh()
        try:
            print(f"Attempting to load model: {self.model_file_path}")
            mesh.setSource(self.model_file_path)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
        return mesh

    def update_transform(self, rotation):
        try:
            # Convert rotation matrix to a quaternion
            quaternion = Rotation.from_matrix(
                rotation
            ).as_quat()  # [x, y, z, w]
            q = QVector3D(quaternion[0], quaternion[1], quaternion[2])
            angle = 2 * np.arccos(quaternion[3])  # Convert w component to angle

            # Apply the quaternion rotation directly
            self.transform.setRotation(
                QQuaternion.fromAxisAndAngle(q, np.degrees(angle))
            )

            print(
                f"Applied rotation (Quaternion): Axis={q}, Angle={np.degrees(angle)}"
            )
        except Exception as e:
            print(f"Error in update_transform: {e}")
