"""Parametric surfaces (Mobius strip ... Gyroid) and their helpers.

ParametricShapesMixin is mixed into wireframe.Wireframe; every method is a classmethod (or staticmethod) that builds and returns
a Wireframe through `cls(vertices, faces)`. Qt-free (split out of wireframe.py, 2026-11-11, unchanged code).
"""
import numpy as np
from math import pi, sin, cos, sqrt


class ParametricShapesMixin:
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
        x, y, z = np.meshgrid(x, y, z, indexing='ij')  # array axes 0, 1, 2 = x, y, z

        values = np.sin(x) * np.cos(y) + np.sin(y) * np.cos(z) + np.sin(z) * np.cos(x)
        spacing = tuple(2 * pi / (n - 1) for n in (u_res, v_res, w_res))
        vertices, faces, _, _ = cls.marching_cubes(values, 0, spacing)
        vertices = vertices - pi  # voxel positions -> world coordinates in [-pi, pi]

        return cls(vertices, faces)

    @staticmethod
    def marching_cubes(scalar_field, iso_level, spacing=(1.0, 1.0, 1.0)):
        from skimage import measure
        verts, faces, normals, values = measure.marching_cubes(scalar_field, iso_level, spacing=spacing)
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
