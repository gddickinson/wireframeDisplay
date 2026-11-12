"""Shape and file loading of the desktop viewer (ViewerFilesMixin, mixed into WireframeViewer): shape loader signals,
File > Open / Save (OBJ, JSON), adding wireframes to the scene and the legacy load_* helpers. Split out of
wireframe_viewer.py (2026-11-11).
"""
from PyQt5.QtWidgets import QMessageBox, QFileDialog

from wireframe import Wireframe
from scene_objects import SceneObject


class ViewerFilesMixin:
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
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")

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
