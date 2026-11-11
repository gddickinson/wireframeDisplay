"""Regression test: the shape loader's V resolution is not used as the trefoil knot's tube radius."""
import numpy as np

from wireframe import Wireframe


def test_trefoil_from_loader_has_thin_tube():
    w = Wireframe.create_parametric_shape("Trefoil Knot", 30, 30)
    ref = Wireframe.create_trefoil_knot(30)  # default tube_radius=0.3
    assert np.abs(w.vertices).max() < 3.5  # the knot itself reaches radius 3; was 33 with a tube of radius 30
    assert np.allclose(w.vertices, ref.vertices)
