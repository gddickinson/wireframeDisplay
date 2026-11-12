import numpy as np
from math import pi, sin, cos, sqrt
import json
from letter_definitions import ALL_CHARACTERS, GAP, SPACE
from mesh_utils import face_array, triangulate

class Wireframe:
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
    def create_cube(cls):
        vertices = np.array([
            [1, 1, 1], [-1, 1, 1], [-1, -1, 1], [1, -1, 1],
            [1, 1, -1], [-1, 1, -1], [-1, -1, -1], [1, -1, -1]
        ], dtype=np.float32)
        faces = np.array([
            [0, 1, 2], [0, 2, 3], [0, 3, 7], [0, 7, 4], [0, 4, 5], [0, 5, 1],
            [6, 2, 1], [6, 1, 5], [6, 5, 4], [6, 4, 7], [6, 7, 3], [6, 3, 2]
        ], dtype=np.int32)
        return cls(vertices, faces)

    @classmethod
    def create_sphere(cls, rows=20, cols=20):
        vertices = []
        for i in range(rows + 1):
            theta = i * pi / rows
            for j in range(cols):
                phi = j * 2 * pi / cols
                x = sin(theta) * cos(phi)
                y = sin(theta) * sin(phi)
                z = cos(theta)
                vertices.append([x, y, z])

        vertices = np.array(vertices, dtype=np.float32)

        faces = []
        for i in range(rows):
            for j in range(cols):
                p1 = i * cols + j
                p2 = p1 + 1 if j < cols - 1 else i * cols
                p3 = (i + 1) * cols + j
                p4 = p3 + 1 if j < cols - 1 else (i + 1) * cols
                faces.append([p1, p2, p3])
                faces.append([p2, p4, p3])

        faces = np.array(faces, dtype=np.int32)
        return cls(vertices, faces)

    @classmethod
    def create_tetrahedron(cls):
        vertices = np.array([
            [1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]
        ], dtype=np.float32)
        faces = np.array([
            [0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]
        ], dtype=np.int32)
        return cls(vertices, faces)

    @classmethod
    def create_octahedron(cls):
        vertices = np.array([
            [1, 0, 0], [-1, 0, 0], [0, 1, 0],
            [0, -1, 0], [0, 0, 1], [0, 0, -1]
        ], dtype=np.float32)
        faces = np.array([
            [0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2],
            [1, 2, 5], [1, 5, 3], [1, 3, 4], [1, 4, 2]
        ], dtype=np.int32)
        return cls(vertices, faces)

    @classmethod
    def create_icosahedron(cls):
        phi = (1 + sqrt(5)) / 2
        vertices = np.array([
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
        ], dtype=np.float32)
        faces = np.array([
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ], dtype=np.int32)
        return cls(vertices, faces)

    @classmethod
    def create_torus(cls, R=1, r=0.3, steps=20, rings=20):
        vertices = []
        for i in range(rings):
            for j in range(steps):
                theta = 2 * pi * i / rings
                phi = 2 * pi * j / steps
                x = (R + r * cos(phi)) * cos(theta)
                y = (R + r * cos(phi)) * sin(theta)
                z = r * sin(phi)
                vertices.append([x, y, z])

        vertices = np.array(vertices, dtype=np.float32)

        faces = []
        for i in range(rings):
            for j in range(steps):
                i1, i2 = i, (i + 1) % rings
                j1, j2 = j, (j + 1) % steps
                faces.append([i1 * steps + j1, i1 * steps + j2, i2 * steps + j2])
                faces.append([i1 * steps + j1, i2 * steps + j2, i2 * steps + j1])

        faces = np.array(faces, dtype=np.int32)
        return cls(vertices, faces)

    @classmethod
    def create_cylinder(cls, radius=1, height=2, segments=20):
        vertices = []
        for i in range(segments):
            theta = 2 * pi * i / segments
            vertices.append([radius * cos(theta), radius * sin(theta), -height/2])
            vertices.append([radius * cos(theta), radius * sin(theta), height/2])
        vertices.append([0, 0, -height/2])  # Bottom center
        vertices.append([0, 0, height/2])   # Top center

        vertices = np.array(vertices, dtype=np.float32)

        faces = []
        for i in range(segments):
            i1, i2 = i * 2, (i * 2 + 2) % (segments * 2)
            faces.append([i1, i2, i2 + 1])
            faces.append([i1, i2 + 1, i1 + 1])
            faces.append([i1, -2, i2])  # Bottom face
            faces.append([i1 + 1, i2 + 1, -1])  # Top face

        faces = np.array(faces, dtype=np.int32)
        return cls(vertices, faces)

    @classmethod
    def create_cone(cls, radius=1, height=2, segments=20):
        vertices = [[0, 0, 0]]  # Base center
        for i in range(segments):
            theta = 2 * pi * i / segments
            vertices.append([radius * cos(theta), radius * sin(theta), 0])
        vertices.append([0, 0, height])  # Apex
        vertices = np.array(vertices, dtype=np.float32)

        faces = []
        for i in range(1, segments + 1):
            faces.append([0, i, i % segments + 1])  # Base faces
            faces.append([i, segments + 1, i % segments + 1])  # Side faces

        faces = np.array(faces, dtype=np.int32)
        return cls(vertices, faces)

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
    def create_sierpinski_triangle(cls, iterations=5, size=1.0):
        def sierpinski(points, n):
            if n == 0:
                return [points]
            else:
                p1, p2, p3 = points
                p12 = (p1 + p2) / 2
                p23 = (p2 + p3) / 2
                p31 = (p3 + p1) / 2
                return (sierpinski([p1, p12, p31], n-1) +
                        sierpinski([p2, p12, p23], n-1) +
                        sierpinski([p3, p23, p31], n-1))

        initial_points = np.array([[0, 0, 0], [size, 0, 0], [size/2, size*sqrt(3)/2, 0]])
        triangles = sierpinski(initial_points, iterations)

        vertices = np.array([point for triangle in triangles for point in triangle])
        faces = np.array([[i*3, i*3+1, i*3+2] for i in range(len(triangles))])

        return cls(vertices, faces)

    @classmethod
    def create_koch_snowflake(cls, iterations=4, size=1.0):
        def koch(points, n):
            if n == 0:
                return points
            else:
                new_points = []
                for i in range(len(points) - 1):
                    a, b = points[i], points[i+1]
                    d = (b - a) / 3
                    c = a + d
                    e = b - d
                    v = np.array([-d[1], d[0], 0])  # Perpendicular vector
                    d = c + v * sqrt(3) / 3
                    new_points.extend([a, c, d, e])
                new_points.append(points[-1])
                return koch(new_points, n-1)

        initial_points = np.array([
            [0, 0, 0],
            [size * cos(2*pi/3), size * sin(2*pi/3), 0],
            [size * cos(4*pi/3), size * sin(4*pi/3), 0],
            [0, 0, 0]
        ])

        points = koch(initial_points, iterations)
        vertices = np.array(points)
        faces = np.array([[i for i in range(len(vertices) - 1)]])

        return cls(vertices, faces)

    @classmethod
    def create_menger_sponge(cls, iterations=3, size=1.0):
        def subdivide_cube(cube):
            new_cubes = []
            for x in [-1, 0, 1]:
                for y in [-1, 0, 1]:
                    for z in [-1, 0, 1]:
                        if abs(x) + abs(y) + abs(z) > 1:
                            new_cube = cube * (1/3) + np.array([x, y, z]) * (size/3)
                            new_cubes.append(new_cube)
            return new_cubes

        def menger(cubes, n):
            if n == 0:
                return cubes
            else:
                new_cubes = []
                for cube in cubes:
                    new_cubes.extend(subdivide_cube(cube))
                return menger(new_cubes, n-1)

        initial_cube = np.array([
            [0, 0, 0], [size, 0, 0], [0, size, 0], [size, size, 0],
            [0, 0, size], [size, 0, size], [0, size, size], [size, size, size]
        ])

        cubes = menger([initial_cube], iterations)

        vertices = np.array([v for cube in cubes for v in cube])
        faces = []
        for i in range(0, len(vertices), 8):
            cube_faces = [
                [i, i+1, i+3, i+2], [i+4, i+5, i+7, i+6],
                [i, i+1, i+5, i+4], [i+2, i+3, i+7, i+6],
                [i, i+2, i+6, i+4], [i+1, i+3, i+7, i+5]
            ]
            faces.extend(cube_faces)

        return cls(vertices, np.array(faces))



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

    # Implement methods for each new shape...
    @classmethod
    def create_dodecahedron(cls):
        phi = (1 + sqrt(5)) / 2
        vertices = np.array([
            [-1, -1, -1], [1, -1, -1], [-1, 1, -1], [1, 1, -1],
            [-1, -1, 1], [1, -1, 1], [-1, 1, 1], [1, 1, 1],
            [0, -phi, -1/phi], [0, phi, -1/phi], [0, -phi, 1/phi], [0, phi, 1/phi],
            [-1/phi, 0, -phi], [1/phi, 0, -phi], [-1/phi, 0, phi], [1/phi, 0, phi],
            [-phi, -1/phi, 0], [phi, -1/phi, 0], [-phi, 1/phi, 0], [phi, 1/phi, 0]
        ])
        faces = [  # the 12 pentagons of the convex hull of the 20 vertices above
            [0, 8, 10, 4, 16], [0, 12, 13, 1, 8], [0, 16, 18, 2, 12],
            [1, 13, 3, 19, 17], [1, 17, 5, 10, 8], [2, 9, 3, 13, 12],
            [2, 18, 6, 11, 9], [3, 9, 11, 7, 19], [4, 10, 5, 15, 14],
            [4, 14, 6, 18, 16], [5, 17, 19, 7, 15], [6, 14, 15, 7, 11]
        ]
        return cls(vertices, faces)

    @classmethod
    def create_pyramid(cls, base_size=1, height=1):
        half_size = base_size / 2
        vertices = np.array([
            [-half_size, -half_size, 0], [half_size, -half_size, 0],
            [half_size, half_size, 0], [-half_size, half_size, 0],
            [0, 0, height]
        ])
        faces = [
            [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4],
            [0, 3, 2, 1]
        ]
        return cls(vertices, faces)

    @classmethod
    def create_prism(cls, base_size=1, height=1, n_sides=6):
        angles = np.linspace(0, 2*pi, n_sides, endpoint=False)
        base_vertices = np.column_stack((np.cos(angles), np.sin(angles), np.zeros(n_sides))) * base_size/2
        top_vertices = base_vertices + [0, 0, height]
        vertices = np.vstack((base_vertices, top_vertices))

        faces = []
        for i in range(n_sides):
            faces.append([i, (i+1)%n_sides, n_sides + (i+1)%n_sides, n_sides + i])
        faces.append(list(range(n_sides)))
        faces.append(list(range(n_sides, 2*n_sides)))

        return cls(vertices, faces)

    @classmethod
    def create_mobius_strip(cls, u_res=30, v_res=10):
        u = np.linspace(0, 2*pi, u_res)
        v = np.linspace(-1, 1, v_res)
        u, v = np.meshgrid(u, v)

        x = (1 + v/2 * np.cos(u/2)) * np.cos(u)
        y = (1 + v/2 * np.cos(u/2)) * np.sin(u)
        z = v/2 * np.sin(u/2)

        vertices = np.column_stack((x.flatten(), y.flatten(), z.flatten()))

        faces = []
        for i in range(u_res-1):
            for j in range(v_res-1):
                faces.append([j*u_res + i, j*u_res + i + 1, (j+1)*u_res + i + 1, (j+1)*u_res + i])

        return cls(vertices, faces)

    @classmethod
    def create_klein_bottle(cls, u_res=30, v_res=30):
        u = np.linspace(0, 2*pi, u_res)
        v = np.linspace(0, 2*pi, v_res)
        u, v = np.meshgrid(u, v)

        x = (2.5 + np.cos(u/2) * np.sin(v) - np.sin(u/2) * np.sin(2*v)) * np.cos(u)
        y = (2.5 + np.cos(u/2) * np.sin(v) - np.sin(u/2) * np.sin(2*v)) * np.sin(u)
        z = np.sin(u/2) * np.sin(v) + np.cos(u/2) * np.sin(2*v)

        vertices = np.column_stack((x.flatten(), y.flatten(), z.flatten()))

        faces = []
        for i in range(u_res-1):
            for j in range(v_res-1):
                faces.append([j*u_res + i, j*u_res + i + 1, (j+1)*u_res + i + 1, (j+1)*u_res + i])

        return cls(vertices, faces)

    @classmethod
    def create_trefoil_knot(cls, u_res=100, tube_radius=0.3):
        t = np.linspace(0, 2*pi, u_res, endpoint=False)  # closed loop: ring i joins ring (i + 1) % u_res
        x = (2 + np.cos(3*t)) * np.cos(2*t)
        y = (2 + np.cos(3*t)) * np.sin(2*t)
        z = np.sin(3*t)

        knot_points = np.column_stack((x, y, z))

        def create_circle(center, normal, radius, res=8):
            t = np.linspace(0, 2*pi, res)
            x = radius * np.cos(t)
            y = radius * np.sin(t)
            circle = np.column_stack((x, y, np.zeros_like(x)))

            z_axis = np.array([0, 0, 1])
            normal = normal / np.linalg.norm(normal)  # arccos needs the unit tangent
            rotation_axis = np.cross(z_axis, normal)
            rotation_angle = np.arccos(np.dot(z_axis, normal))
            rotation_matrix = cls.rotation_matrix(rotation_axis, rotation_angle)

            rotated_circle = np.dot(circle, rotation_matrix.T)
            return rotated_circle + center

        vertices = []
        faces = []
        circle_res = 8

        for i in range(u_res):
            center = knot_points[i]
            next_center = knot_points[(i + 1) % u_res]
            normal = next_center - center
            circle = create_circle(center, normal, tube_radius, circle_res)
            vertices.extend(circle)

            for j in range(circle_res):
                next_j = (j + 1) % circle_res
                faces.append([
                    i * circle_res + j,
                    i * circle_res + next_j,
                    ((i + 1) % u_res) * circle_res + next_j,
                    ((i + 1) % u_res) * circle_res + j
                ])

        return cls(vertices, faces)

    @classmethod
    def create_helicoid(cls, u_res=30, v_res=30):
        u = np.linspace(-pi, pi, u_res)
        v = np.linspace(-1, 1, v_res)
        u, v = np.meshgrid(u, v)

        x = v * np.cos(u)
        y = v * np.sin(u)
        z = u

        vertices = np.column_stack((x.flatten(), y.flatten(), z.flatten()))

        faces = []
        for i in range(u_res-1):
            for j in range(v_res-1):
                faces.append([j*u_res + i, j*u_res + i + 1, (j+1)*u_res + i + 1, (j+1)*u_res + i])

        return cls(vertices, faces)

    @classmethod
    def create_catenoid(cls, u_res=30, v_res=30):
        u = np.linspace(-pi, pi, u_res)
        v = np.linspace(-1, 1, v_res)
        u, v = np.meshgrid(u, v)

        x = np.cosh(v) * np.cos(u)
        y = np.cosh(v) * np.sin(u)
        z = v

        vertices = np.column_stack((x.flatten(), y.flatten(), z.flatten()))

        faces = []
        for i in range(u_res-1):
            for j in range(v_res-1):
                faces.append([j*u_res + i, j*u_res + i + 1, (j+1)*u_res + i + 1, (j+1)*u_res + i])

        return cls(vertices, faces)

    @classmethod
    def create_sine_surface(cls, u_res=30, v_res=30):
        u = np.linspace(0, 2*pi, u_res)
        v = np.linspace(0, 2*pi, v_res)
        u, v = np.meshgrid(u, v)

        x = np.sin(u)
        y = np.sin(v)
        z = np.sin(u + v)

        vertices = np.column_stack((x.flatten(), y.flatten(), z.flatten()))

        faces = []
        for i in range(u_res-1):
            for j in range(v_res-1):
                faces.append([j*u_res + i, j*u_res + i + 1, (j+1)*u_res + i + 1, (j+1)*u_res + i])

        return cls(vertices, faces)

    @classmethod
    def create_gyroid(cls, u_res=30, v_res=30, w_res=30):
        x = np.linspace(-pi, pi, u_res)
        y = np.linspace(-pi, pi, v_res)
        z = np.linspace(-pi, pi, w_res)
        x, y, z = np.meshgrid(x, y, z)

        values = np.sin(x) * np.cos(y) + np.sin(y) * np.cos(z) + np.sin(z) * np.cos(x)
        vertices, faces, _, _ = cls.marching_cubes(values, 0)

        return cls(vertices, faces)

    @classmethod
    def create_apollonian_gasket(cls, iterations=3, size=1):
        def circle_inversion(circle, point):
            cx, cy, cr = circle
            px, py = point
            dx, dy = px - cx, py - cy
            factor = cr**2 / (dx**2 + dy**2)
            return cx + dx * factor, cy + dy * factor

        def get_inner_circle(c1, c2, c3):
            x1, y1, r1 = c1
            x2, y2, r2 = c2
            x3, y3, r3 = c3

            a = 1/r1 + 1/r2 + 1/r3
            b = x1/r1 + x2/r2 + x3/r3
            c = y1/r1 + y2/r2 + y3/r3
            d = (x1**2 + y1**2 - r1**2)/r1 + (x2**2 + y2**2 - r2**2)/r2 + (x3**2 + y3**2 - r3**2)/r3

            x = b / (2*a)
            y = c / (2*a)
            r = sqrt(x**2 + y**2 - d/a)

            return (x, y, r)

        def generate_circles(c1, c2, c3, depth):
            if depth == 0:
                return [c1, c2, c3]

            circles = [c1, c2, c3]
            inner = get_inner_circle(c1, c2, c3)
            circles.append(inner)

            if depth > 1:
                circles.extend(generate_circles(c1, c2, inner, depth-1))
                circles.extend(generate_circles(c1, c3, inner, depth-1))
                circles.extend(generate_circles(c2, c3, inner, depth-1))

            return circles

        initial_circles = [
            (0, -1/sqrt(3), 1/sqrt(3)),
            (-0.5, 1/(2*sqrt(3)), 1/sqrt(3)),
            (0.5, 1/(2*sqrt(3)), 1/sqrt(3))
        ]

        circles = generate_circles(*initial_circles, iterations)

        vertices = []
        faces = []
        for circle in circles:
            cx, cy, cr = circle
            n_points = max(8, int(32 * cr))
            for i in range(n_points):
                angle = 2 * pi * i / n_points
                x = cx + cr * cos(angle)
                y = cy + cr * sin(angle)
                vertices.append([x*size, y*size, 0])

        return cls(vertices, faces)

    @classmethod
    def create_jerusalem_cube(cls, iterations=3, size=1):
        def subdivide(cube):
            x, y, z, s = cube
            s = s / 3
            return [
                (x, y, z, s),
                (x + 2*s, y, z, s),
                (x, y + 2*s, z, s),
                (x + 2*s, y + 2*s, z, s),
                (x, y, z + 2*s, s),
                (x + 2*s, y, z + 2*s, s),
                (x, y + 2*s, z + 2*s, s),
                (x + 2*s, y + 2*s, z + 2*s, s)
            ]

        def generate_cubes(iterations):
            cubes = [(0, 0, 0, size)]
            for _ in range(iterations):
                new_cubes = []
                for cube in cubes:
                    new_cubes.extend(subdivide(cube))
                cubes = new_cubes
            return cubes

        cubes = generate_cubes(iterations)
        vertices = []
        faces = []
        for i, (x, y, z, s) in enumerate(cubes):
            cube_vertices = [
                [x, y, z], [x+s, y, z], [x+s, y+s, z], [x, y+s, z],
                [x, y, z+s], [x+s, y, z+s], [x+s, y+s, z+s], [x, y+s, z+s]
            ]
            base_index = len(vertices)
            vertices.extend(cube_vertices)
            cube_faces = [
                [0, 1, 2, 3], [4, 5, 6, 7], [0, 4, 7, 3],
                [1, 5, 6, 2], [0, 1, 5, 4], [3, 2, 6, 7]
            ]
            faces.extend([[f + base_index for f in face] for face in cube_faces])

        return cls(vertices, faces)

    @classmethod
    def create_sierpinski_tetrahedron(cls, iterations=4, size=1):
        def midpoint(p1, p2):
            return [(p1[i] + p2[i]) / 2 for i in range(3)]

        def subdivide(tetrahedron):
            a, b, c, d = tetrahedron
            ab, ac, ad = midpoint(a, b), midpoint(a, c), midpoint(a, d)
            bc, bd = midpoint(b, c), midpoint(b, d)
            cd = midpoint(c, d)
            return [
                (a, ab, ac, ad),
                (ab, b, bc, bd),
                (ac, bc, c, cd),
                (ad, bd, cd, d)
            ]

        def generate_tetrahedra(iterations):
            initial_tetrahedron = [
                [0, 0, 0],
                [size, 0, 0],
                [size/2, size*sqrt(3)/2, 0],
                [size/2, size*sqrt(3)/6, size*sqrt(6)/3]
            ]
            tetrahedra = [initial_tetrahedron]
            for _ in range(iterations):
                new_tetrahedra = []
                for tetra in tetrahedra:
                    new_tetrahedra.extend(subdivide(tetra))
                tetrahedra = new_tetrahedra
            return tetrahedra

        tetrahedra = generate_tetrahedra(iterations)
        vertices = []
        faces = []
        for i, tetra in enumerate(tetrahedra):
            base_index = len(vertices)
            vertices.extend(tetra)
            tetra_faces = [
                [0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]
            ]
            faces.extend([[f + base_index for f in face] for face in tetra_faces])

        return cls(vertices, faces)

    @classmethod
    def create_pythagoras_tree_3d(cls, iterations=5, size=1, angle=pi/4):
        def create_cube(pos, size):
            x, y, z = pos
            return [
                [x, y, z], [x+size, y, z], [x+size, y+size, z], [x, y+size, z],
                [x, y, z+size], [x+size, y, z+size], [x+size, y+size, z+size], [x, y+size, z+size]
            ]

        def generate_tree(pos, size, angle, iteration):
            if iteration == 0:
                return []

            cubes = [create_cube(pos, size)]
            x, y, z = pos

            # Right branch
            new_size = size * cos(angle)
            new_x = x + size - new_size * sin(angle)
            new_y = y + size + new_size * cos(angle)
            new_z = z + size
            cubes.extend(generate_tree((new_x, new_y, new_z), new_size, angle, iteration-1))

            # Left branch
            new_size = size * sin(angle)
            new_x = x + size * cos(angle)
            new_y = y + size
            new_z = z + size + new_size
            cubes.extend(generate_tree((new_x, new_y, new_z), new_size, angle, iteration-1))

            return cubes

        cubes = generate_tree((0, 0, 0), size, angle, iterations)
        vertices = []
        faces = []
        for i, cube in enumerate(cubes):
            base_index = len(vertices)
            vertices.extend(cube)
            cube_faces = [
                [0, 1, 2, 3], [4, 5, 6, 7], [0, 4, 7, 3],
                [1, 5, 6, 2], [0, 1, 5, 4], [3, 2, 6, 7]
            ]
            faces.extend([[f + base_index for f in face] for face in cube_faces])

        return cls(vertices, faces)

    @staticmethod
    def marching_cubes(scalar_field, iso_level):
        from skimage import measure
        verts, faces, normals, values = measure.marching_cubes(scalar_field, iso_level)
        return verts, faces, normals, values

    @staticmethod
    def rotation_matrix(axis, theta):
        """
        Return the rotation matrix associated with counterclockwise rotation about
        the given axis by theta radians.
        """
        axis = np.asarray(axis)
        axis = axis / sqrt(np.dot(axis, axis))
        a = cos(theta / 2.0)
        b, c, d = -axis * sin(theta / 2.0)
        aa, bb, cc, dd = a * a, b * b, c * c, d * d
        bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
        return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                         [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                         [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])
