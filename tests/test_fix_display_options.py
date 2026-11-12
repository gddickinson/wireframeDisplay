"""Regression tests: every Display Options setting changes the GL items (desktop viewer, offscreen Qt)."""
import numpy as np
import pytest

pytest.importorskip("PyQt5")
pytest.importorskip("pyqtgraph")
from PyQt5.QtGui import QColor  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

import wireframe_viewer as wv  # noqa: E402

QAPP = QApplication.instance() or QApplication([])


@pytest.fixture
def viewer():
    v = wv.WireframeViewer()
    v.animation_timer.stop()
    v.on_shape_loaded(("basic", "Dodecahedron"))
    return v


def rgba(c):
    return tuple(round(float(x), 3) for x in c)


def test_edges_and_vertices_are_gl_items(viewer):
    obj, d = viewer.scene.objects[0], viewer.display_options
    assert obj.edge_item is not None and obj.vertex_item is not None  # used to be always None
    assert obj.edge_item in viewer.view.items and obj.vertex_item in viewer.view.items
    assert len(obj.edge_item.pos) == 2 * 30  # 30 dodecahedron edges as line segments
    assert obj.edge_item.visible() and not obj.vertex_item.visible()  # defaults: edges on, vertices off
    d.show_edges.setChecked(False)
    d.show_vertices.setChecked(True)
    assert not obj.edge_item.visible() and obj.vertex_item.visible()
    d.show_faces.setChecked(False)
    assert not obj.mesh_item.visible()


def test_colours_widths_and_sizes(viewer):
    obj, d = viewer.scene.objects[0], viewer.display_options
    d.face_color_btn.setColor(QColor(10, 200, 30))
    d.edge_color_btn.setColor(QColor(255, 255, 0))
    d.vertex_color_btn.setColor(QColor(0, 0, 255))
    viewer.update_display_options()
    assert rgba(obj.mesh_item.opts["color"]) == rgba((10 / 255, 200 / 255, 30 / 255, 1))
    assert rgba(obj.edge_item.color) == (1, 1, 0, 1)
    assert rgba(obj.vertex_item.color) == (0, 0, 1, 1)
    d.edge_width.setValue(4)
    d.vertex_size.setValue(12)
    assert obj.edge_item.width == 4 and obj.vertex_item.size == 12


def test_items_follow_the_object(viewer):
    obj = viewer.scene.objects[0]
    obj.translate(0, 0, 2.5)
    viewer.update_display()
    assert np.isclose(obj.vertex_item.pos[:, 2].mean(), obj.get_transformed_vertices()[:, 2].mean())
    assert np.isclose(obj.edge_item.pos[:, 2].min(), obj.get_transformed_vertices()[:, 2].min())


def test_faceless_shape_shows_vertices(viewer):
    viewer.on_shape_loaded(("fractal", ("Apollonian Gasket", 2, 1.0)))
    obj = viewer.scene.objects[-1]
    assert obj.vertex_item.visible()  # no faces: points are all there is to draw (as in the web viewer)
