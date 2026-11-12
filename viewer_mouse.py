"""Mouse handling of the desktop viewer (ViewerMouseMixin, mixed into WireframeViewer): hover highlight, press to
pick an object, drag to rotate it (Ctrl + drag moves it), double-click a list entry to centre the camera, and the
camera-ray picking. Split out of wireframe_viewer.py (2026-11-11).
"""
import numpy as np
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QVector3D


class ViewerMouseMixin:
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
