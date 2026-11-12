"""Desktop app: the WireframeViewer main window (PyQt5 + pyqtgraph). Run: python wireframe_viewer.py

Parts live in scene_objects.py (SceneObject, Scene), viewer_dialogs.py (dialogs), viewer_mouse.py (mouse) and
viewer_files.py (shape and file loading); their public names are re-exported here.
"""
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSlider,
                             QLabel, QMessageBox, QGroupBox, QColorDialog, QAction, QListWidget, QSplitter, QMenu,
                             QInputDialog)
from PyQt5.QtCore import Qt, QTimer, QTime
import pyqtgraph.opengl as gl
import numpy as np

import shape_catalog as catalog
from shape_loader_dialog import ShapeLoaderDialog
from scene_objects import SceneObject, Scene, default_style, display_style  # noqa: F401 (re-exported)
from viewer_dialogs import ColorButton, DisplayOptionsDialog, ObjectPropertiesDialog  # noqa: F401 (re-exported)
from viewer_files import ViewerFilesMixin
from viewer_mouse import ViewerMouseMixin
from wireframe import Wireframe  # noqa: F401 (re-exported)


class WireframeViewer(ViewerFilesMixin, ViewerMouseMixin, QMainWindow):
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
        self.display_options.show_faces.setChecked(catalog.DISPLAY["show_faces"])
        self.display_options.show_edges.setChecked(catalog.DISPLAY["show_edges"])
        self.display_options.show_vertices.setChecked(catalog.DISPLAY["show_vertices"])
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
        self.translate_x = self.create_labeled_slider("X", *catalog.TRANSLATION_SLIDER, translation_layout)
        self.translate_y = self.create_labeled_slider("Y", *catalog.TRANSLATION_SLIDER, translation_layout)
        self.translate_z = self.create_labeled_slider("Z", *catalog.TRANSLATION_SLIDER, translation_layout)
        transform_layout.addWidget(translation_group)

        # Scale control
        scale_group = QGroupBox("Scale")
        scale_layout = QVBoxLayout()
        scale_group.setLayout(scale_layout)
        self.scale_slider = self.create_labeled_slider("Scale", *catalog.SCALE_SLIDER, scale_layout)
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

        if self.is_playing:  # Play button: run the physics (gravity and ground bounce)
            self.scene.update_physics(dt)

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = WireframeViewer()
    viewer.show()
    sys.exit(app.exec_())
