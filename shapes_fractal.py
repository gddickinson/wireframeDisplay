"""Fractal patterns (Sierpinski triangle ... 3D Pythagoras tree).

FractalShapesMixin is mixed into wireframe.Wireframe; every method is a classmethod (or staticmethod) that builds and returns
a Wireframe through `cls(vertices, faces)`. Qt-free (split out of wireframe.py, 2026-11-11, unchanged code).
"""
import numpy as np
from math import pi, sin, cos, sqrt


class FractalShapesMixin:
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
                    d = (c + e) / 2 + v * sqrt(3) / 2  # apex of an equilateral bump on the middle third
                    new_points.extend([a, c, d, e])
                new_points.append(points[-1])
                return koch(new_points, n-1)

        # Equilateral triangle inscribed in a circle of radius `size`, traversed clockwise so the bumps (on the left
        # of each segment) point outwards; the last point closes the loop.
        initial_points = np.array([
            [size, 0, 0],
            [size * cos(4*pi/3), size * sin(4*pi/3), 0],
            [size * cos(2*pi/3), size * sin(2*pi/3), 0],
            [size, 0, 0]
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
            # Jerusalem cube: 8 corner cubes of side k*s and 12 edge cubes of side k^2*s between them,
            # k = sqrt(2) - 1 (so 2k + k^2 = 1), leaving a cross-shaped hole through each face.
            x, y, z, s = cube
            a = s * (sqrt(2) - 1)
            b = s * (sqrt(2) - 1) ** 2
            corners = [(x + i * (s - a), y + j * (s - a), z + k * (s - a), a)
                       for i in (0, 1) for j in (0, 1) for k in (0, 1)]
            edges = [(x + a, y + j * (s - b), z + k * (s - b), b) for j in (0, 1) for k in (0, 1)]
            edges += [(x + i * (s - b), y + a, z + k * (s - b), b) for i in (0, 1) for k in (0, 1)]
            edges += [(x + i * (s - b), y + j * (s - b), z + a, b) for i in (0, 1) for j in (0, 1)]
            return corners + edges

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
