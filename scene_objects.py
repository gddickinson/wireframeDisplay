"""Scene objects of the desktop viewer: SceneObject (a Wireframe with position, rotation, scale, physics state and
its GL items: faces, edges, vertices), Scene (the object list and physics), and the display-style helpers
default_style / display_style. Split out of wireframe_viewer.py (2026-11-11).
"""
import numpy as np
import pyqtgraph.opengl as gl

import shape_catalog as catalog
from mesh_utils import edges_from_faces
from scene_math import physics_step, transform_vertices


def _rgba(qcolor):
    return (qcolor.redF(), qcolor.greenF(), qcolor.blueF(), 1.0)


def default_style():
    """Display style before the options dialog is read: shape_catalog defaults."""
    d = catalog.DISPLAY
    return {"show_faces": d["show_faces"], "show_edges": d["show_edges"], "show_vertices": d["show_vertices"],
            "face_color": catalog.OBJECT_COLOR, "edge_color": tuple(c / 255 for c in d["edge_color"]) + (1.0,),
            "vertex_color": tuple(c / 255 for c in d["vertex_color"]) + (1.0,),
            "edge_width": d["edge_width"][2], "vertex_size": d["vertex_size"][2]}


def display_style(options):
    """The settings of a DisplayOptionsDialog as plain values (colours as RGBA 0-1)."""
    return {"show_faces": options.show_faces.isChecked(), "show_edges": options.show_edges.isChecked(),
            "show_vertices": options.show_vertices.isChecked(), "face_color": _rgba(options.face_color_btn.color),
            "edge_color": _rgba(options.edge_color_btn.color), "vertex_color": _rgba(options.vertex_color_btn.color),
            "edge_width": options.edge_width.value(), "vertex_size": options.vertex_size.value()}


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
        self.original_color = catalog.OBJECT_COLOR  # Light gray
        self.hover_color = catalog.HOVER_COLOR  # Bright red
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
        """Rebuild the GL items: faces (GLMeshItem), polygon edges (GLLinePlotItem) and vertices (GLScatterPlotItem).
        display_options is the DisplayOptionsDialog; None keeps the current style (animation / properties updates)."""
        if display_options is not None:
            self.style = display_style(display_options)
        style = getattr(self, "style", None) or default_style()
        if self.current_color != self.hover_color:
            self.current_color = style["face_color"]
        self.original_color = style["face_color"]
        transformed_vertices = self.get_transformed_vertices()

        if self.mesh_item is None:
            self.mesh_item = gl.GLMeshItem(vertexes=transformed_vertices, faces=self.wireframe.triangles(),
                                           smooth=True, drawEdges=False)
            self.mesh_item.setColor(self.current_color)
            self.edge_item = gl.GLLinePlotItem(mode='lines', antialias=True, glOptions='opaque')
            self.vertex_item = gl.GLScatterPlotItem(pxMode=True, glOptions='opaque')
        else:
            self.mesh_item.setMeshData(vertexes=transformed_vertices, faces=self.wireframe.triangles(),
                                       color=self.current_color)
        self.set_item_geometry(transformed_vertices, style)

        has_faces = self.wireframe.faces is not None and len(self.wireframe.faces) > 0
        self.mesh_item.setVisible(style["show_faces"] and has_faces)
        self.edge_item.setVisible(style["show_edges"] and has_faces)
        self.vertex_item.setVisible(style["show_vertices"] or not has_faces)  # a point cloud is all there is to draw

    def set_item_geometry(self, vertices, style):
        """Move the edge and vertex items to the transformed vertices, with the current colours and sizes."""
        if not hasattr(self, "_edges"):
            self._edges = np.array(edges_from_faces(self.wireframe.faces), dtype=int).reshape(-1, 2)
        segments = vertices[self._edges.ravel()] if len(self._edges) else np.zeros((2, 3))
        self.edge_item.setData(pos=segments, color=style["edge_color"], width=style["edge_width"])
        self.vertex_item.setData(pos=vertices, color=style["vertex_color"], size=style["vertex_size"])

    def get_center(self):
        return np.array(self.center) + np.array(self.position)

    def calculate_center(self):
        return np.mean(self.wireframe.vertices, axis=0)

    def get_transformed_vertices(self):
        """Scale and rotate about the centre, then translate (scene_math.transform_vertices)."""
        return transform_vertices(self.wireframe.vertices, self.center, self.scale, self.rotation, self.position)

    def update_center(self):
        self.center = self.calculate_center()


    def apply_transformation(self):
        if self.mesh_item:
            translated_vertices = self.get_transformed_vertices()

            self.mesh_item.setMeshData(vertexes=translated_vertices, faces=self.wireframe.triangles(),
                                       color=self.current_color)
            if self.edge_item is not None:
                self.set_item_geometry(translated_vertices, getattr(self, "style", None) or default_style())

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
            # integrate, simple gravity along -z (the camera's up axis), bounce at z = 0: scene_math.physics_step
            physics_step(obj.position, obj.velocity, obj.rotation, obj.angular_velocity, dt)

    def apply_transformations(self):
        for obj in self.objects:
            obj.apply_transformation()
