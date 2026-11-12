"""Wireframe: vertices (float32) and polygon faces, plus the shape loader's entry points.

The generators live in mixins: shapes_basic.BasicShapesMixin, shapes_parametric.ParametricShapesMixin and
shapes_fractal.FractalShapesMixin; this module keeps construction, drawing (triangles, create_mesh_item: pyqtgraph is
imported lazily, so the module is Qt-free), transforms, OBJ / JSON files, text and the loader dispatchers.
"""
import numpy as np
import json
from letter_definitions import ALL_CHARACTERS, GAP, SPACE
from mesh_utils import face_array, triangulate
from shapes_basic import BasicShapesMixin
from shapes_fractal import FractalShapesMixin
from shapes_parametric import ParametricShapesMixin

class Wireframe(BasicShapesMixin, ParametricShapesMixin, FractalShapesMixin):
    def __init__(self, vertices, faces=None, edges=None):
        self.original_vertices = np.array(vertices, dtype=np.float32)
        self.vertices = self.original_vertices.copy()
        # Polygon faces of one size are kept as (N, k); mixed sizes are fan-triangulated; negative indices count
        # from the end of the vertex list.
        self.faces = face_array(faces, len(self.original_vertices))
        self.edges = np.array(edges, dtype=np.int32) if edges is not None else None
        self.mesh_item = None

    def triangles(self):
        """Faces as (M, 3) triangles, as OpenGL draws them (quads and other polygons are fan-triangulated)."""
        if self.faces is None:
            return None
        if self.faces.ndim == 2 and self.faces.shape[1] == 3:
            return self.faces
        return triangulate(self.faces)

    def create_mesh_item(self, draw_faces=True, draw_edges=True):
        import pyqtgraph.opengl as gl  # imported here so the shape code works without Qt (web API, tests)
        tris = self.triangles()
        colors = np.ones((len(tris), 4), dtype=np.float32) if tris is not None else None
        self.mesh_item = gl.GLMeshItem(
            vertexes=self.vertices,
            faces=tris,
            faceColors=colors,
            drawEdges=draw_edges,
            drawFaces=draw_faces,
            smooth=False
        )
        return self.mesh_item

    def translate(self, dx, dy, dz):
        translation = np.array([dx, dy, dz], dtype=np.float32)
        self.vertices += translation

    def scale(self, sx, sy, sz):
        scaling = np.array([sx, sy, sz], dtype=np.float32)
        self.vertices *= scaling

    @classmethod
    def load_from_obj(cls, filename):
        vertices = []
        faces = []
        with open(filename, 'r') as file:
            for line in file:
                if line.startswith('v '):
                    vertices.append([float(x) for x in line.split()[1:4]])
                elif line.startswith('f '):
                    faces.append([int(x.split('/')[0]) - 1 for x in line.split()[1:]])
        return cls(np.array(vertices, dtype=np.float32), faces)

    def save_to_obj(self, filename):
        with open(filename, 'w') as file:
            for v in self.vertices:
                file.write(f"v {v[0]} {v[1]} {v[2]}\n")
            for f in self.faces:
                file.write("f " + " ".join(str(int(i) + 1) for i in f) + "\n")

    def save_to_json(self, filename):
        data = {
            'vertices': self.vertices.tolist(),
            'faces': self.faces.tolist() if self.faces is not None else None,
            'edges': self.edges.tolist() if self.edges is not None else None
        }
        with open(filename, 'w') as file:
            json.dump(data, file)

    @classmethod
    def load_from_json(cls, filename):
        with open(filename, 'r') as file:
            data = json.load(file)
        return cls(
            np.array(data['vertices'], dtype=np.float32),
            np.array(data['faces'], dtype=np.int32) if data['faces'] else None,
            np.array(data['edges'], dtype=np.int32) if data['edges'] else None
        )

    @classmethod
    def create_character(cls, char):
        char = char.upper()
        if char not in ALL_CHARACTERS:
            raise ValueError(f"Character '{char}' is not defined")

        vertices, faces = ALL_CHARACTERS[char]
        return cls(vertices, faces)

    @classmethod
    def create_text(cls, text, spacing=GAP):
        """Glyphs from letter_definitions placed left to right: each advances by its width plus `spacing`,
        a space by SPACE; undefined characters are skipped."""
        text = text.upper()
        char_shapes = []
        offset = 0.0
        for char in text:
            if char == ' ':
                offset += SPACE
                continue
            if char in ALL_CHARACTERS:
                char_shape = cls.create_character(char)
                x0 = float(char_shape.vertices[:, 0].min())
                width = float(char_shape.vertices[:, 0].max()) - x0
                char_shape.translate(offset - x0, 0, 0)
                char_shapes.append(char_shape)
                offset += width + spacing

        if not char_shapes:
            raise ValueError(f"No supported characters in {text!r}; defined: {' '.join(sorted(ALL_CHARACTERS))}")

        # Combine all character shapes into a single wireframe
        all_vertices = []
        all_faces = []
        vertex_count = 0
        for shape in char_shapes:
            all_vertices.extend(shape.vertices)
            all_faces.extend([f + vertex_count for f in shape.faces])
            vertex_count += len(shape.vertices)

        return cls(np.array(all_vertices), np.array(all_faces))

    @classmethod
    def create_basic_shape(cls, shape_type):
        if shape_type == 'Cube':
            return cls.create_cube()
        elif shape_type == 'Sphere':
            return cls.create_sphere()
        elif shape_type == 'Tetrahedron':
            return cls.create_tetrahedron()
        elif shape_type == 'Octahedron':
            return cls.create_octahedron()
        elif shape_type == 'Icosahedron':
            return cls.create_icosahedron()
        elif shape_type == 'Dodecahedron':
            return cls.create_dodecahedron()
        elif shape_type == 'Torus':
            return cls.create_torus()
        elif shape_type == 'Cylinder':
            return cls.create_cylinder()
        elif shape_type == 'Cone':
            return cls.create_cone()
        elif shape_type == 'Pyramid':
            return cls.create_pyramid()
        elif shape_type == 'Prism':
            return cls.create_prism()
        else:
            raise ValueError(f"Unknown basic shape type: {shape_type}")

    @classmethod
    def create_parametric_shape(cls, shape_type, u_res, v_res):
        if shape_type == 'Mobius Strip':
            return cls.create_mobius_strip(u_res, v_res)
        elif shape_type == 'Klein Bottle':
            return cls.create_klein_bottle(u_res, v_res)
        elif shape_type == 'Trefoil Knot':
            return cls.create_trefoil_knot(u_res)  # v_res does not apply: the tube keeps its default radius
        elif shape_type == 'Helicoid':
            return cls.create_helicoid(u_res, v_res)
        elif shape_type == 'Catenoid':
            return cls.create_catenoid(u_res, v_res)
        elif shape_type == 'Sine Surface':
            return cls.create_sine_surface(u_res, v_res)
        elif shape_type == 'Gyroid':
            return cls.create_gyroid(u_res, v_res)
        else:
            raise ValueError(f"Unknown parametric shape type: {shape_type}")

    @classmethod
    def create_fractal(cls, fractal_type, iterations, size):
        if fractal_type == 'Sierpinski Triangle':
            return cls.create_sierpinski_triangle(iterations, size)
        elif fractal_type == 'Koch Snowflake':
            return cls.create_koch_snowflake(iterations, size)
        elif fractal_type == 'Menger Sponge':
            return cls.create_menger_sponge(iterations, size)
        elif fractal_type == 'Apollonian Gasket':
            return cls.create_apollonian_gasket(iterations, size)
        elif fractal_type == 'Jerusalem Cube':
            return cls.create_jerusalem_cube(iterations, size)
        elif fractal_type == 'Sierpinski Tetrahedron':
            return cls.create_sierpinski_tetrahedron(iterations, size)
        elif fractal_type == 'Pythagoras Tree 3D':
            return cls.create_pythagoras_tree_3d(iterations, size)
        else:
            raise ValueError(f"Unknown fractal type: {fractal_type}")

    @classmethod
    def load_mri(cls, filename, level=None, max_size=128):
        """Isosurface of a NIfTI volume (.nii / .nii.gz) in scanner (world) millimetres, via marching cubes.

        4D files use their first volume. level is the intensity threshold (default: Otsu's threshold of the volume);
        volumes larger than max_size voxels along an axis are sampled with a coarser marching-cubes step.
        """
        import nibabel as nib
        from skimage import filters, measure
        img = nib.load(str(filename))
        data = np.asarray(img.dataobj, dtype=np.float32)
        if data.ndim == 4:
            data = data[..., 0]
        if data.ndim != 3:
            raise ValueError(f"expected a 3D or 4D NIfTI volume, got shape {data.shape}")
        if level is None:
            level = float(filters.threshold_otsu(data))
        step = max(1, int(np.ceil(max(data.shape) / max_size)))
        verts, faces, _, _ = measure.marching_cubes(data, level, step_size=step)
        return cls(nib.affines.apply_affine(img.affine, verts), faces)
