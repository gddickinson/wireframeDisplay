import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QPushButton,
                             QSlider, QLabel, QMessageBox, QGroupBox, QCheckBox, QColorDialog, QAction,
                             QFileDialog, QSpinBox, QListWidget, QSplitter, QDialog, QFormLayout, QMenu, QDoubleSpinBox,
                             QDialogButtonBox, QInputDialog, QLineEdit)

from PyQt5.QtCore import Qt, QTimer, QTime, QPointF
from PyQt5.QtGui import QVector3D, QMatrix4x4, QColor
from PyQt5.QtGui import QColor
import pyqtgraph.opengl as gl
import numpy as np
from wireframe import Wireframe
from shape_loader_dialog import ShapeLoaderDialog

import numpy as np


class SceneObject:
    def __init__(self, wireframe, position=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
        self.wireframe = wireframe
        self.position = np.array(position, dtype=float)
        self.rotation = np.array(rotation, dtype=float)
        self.scale = np.array(scale, dtype=float)
        self.velocity = np.zeros(3)
        self.angular_velocity = np.zeros(3)
        self.mesh_item = None
        self.edge_item = None
        self.vertex_item = None
        self.center = self.calculate_center()
        self.original_color = (0.7, 0.7, 0.7, 1.0)  # Light gray
        self.hover_color = (1.0, 0.0, 0.0, 1.0)  # Bright red
        self.current_color = self.original_color
        # New properties
        self.name = "Unnamed Object"
        self.mass = 1.0
        self.rotation_speed = np.zeros(3)  # x, y, z rotation speeds
        self.is_animated = False

        print(f"SceneObject initialized with color: {self.current_color}")

    def set_name(self, name):
        self.name = name

    def set_mass(self, mass):
        self.mass = max(0.1, mass)  # Ensure mass is positive

    def set_rotation_speed(self, x, y, z):
        self.rotation_speed = np.array([x, y, z])

    def set_scale(self, x, y, z):
        self.scale = np.array([x, y, z])
        self.update_mesh(None)  # Update mesh to reflect new scale

    def toggle_animation(self):
        self.is_animated = not self.is_animated

    def update_animation(self, dt):
        if self.is_animated:
            self.rotation += self.rotation_speed * dt
            self.update_mesh(None)

    def set_hover_color(self):
        #print(f"Setting hover color: {self.hover_color}")
        self.current_color = self.hover_color
        self.update_color()

    def reset_color(self):
        #print(f"Resetting to original color: {self.original_color}")
        self.current_color = self.original_color
        self.update_color()

    def update_color(self):
        if self.mesh_item:
            #print(f"Updating mesh item color to: {self.current_color}")
            self.mesh_item.setColor(self.current_color)
            # Force update of the mesh data to trigger a redraw
            if hasattr(self.mesh_item, 'meshData'):
                vertices = self.mesh_item.meshData.vertexes()
                faces = self.mesh_item.meshData.faces()
                self.mesh_item.setMeshData(vertexes=vertices, faces=faces, color=self.current_color)
            else:
                print("Mesh item does not have meshData attribute")
        else:
            print("Mesh item is None, color not updated")

    def update_mesh(self, display_options):
        transformed_vertices = self.get_transformed_vertices()

        if self.mesh_item is None:
            #print("Creating new mesh item")
            self.mesh_item = gl.GLMeshItem(vertexes=transformed_vertices, faces=self.wireframe.triangles(),
                                           smooth=True, drawEdges=True, edgeColor=(0, 0, 0, 1))
            self.mesh_item.setColor(self.current_color)
        else:
            #print("Updating existing mesh item")
            self.mesh_item.setMeshData(vertexes=transformed_vertices, faces=self.wireframe.triangles(), color=self.current_color)

        if display_options is not None:  # None: keep the current visibility (animation / properties updates)
            self.mesh_item.setVisible(display_options.show_faces.isChecked())
        #print(f"Mesh visibility set to: {display_options.show_faces.isChecked()}")

    def get_center(self):
        return np.array(self.center) + np.array(self.position)

    def calculate_center(self):
        return np.mean(self.wireframe.vertices, axis=0)

    def get_transformed_vertices(self):
        # Apply scale
        scaled_vertices = (self.wireframe.vertices - self.center) * self.scale + self.center

        # Apply rotation
        rotation_x = np.array([[1, 0, 0],
                               [0, np.cos(self.rotation[0]), -np.sin(self.rotation[0])],
                               [0, np.sin(self.rotation[0]), np.cos(self.rotation[0])]])
        rotation_y = np.array([[np.cos(self.rotation[1]), 0, np.sin(self.rotation[1])],
                               [0, 1, 0],
                               [-np.sin(self.rotation[1]), 0, np.cos(self.rotation[1])]])
        rotation_z = np.array([[np.cos(self.rotation[2]), -np.sin(self.rotation[2]), 0],
                               [np.sin(self.rotation[2]), np.cos(self.rotation[2]), 0],
                               [0, 0, 1]])
        rotation_matrix = np.dot(rotation_z, np.dot(rotation_y, rotation_x))
        rotated_vertices = np.dot(scaled_vertices - self.center, rotation_matrix.T) + self.center

        # Apply translation
        return rotated_vertices + self.position

    def update_center(self):
        self.center = self.calculate_center()


    def apply_transformation(self):
        if self.mesh_item:
            # Apply scale
            scaled_vertices = (self.wireframe.vertices - self.center) * self.scale + self.center

            # Apply rotation
            rotation_x = np.array([[1, 0, 0],
                                   [0, np.cos(self.rotation[0]), -np.sin(self.rotation[0])],
                                   [0, np.sin(self.rotation[0]), np.cos(self.rotation[0])]])
            rotation_y = np.array([[np.cos(self.rotation[1]), 0, np.sin(self.rotation[1])],
                                   [0, 1, 0],
                                   [-np.sin(self.rotation[1]), 0, np.cos(self.rotation[1])]])
            rotation_z = np.array([[np.cos(self.rotation[2]), -np.sin(self.rotation[2]), 0],
                                   [np.sin(self.rotation[2]), np.cos(self.rotation[2]), 0],
                                   [0, 0, 1]])
            rotation_matrix = np.dot(rotation_z, np.dot(rotation_y, rotation_x))
            rotated_vertices = np.dot(scaled_vertices - self.center, rotation_matrix.T) + self.center

            # Apply translation
            translated_vertices = rotated_vertices + self.position

            self.mesh_item.setMeshData(vertexes=translated_vertices, faces=self.wireframe.triangles())

            if self.edge_item:
                self.edge_item.setData(pos=translated_vertices)

            if self.vertex_item:
                self.vertex_item.setData(pos=translated_vertices)

    def translate(self, dx, dy, dz):
        self.position += np.array([dx, dy, dz])

    def rotate(self, rx, ry, rz):
        self.rotation += np.array([rx, ry, rz])

    def scale_object(self, sx, sy, sz):
        self.scale *= np.array([sx, sy, sz])
        self.update_center()

    def cleanup(self):
        """Remove all items associated with this object from the view."""
        if self.mesh_item:
            self.mesh_item.setParent(None)
            self.mesh_item = None
        if self.edge_item:
            self.edge_item.setParent(None)
            self.edge_item = None
        if self.vertex_item:
            self.vertex_item.setParent(None)
            self.vertex_item = None


class Scene:
    def __init__(self):
        self.objects = []

    def add_object(self, scene_object):
        self.objects.append(scene_object)

    def remove_object(self, scene_object):
        self.objects.remove(scene_object)

    def update_physics(self, dt):
        for obj in self.objects:
            # Update position
            obj.position += obj.velocity * dt

            # Update rotation
            obj.rotation += obj.angular_velocity * dt

            # Apply simple gravity
            obj.velocity[1] -= 9.8 * dt  # Assuming Y is up

            # Simple ground collision
            if obj.position[1] < 0:
                obj.position[1] = 0
                obj.velocity[1] = -obj.velocity[1] * 0.8  # Bounce with damping

    def apply_transformations(self):
        for obj in self.objects:
            obj.apply_transformation()


class ColorButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setColor(color)

    def setColor(self, color):
        self.color = color
        self.setStyleSheet(f"background-color: {color.name()}; color: {'black' if color.lightness() > 127 else 'white'}")
        self.setText(color.name())

class DisplayOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Display Options")
        self.setGeometry(100, 100, 300, 300)

        layout = QVBoxLayout()

        self.show_faces = QCheckBox("Show Faces")
        self.show_edges = QCheckBox("Show Edges")
        self.show_vertices = QCheckBox("Show Vertices")

        self.face_color_btn = ColorButton(QColor(200, 200, 200))
        self.edge_color_btn = ColorButton(QColor(0, 0, 0))
        self.vertex_color_btn = ColorButton(QColor(255, 0, 0))

        self.edge_width = QSpinBox()
        self.edge_width.setRange(1, 10)
        self.edge_width.setValue(1)
        self.edge_width.setPrefix("Edge Width: ")

        self.vertex_size = QSpinBox()
        self.vertex_size.setRange(1, 20)
        self.vertex_size.setValue(5)
        self.vertex_size.setPrefix("Vertex Size: ")

        layout.addWidget(self.show_faces)
        layout.addWidget(self.show_edges)
        layout.addWidget(self.show_vertices)
        layout.addWidget(self.face_color_btn)
        layout.addWidget(self.edge_color_btn)
        layout.addWidget(self.vertex_color_btn)
        layout.addWidget(self.edge_width)
        layout.addWidget(self.vertex_size)

        self.setLayout(layout)

class ObjectPropertiesDialog(QDialog):
    def __init__(self, scene_object, parent=None):
        super().__init__(parent)
        self.scene_object = scene_object
        self.setWindowTitle(f"Properties: {scene_object.name}")
        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        self.name_input = QLineEdit(self.scene_object.name)
        layout.addRow("Name:", self.name_input)

        self.mass_input = QDoubleSpinBox()
        self.mass_input.setRange(0.1, 1000)
        self.mass_input.setValue(self.scene_object.mass)
        layout.addRow("Mass:", self.mass_input)

        self.scale_x = QDoubleSpinBox()
        self.scale_y = QDoubleSpinBox()
        self.scale_z = QDoubleSpinBox()
        for spinbox in (self.scale_x, self.scale_y, self.scale_z):
            spinbox.setRange(0.1, 10)
            spinbox.setSingleStep(0.1)
            spinbox.setValue(1)
        layout.addRow("Scale X:", self.scale_x)
        layout.addRow("Scale Y:", self.scale_y)
        layout.addRow("Scale Z:", self.scale_z)

        self.rot_speed_x = QDoubleSpinBox()
        self.rot_speed_y = QDoubleSpinBox()
        self.rot_speed_z = QDoubleSpinBox()
        for spinbox in (self.rot_speed_x, self.rot_speed_y, self.rot_speed_z):
            spinbox.setRange(-10, 10)
            spinbox.setSingleStep(0.1)
            spinbox.setValue(0)
        layout.addRow("Rotation Speed X:", self.rot_speed_x)
        layout.addRow("Rotation Speed Y:", self.rot_speed_y)
        layout.addRow("Rotation Speed Z:", self.rot_speed_z)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_values(self):
        return {
            "name": self.name_input.text(),
            "mass": self.mass_input.value(),
            "scale": (self.scale_x.value(), self.scale_y.value(), self.scale_z.value()),
            "rotation_speed": (self.rot_speed_x.value(), self.rot_speed_y.value(), self.rot_speed_z.value())
        }


class WireframeViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scene = Scene()
        self.initUI()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_scene)
        self.animation_timer.start(16)  # ~60 FPS
        self.last_time = QTime.currentTime()
        self.is_playing = False
        self.selected_object = None
        self.last_mouse_pos = None
        self.hovered_object = None


    def initUI(self):
        self.setWindowTitle('Wireframe Viewer')
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Create a splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel for object list and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.object_list = QListWidget()
        self.object_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.object_list.customContextMenuRequested.connect(self.show_context_menu)
        left_layout.addWidget(QLabel("Scene Objects:"))
        left_layout.addWidget(self.object_list)

        load_button = QPushButton('Load Shape')
        load_button.clicked.connect(self.show_shape_loader)
        left_layout.addWidget(load_button)

        remove_button = QPushButton('Remove Selected')
        remove_button.clicked.connect(self.remove_selected_object)
        left_layout.addWidget(remove_button)

        # Animation controls
        anim_layout = QHBoxLayout()
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.toggle_animation)
        anim_layout.addWidget(self.play_button)
        left_layout.addLayout(anim_layout)

        splitter.addWidget(left_panel)

        # Right panel for 3D view and controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 3D visualization widget
        self.view = gl.GLViewWidget()
        right_layout.addWidget(self.view, stretch=4)

        # Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        right_layout.addWidget(controls_widget, stretch=1)

        # Transformation controls
        self.create_transformation_controls(controls_layout)

        splitter.addWidget(right_panel)

        # Set the initial sizes of the splitter
        splitter.setSizes([200, 800])

        # Menu
        self.create_menus()

        # Shape loader
        self.shape_loader = ShapeLoaderDialog(self)
        self.shape_loader.shape_loaded.connect(self.on_shape_loaded)

        # Display options
        self.display_options = DisplayOptionsDialog(self)
        self.setup_display_options()

        # Set up mouse interaction for the GLViewWidget
        self.view.mousePressEvent = self.mousePressEvent
        self.view.mouseMoveEvent = self.mouseMoveEvent
        self.view.mouseReleaseEvent = self.mouseReleaseEvent

        # Modify the object_list to handle double clicks
        self.object_list.itemDoubleClicked.connect(self.center_view_on_object)

        # Set up mouse tracking for hover effect
        self.view.setMouseTracking(True)
        self.view.mouseMoveEvent = self.mouseMoveEvent

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        view_menu = menubar.addMenu('View')
        shape_menu = menubar.addMenu('Shapes')

        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        display_options_action = QAction('Display Options', self)
        display_options_action.triggered.connect(self.show_display_options)
        view_menu.addAction(display_options_action)

        load_shape_action = QAction('Load Shape', self)
        load_shape_action.triggered.connect(self.show_shape_loader)
        shape_menu.addAction(load_shape_action)

    def show_context_menu(self, position):
        item = self.object_list.itemAt(position)
        if item is not None:
            index = self.object_list.row(item)
            scene_object = self.scene.objects[index]

            context_menu = QMenu(self)
            rename_action = context_menu.addAction("Rename")
            delete_action = context_menu.addAction("Delete")
            properties_action = context_menu.addAction("Properties")
            toggle_animation_action = context_menu.addAction("Toggle Animation")

            action = context_menu.exec_(self.object_list.mapToGlobal(position))

            if action == rename_action:
                self.rename_object(scene_object)
            elif action == delete_action:
                self.delete_object(index)
            elif action == properties_action:
                self.show_properties_dialog(scene_object)
            elif action == toggle_animation_action:
                scene_object.toggle_animation()


    def setup_display_options(self):
        self.display_options.show_faces.setChecked(True)
        self.display_options.show_edges.setChecked(True)
        self.display_options.show_vertices.setChecked(False)
        self.display_options.face_color_btn.clicked.connect(lambda: self.change_color('face'))
        self.display_options.edge_color_btn.clicked.connect(lambda: self.change_color('edge'))
        self.display_options.vertex_color_btn.clicked.connect(lambda: self.change_color('vertex'))
        self.display_options.show_faces.stateChanged.connect(self.update_display_options)
        self.display_options.show_edges.stateChanged.connect(self.update_display_options)
        self.display_options.show_vertices.stateChanged.connect(self.update_display_options)
        self.display_options.edge_width.valueChanged.connect(self.update_display_options)
        self.display_options.vertex_size.valueChanged.connect(self.update_display_options)


    def create_transformation_controls(self, layout):
        transform_layout = QHBoxLayout()

        # Translation controls
        translation_group = QGroupBox("Translation")
        translation_layout = QVBoxLayout()
        translation_group.setLayout(translation_layout)
        self.translate_x = self.create_labeled_slider("X", -5, 5, 0, 0.1, translation_layout)
        self.translate_y = self.create_labeled_slider("Y", -5, 5, 0, 0.1, translation_layout)
        self.translate_z = self.create_labeled_slider("Z", -5, 5, 0, 0.1, translation_layout)
        transform_layout.addWidget(translation_group)

        # Scale control
        scale_group = QGroupBox("Scale")
        scale_layout = QVBoxLayout()
        scale_group.setLayout(scale_layout)
        self.scale_slider = self.create_labeled_slider("Scale", 0.1, 2, 1, 0.1, scale_layout)
        transform_layout.addWidget(scale_group)

        layout.addLayout(transform_layout)

        # Reset button
        self.reset_button = QPushButton("Reset Transformation")
        self.reset_button.clicked.connect(self.reset_transformation)
        layout.addWidget(self.reset_button)

    def create_labeled_slider(self, label, min_val, max_val, initial_val, step, layout):
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel(label))

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val / step))
        slider.setMaximum(int(max_val / step))
        slider.setValue(int(initial_val / step))
        slider.valueChanged.connect(self.apply_transformation)

        value_label = QLabel(f"{initial_val:.1f}")
        slider.valueChanged.connect(lambda v: value_label.setText(f"{v * step:.1f}"))

        slider_layout.addWidget(slider)
        slider_layout.addWidget(value_label)
        layout.addLayout(slider_layout)
        return slider

    def load_shape(self):
        shape = self.shape_combo.currentText()
        self.view.clear()

        try:
            if shape == 'Cube':
                self.wireframe = Wireframe.create_cube()
            elif shape == 'Sphere':
                self.wireframe = Wireframe.create_sphere()
            elif shape == 'Tetrahedron':
                self.wireframe = Wireframe.create_tetrahedron()
            elif shape == 'Octahedron':
                self.wireframe = Wireframe.create_octahedron()
            elif shape == 'Icosahedron':
                self.wireframe = Wireframe.create_icosahedron()
            elif shape == 'Torus':
                self.wireframe = Wireframe.create_torus()
            elif shape == 'Cylinder':
                self.wireframe = Wireframe.create_cylinder()
            elif shape == 'Cone':
                self.wireframe = Wireframe.create_cone()

            self.update_display()
            self.reset_transformation()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load shape: {str(e)}")

    def apply_transformation(self):
        if not self.scene.objects:
            return

        try:
            # Apply translation
            translation = np.array([
                self.translate_x.value() * 0.1,
                self.translate_y.value() * 0.1,
                self.translate_z.value() * 0.1
            ])

            # Apply scaling
            scale_factor = self.scale_slider.value() * 0.1
            scaling = np.array([scale_factor, scale_factor, scale_factor])

            for obj in self.scene.objects:
                # Reset to original position and scale
                obj.position = np.zeros(3)
                obj.scale = np.ones(3)

                # Apply new translation and scaling
                obj.position += translation
                obj.scale *= scaling

                obj.apply_transformation()

            self.update_display()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error applying transformation: {str(e)}")

    def reset_transformation(self):
        for slider in [self.translate_x, self.translate_y, self.translate_z]:
            slider.setValue(0)
        self.scale_slider.setValue(10)  # 1.0 scale

        for obj in self.scene.objects:
            obj.position = np.zeros(3)
            obj.scale = np.ones(3)
            obj.rotation = np.zeros(3)
            obj.apply_transformation()

        self.update_display()

    def show_display_options(self):
        self.display_options.show()

    def change_color(self, component):
        color = QColorDialog.getColor()
        if color.isValid():
            if component == 'face':
                self.display_options.face_color_btn.setColor(color)
            elif component == 'edge':
                self.display_options.edge_color_btn.setColor(color)
            elif component == 'vertex':
                self.display_options.vertex_color_btn.setColor(color)
            self.update_display_options()

    def update_display_options(self):
        for obj in self.scene.objects:
            obj.update_mesh(self.display_options)

    def update_display(self):
        #print("Updating display")
        for obj in self.scene.objects:
            obj.update_mesh(self.display_options)
        self.view.update()


    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "", "OBJ Files (*.obj);;JSON Files (*.json)")
        if filename:
            try:
                if filename.endswith('.obj'):
                    wireframe = Wireframe.load_from_obj(filename)
                elif filename.endswith('.json'):
                    wireframe = Wireframe.load_from_json(filename)
                else:
                    raise ValueError("expected a .obj or .json file")
                self.add_wireframe(wireframe, f"file: {filename.replace(chr(92), '/').split('/')[-1]}")
                self.update_display()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def save_file(self):
        """Save the selected scene object's wireframe (or the most recently added one)."""
        if not self.scene.objects:
            QMessageBox.warning(self, "Warning", "No wireframe to save")
            return
        row = self.object_list.currentRow()
        wireframe = self.scene.objects[row if 0 <= row < len(self.scene.objects) else -1].wireframe

        filename, _ = QFileDialog.getSaveFileName(self, "Save File", "", "OBJ Files (*.obj);;JSON Files (*.json)")
        if filename:
            try:
                if filename.endswith('.json'):
                    wireframe.save_to_json(filename)
                else:
                    wireframe.save_to_obj(filename)
                QMessageBox.information(self, "Success", "File saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")


    def show_shape_loader(self):
        self.shape_loader.show()
        self.shape_loader.raise_()
        self.shape_loader.activateWindow()

    def on_shape_loaded(self, shape_data):
        print(f"Debug - WireframeViewer: Received shape_data: {shape_data}")
        shape_type, shape_info = shape_data
        try:
            wireframe = self.create_wireframe(shape_type, shape_info)
            if wireframe:
                self.add_wireframe(wireframe, f"{shape_type}: {shape_info}")
        except Exception as e:
            print(f"Error loading shape: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load shape: {str(e)}")

    def add_wireframe(self, wireframe, name):
        """Add a wireframe to the scene; the mesh is built first so a failure leaves the scene unchanged."""
        scene_object = SceneObject(wireframe)
        scene_object.wireframe.name = name
        scene_object.update_mesh(self.display_options)
        self.scene.add_object(scene_object)
        self.view.addItem(scene_object.mesh_item)
        if scene_object.edge_item:
            self.view.addItem(scene_object.edge_item)
        if scene_object.vertex_item:
            self.view.addItem(scene_object.vertex_item)
        self.object_list.addItem(scene_object.wireframe.name)
        return scene_object

    def create_wireframe(self, shape_type, shape_info):
        if shape_type == 'basic':
            return Wireframe.create_basic_shape(shape_info)
        elif shape_type == 'parametric':
            return Wireframe.create_parametric_shape(*shape_info)
        elif shape_type == 'fractal':
            return Wireframe.create_fractal(*shape_info)
        elif shape_type == 'text':
            return Wireframe.create_text(shape_info)
        elif shape_type == 'mri':
            return Wireframe.load_mri(shape_info)
        elif shape_type == 'super_resolution':
            return Wireframe.load_super_resolution(shape_info)
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")

    def remove_selected_object(self):
        selected_items = self.object_list.selectedItems()
        for item in selected_items:
            index = self.object_list.row(item)
            if 0 <= index < len(self.scene.objects):
                scene_object = self.scene.objects[index]

                # Remove items from the view
                if scene_object.mesh_item in self.view.items:
                    self.view.removeItem(scene_object.mesh_item)
                if scene_object.edge_item in self.view.items:
                    self.view.removeItem(scene_object.edge_item)
                if scene_object.vertex_item in self.view.items:
                    self.view.removeItem(scene_object.vertex_item)

                # Remove object from the scene
                self.scene.objects.pop(index)

                # Remove item from the list widget
                self.object_list.takeItem(index)
            else:
                print(f"Invalid index {index} for object removal")

        # Ensure the object_list and scene.objects are in sync
        self.sync_object_list()

    def rename_object(self, scene_object):
        new_name, ok = QInputDialog.getText(self, "Rename Object", "Enter new name:", text=scene_object.name)
        if ok and new_name:
            scene_object.set_name(new_name)
            self.update_object_list()

    def delete_object(self, index):
        if 0 <= index < len(self.scene.objects):
            # Remove the object from the scene
            obj_to_remove = self.scene.objects.pop(index)

            # Remove the object's items from the 3D view
            if obj_to_remove.mesh_item:
                self.view.removeItem(obj_to_remove.mesh_item)
            if obj_to_remove.edge_item:
                self.view.removeItem(obj_to_remove.edge_item)
            if obj_to_remove.vertex_item:
                self.view.removeItem(obj_to_remove.vertex_item)

            # Update the object list in the UI
            self.update_object_list()

            # If the deleted object was the hovered object, reset it
            if self.hovered_object == obj_to_remove:
                self.hovered_object = None

            # If the deleted object was the selected object, reset it
            if self.selected_object == obj_to_remove:
                self.selected_object = None

            print(f"Object at index {index} deleted and removed from view")
        else:
            print(f"Invalid index {index} for object deletion")


    def show_properties_dialog(self, scene_object):
        dialog = ObjectPropertiesDialog(scene_object, self)
        if dialog.exec_():
            values = dialog.get_values()
            scene_object.set_name(values["name"])
            scene_object.set_mass(values["mass"])
            scene_object.set_scale(*values["scale"])
            scene_object.set_rotation_speed(*values["rotation_speed"])
            self.update_object_list()
            self.update_display()

    def update_object_list(self):
        self.object_list.clear()
        for obj in self.scene.objects:
            self.object_list.addItem(obj.name)

    def update_scene(self):
        current_time = QTime.currentTime()
        dt = self.last_time.msecsTo(current_time) / 1000.0
        self.last_time = current_time

        for obj in self.scene.objects:
            obj.update_animation(dt)

        self.update_display()


    def sync_object_list(self):
        # Clear the object_list
        self.object_list.clear()

        # Repopulate the object_list from scene.objects
        for obj in self.scene.objects:
            # Assuming each object has a name or some identifier
            self.object_list.addItem(f"Object: {obj.wireframe.name if hasattr(obj.wireframe, 'name') else 'Unnamed'}")


    def toggle_animation(self):
        if self.is_playing:
            self.is_playing = False
            self.play_button.setText('Play')
        else:
            self.is_playing = True
            self.play_button.setText('Pause')
            self.last_time = QTime.currentTime()

    # def update_scene(self):
    #     current_time = QTime.currentTime()

    #     if self.is_playing:
    #         dt = self.last_time.msecsTo(current_time) / 1000.0
    #         self.scene.update_physics(dt)

    #     self.last_time = current_time
    #     self.scene.apply_transformations()
    #     self.update_display()


    def load_basic_shape(self, shape_name):
        try:
            self.wireframe = Wireframe.create_basic_shape(shape_name)
            print(f"Debug - WireframeViewer: Basic shape '{shape_name}' created successfully")
        except Exception as e:
            print(f"Debug - WireframeViewer: Error creating basic shape: {str(e)}")
            raise

    def load_parametric_shape(self, shape_info):
        shape_name, u_res, v_res = shape_info
        try:
            self.wireframe = Wireframe.create_parametric_shape(shape_name, u_res, v_res)
            print(f"Debug - WireframeViewer: Parametric shape '{shape_name}' created successfully")
        except Exception as e:
            print(f"Debug - WireframeViewer: Error creating parametric shape: {str(e)}")
            raise

    def load_fractal_shape(self, fractal_info):
        fractal_type, iterations, size = fractal_info
        try:
            if fractal_type == 'Sierpinski Triangle':
                self.wireframe = Wireframe.create_sierpinski_triangle(iterations, size)
            elif fractal_type == 'Koch Snowflake':
                self.wireframe = Wireframe.create_koch_snowflake(iterations, size)
            elif fractal_type == 'Menger Sponge':
                self.wireframe = Wireframe.create_menger_sponge(iterations, size)
            elif fractal_type == 'Apollonian Gasket':
                self.wireframe = Wireframe.create_apollonian_gasket(iterations, size)
            elif fractal_type == 'Jerusalem Cube':
                self.wireframe = Wireframe.create_jerusalem_cube(iterations, size)
            elif fractal_type == 'Sierpinski Tetrahedron':
                self.wireframe = Wireframe.create_sierpinski_tetrahedron(iterations, size)
            elif fractal_type == 'Pythagoras Tree 3D':
                self.wireframe = Wireframe.create_pythagoras_tree_3d(iterations, size)
            else:
                raise ValueError(f"Unknown fractal type: {fractal_type}")
            print(f"Debug - WireframeViewer: Fractal '{fractal_type}' created successfully")
        except Exception as e:
            print(f"Debug - WireframeViewer: Error creating fractal: {str(e)}")
            raise

    def load_text_shape(self, text):
        try:
            self.wireframe = Wireframe.create_text(text)
            print(f"Debug - WireframeViewer: Text shape '{text}' created successfully")
        except Exception as e:
            print(f"Debug - WireframeViewer: Error creating text shape: {str(e)}")
            raise

    def load_mri_data(self, filename):
        try:
            self.wireframe = Wireframe.load_mri(filename)
            print(f"Debug - WireframeViewer: MRI data loaded successfully from {filename}")
        except Exception as e:
            print(f"Debug - WireframeViewer: Error loading MRI data: {str(e)}")
            raise

    def load_super_resolution_data(self, filename):
        try:
            self.wireframe = Wireframe.load_super_resolution(filename)
            print(f"Debug - WireframeViewer: Super-resolution data loaded successfully from {filename}")
        except Exception as e:
            print(f"Debug - WireframeViewer: Error loading super-resolution data: {str(e)}")
            raise

    def mouseMoveEvent(self, event):
        pos = QPointF(event.x(), event.y())
        new_hovered_object = self.get_object_at_position(pos)
        #print(f"Mouse moved to ({event.x()}, {event.y()})")
        #print(f"New hovered object: {new_hovered_object}")

        if new_hovered_object != self.hovered_object:
            #print("Hover object changed")
            if self.hovered_object:
                #print(f"Resetting color of previously hovered object: {self.hovered_object}")
                self.hovered_object.reset_color()

            self.hovered_object = new_hovered_object
            if self.hovered_object:
                #print(f"Setting hover color for new hovered object: {self.hovered_object}")
                self.hovered_object.set_hover_color()

            self.update_display()

        # Handle dragging for selected object
        if self.selected_object and event.buttons() & Qt.LeftButton:
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()

            if event.modifiers() & Qt.ControlModifier:
                self.selected_object.translate(-dx * 0.01, dy * 0.01, 0)
            else:
                self.selected_object.rotate(-dy * 0.01, -dx * 0.01, 0)

            self.selected_object.apply_transformation()
            self.update_display()

        self.last_mouse_pos = event.pos()


    def center_view_on_object(self, item):
        index = self.object_list.row(item)
        if 0 <= index < len(self.scene.objects):
            obj = self.scene.objects[index]
            center = obj.get_center()
            # Convert NumPy array to QVector3D
            center_qvector = QVector3D(center[0], center[1], center[2])

            # Get the current distance of the camera from the center
            current_distance = (self.view.cameraPosition() - self.view.opts['center']).length()

            # Set the new center
            self.view.opts['center'] = center_qvector

            # Calculate the new camera position
            camera_vector = self.view.cameraPosition() - self.view.opts['center']
            camera_vector = camera_vector.normalized() * current_distance
            new_camera_pos = center_qvector + camera_vector

            # Update the camera position
            self.view.setCameraPosition(pos=new_camera_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected_object = None
            self.last_mouse_pos = None


    def get_object_at_position(self, pos):
        ray_start, ray_direction = self.calculate_camera_ray(pos)
        if ray_start is None or ray_direction is None:
            print("Failed to calculate camera ray")
            return None

        # Convert QVector3D to NumPy arrays
        ray_start = np.array([ray_start.x(), ray_start.y(), ray_start.z()])
        ray_direction = np.array([ray_direction.x(), ray_direction.y(), ray_direction.z()])

        closest_object = None
        min_distance = float('inf')

        for obj in self.scene.objects:
            object_center = obj.get_center()

            # Calculate the closest point on the ray to the object's center
            t = np.dot(object_center - ray_start, ray_direction)
            closest_point = ray_start + t * ray_direction

            # Calculate the distance from the closest point to the object's center
            distance = np.linalg.norm(object_center - closest_point)

            #print(f"Object: {obj}, Distance: {distance}")

            # Update the closest object if this one is closer
            if distance < min_distance:
                min_distance = distance
                closest_object = obj

        # Return the closest object if it's within a certain threshold distance
        threshold = 1.0  # Increased threshold for easier selection
        result = closest_object if min_distance < threshold else None
        #rint(f"Closest object: {result}, Distance: {min_distance}")
        return result

    def calculate_camera_ray(self, pos):
        # Get the view matrix
        view_matrix = self.view.viewMatrix()

        # Get the projection matrix
        try:
            projection_matrix = self.view.projectionMatrix()  # pyqtgraph < 0.13
        except TypeError:  # pyqtgraph >= 0.13: projectionMatrix(region, viewport)
            viewport = self.view.getViewport()
            projection_matrix = self.view.projectionMatrix(viewport, viewport)

        # Combine view and projection matrices
        view_projection_matrix = projection_matrix * view_matrix

        # Invert the combined matrix
        inverse_matrix, invertible = view_projection_matrix.inverted()
        if not invertible:
            print("Error: View projection matrix is not invertible")
            return None, None

        # Calculate near and far points in normalized device coordinates
        x = (2.0 * pos.x()) / self.view.width() - 1.0
        y = 1.0 - (2.0 * pos.y()) / self.view.height()
        near_point = QVector3D(x, y, -1.0)
        far_point = QVector3D(x, y, 1.0)

        # Transform near and far points to world coordinates
        near_point = inverse_matrix.map(near_point)
        far_point = inverse_matrix.map(far_point)

        # Calculate ray direction
        ray_direction = (far_point - near_point).normalized()

        return near_point, ray_direction


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()
            self.selected_object = self.get_object_at_position(QPointF(event.x(), event.y()))
            if self.selected_object:
                print(f"Selected object: {self.selected_object}")  # Debug print
            else:
                print("No object selected")  # Debug print

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = WireframeViewer()
    viewer.show()
    sys.exit(app.exec_())
