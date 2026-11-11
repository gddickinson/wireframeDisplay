"""Regression tests: polygon faces (quads, pentagons, mixed) load, draw as triangles and survive OBJ save/load."""
import numpy as np
import pytest

from wireframe import Wireframe


@pytest.mark.parametrize("name", ["Pyramid", "Prism"])
def test_mixed_polygon_shapes_build(name):
    w = Wireframe.create_basic_shape(name)  # used to raise "inhomogeneous shape" ValueError
    assert len(w.vertices) and len(w.faces)
    assert w.triangles().shape[1] == 3


def test_cylinder_faces_have_no_negative_indices():
    w = Wireframe.create_cylinder(segments=20)
    assert w.faces.min() >= 0 and w.faces.max() == len(w.vertices) - 1  # -2/-1 meant bottom/top centre


def test_quads_are_triangulated_for_drawing():
    w = Wireframe.create_mobius_strip(30, 10)
    assert w.faces.shape[1] == 4
    tri = w.triangles()
    assert tri.shape == (2 * len(w.faces), 3)
    assert set(np.unique(tri)) == set(np.unique(w.faces))


def test_mesh_item_gets_triangles():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])  # noqa: F841 (kept alive for the test)
    w = Wireframe.create_dodecahedron()
    item = w.create_mesh_item()
    assert item.opts["meshdata"].faces().shape == (36, 3)


def test_obj_round_trip_keeps_polygons(tmp_path):
    w = Wireframe.create_prism()  # 6 quads + 2 hexagons
    p = tmp_path / "prism.obj"
    w.save_to_obj(p)
    lines = [ln for ln in p.read_text().splitlines() if ln.startswith("f ")]
    assert len(lines) == len(w.faces) and all(len(ln.split()) - 1 == 3 for ln in lines)
    q = Wireframe.create_mobius_strip(8, 4)
    q.save_to_obj(tmp_path / "m.obj")
    back = Wireframe.load_from_obj(tmp_path / "m.obj")
    assert np.array_equal(back.faces, q.faces)
    assert np.allclose(back.vertices, q.vertices, atol=1e-6)
