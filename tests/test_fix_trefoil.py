"""Regression test: the shape loader's V resolution is not used as the trefoil knot's tube radius."""
import numpy as np

from wireframe import Wireframe


def test_trefoil_from_loader_has_thin_tube():
    w = Wireframe.create_parametric_shape("Trefoil Knot", 30, 30)
    ref = Wireframe.create_trefoil_knot(30)  # default tube_radius=0.3
    assert np.abs(w.vertices).max() < 3.5  # the knot itself reaches radius 3; was 33 with a tube of radius 30
    assert np.allclose(w.vertices, ref.vertices)


def test_trefoil_tube_is_valid_at_every_loader_resolution():
    for u in range(10, 101, 3):  # the loader's U range is 10-100; 10-18 used to give NaN vertices
        w = Wireframe.create_trefoil_knot(u)
        assert np.isfinite(w.vertices).all(), u
        rings = w.vertices.reshape(u, 8, 3)
        centres = rings.mean(axis=1)
        assert len(np.unique(centres.round(5), axis=0)) == u, u  # the last ring no longer repeats the first


def test_trefoil_rings_are_perpendicular_to_the_knot():
    u = 60
    w = Wireframe.create_trefoil_knot(u)
    rings = w.vertices.reshape(u, 8, 3).astype(float)
    t = np.linspace(0, 2 * np.pi, u, endpoint=False)
    knot = np.c_[(2 + np.cos(3 * t)) * np.cos(2 * t), (2 + np.cos(3 * t)) * np.sin(2 * t), np.sin(3 * t)]
    tangent = np.roll(knot, -1, axis=0) - knot
    tangent /= np.linalg.norm(tangent, axis=1, keepdims=True)
    radial = rings - knot[:, None, :]
    assert np.allclose(np.linalg.norm(radial, axis=2), 0.3, atol=1e-5)
    assert np.abs(np.einsum("rpk,rk->rp", radial, tangent)).max() < 1e-5
