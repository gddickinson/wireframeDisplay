"""Dialogs of the desktop viewer: ColorButton, DisplayOptionsDialog (View > Display Options) and
ObjectPropertiesDialog (right-click > Properties). Split out of wireframe_viewer.py (2026-11-11).
"""
from PyQt5.QtWidgets import (QPushButton, QDialog, QVBoxLayout, QCheckBox, QSpinBox, QFormLayout, QLineEdit,
                             QDoubleSpinBox, QDialogButtonBox)
from PyQt5.QtGui import QColor

import shape_catalog as catalog


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

        d = catalog.DISPLAY
        self.face_color_btn = ColorButton(QColor.fromRgbF(*catalog.OBJECT_COLOR))  # what objects are drawn in
        self.edge_color_btn = ColorButton(QColor(*d["edge_color"]))
        self.vertex_color_btn = ColorButton(QColor(*d["vertex_color"]))

        self.edge_width = QSpinBox()
        self.edge_width.setRange(*d["edge_width"][:2])
        self.edge_width.setValue(d["edge_width"][2])
        self.edge_width.setPrefix("Edge Width: ")

        self.vertex_size = QSpinBox()
        self.vertex_size.setRange(*d["vertex_size"][:2])
        self.vertex_size.setValue(d["vertex_size"][2])
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
