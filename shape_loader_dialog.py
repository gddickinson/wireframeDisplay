from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLineEdit,
                             QLabel, QGroupBox, QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import pyqtSignal, Qt

import shape_catalog as catalog

class ShapeLoaderDialog(QDialog):
    shape_loaded = pyqtSignal(object)  # Signal to emit the loaded shape

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shape Loader")
        self.setGeometry(100, 100, 400, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Keep dialog on top
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Basic shapes
        basic_group = QGroupBox("Basic Shapes")
        basic_layout = QVBoxLayout()
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(catalog.BASIC_SHAPES)
        basic_layout.addWidget(self.shape_combo)
        self.load_basic_button = QPushButton('Load Basic Shape')
        self.load_basic_button.clicked.connect(self.load_basic_shape)
        basic_layout.addWidget(self.load_basic_button)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Parametric shapes
        parametric_group = QGroupBox("Parametric Shapes")
        parametric_layout = QVBoxLayout()
        self.parametric_combo = QComboBox()
        self.parametric_combo.addItems(catalog.PARAMETRIC_SHAPES)
        parametric_layout.addWidget(self.parametric_combo)
        self.param_u = QSpinBox()
        self.param_u.setRange(*catalog.PARAM_RESOLUTION[:2])
        self.param_u.setValue(catalog.PARAM_RESOLUTION[2])
        parametric_layout.addWidget(QLabel("U resolution:"))
        parametric_layout.addWidget(self.param_u)
        self.param_v = QSpinBox()
        self.param_v.setRange(*catalog.PARAM_RESOLUTION[:2])
        self.param_v.setValue(catalog.PARAM_RESOLUTION[2])
        parametric_layout.addWidget(QLabel("V resolution:"))
        parametric_layout.addWidget(self.param_v)
        self.load_parametric_button = QPushButton('Load Parametric Shape')
        self.load_parametric_button.clicked.connect(self.load_parametric_shape)
        parametric_layout.addWidget(self.load_parametric_button)
        parametric_group.setLayout(parametric_layout)
        layout.addWidget(parametric_group)

        # Fractal patterns
        fractal_group = QGroupBox("Fractal Patterns")
        fractal_layout = QVBoxLayout()
        self.fractal_combo = QComboBox()
        self.fractal_combo.addItems(catalog.FRACTALS)
        fractal_layout.addWidget(QLabel("Fractal Type:"))
        fractal_layout.addWidget(self.fractal_combo)
        self.fractal_iterations = QSpinBox()
        self.fractal_iterations.setRange(*catalog.FRACTAL_ITERATIONS[:2])
        self.fractal_iterations.setValue(catalog.FRACTAL_ITERATIONS[2])
        fractal_layout.addWidget(QLabel("Iterations:"))
        fractal_layout.addWidget(self.fractal_iterations)
        self.fractal_size = QDoubleSpinBox()
        self.fractal_size.setRange(*catalog.FRACTAL_SIZE[:2])
        self.fractal_size.setValue(catalog.FRACTAL_SIZE[2])
        self.fractal_size.setSingleStep(catalog.FRACTAL_SIZE[3])
        fractal_layout.addWidget(QLabel("Size:"))
        fractal_layout.addWidget(self.fractal_size)
        self.load_fractal_button = QPushButton('Load Fractal')
        self.load_fractal_button.clicked.connect(self.load_fractal)
        fractal_layout.addWidget(self.load_fractal_button)
        fractal_group.setLayout(fractal_layout)
        layout.addWidget(fractal_group)

        # Text shapes
        text_group = QGroupBox("Text Shapes")
        text_layout = QVBoxLayout()
        self.text_input = QLineEdit()
        text_layout.addWidget(QLabel("Enter Text:"))
        text_layout.addWidget(self.text_input)
        self.load_text_button = QPushButton('Load Text Shape')
        self.load_text_button.clicked.connect(self.load_text_shape)
        text_layout.addWidget(self.load_text_button)
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

        # MRI data
        mri_group = QGroupBox("MRI Data (NIfTI isosurface)")
        mri_layout = QVBoxLayout()
        self.load_mri_button = QPushButton('Load MRI Data')
        self.load_mri_button.clicked.connect(self.load_mri_data)
        mri_layout.addWidget(self.load_mri_button)
        mri_group.setLayout(mri_layout)
        layout.addWidget(mri_group)

        self.setLayout(layout)

    def load_basic_shape(self):
        shape = self.shape_combo.currentText()
        self.shape_loaded.emit(('basic', shape))

    def load_parametric_shape(self):
        shape = self.parametric_combo.currentText()
        u_res = self.param_u.value()
        v_res = self.param_v.value()
        self.shape_loaded.emit(('parametric', (shape, u_res, v_res)))

    def load_fractal(self):
        fractal_type = self.fractal_combo.currentText()
        iterations = self.fractal_iterations.value()
        size = self.fractal_size.value()
        self.shape_loaded.emit(('fractal', (fractal_type, iterations, size)))

    def load_text_shape(self):
        text = self.text_input.text()
        if text:
            self.shape_loaded.emit(('text', text))
        else:
            QMessageBox.warning(self, "Warning", "Please enter some text")

    def load_mri_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open MRI Data", "", "NIfTI files (*.nii *.nii.gz)")
        if filename:
            self.shape_loaded.emit(('mri', filename))

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dialog = ShapeLoaderDialog()
    dialog.show()
    sys.exit(app.exec_())
