"""The basic solids of the shape loader (Cube ... Prism).

BasicShapesMixin is mixed into wireframe.Wireframe; every method is a classmethod (or staticmethod) that builds and returns
a Wireframe through `cls(vertices, faces)`. Qt-free (split out of wireframe.py, 2026-11-11, unchanged code).
"""
import numpy as np
from math import pi, sin, cos, sqrt


class BasicShapesMixin:
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
