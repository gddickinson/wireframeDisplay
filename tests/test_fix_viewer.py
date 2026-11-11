"""Regression tests for the desktop viewer (offscreen Qt): animation, bad text, open/save, mouse picking."""
import numpy as np
import pytest

pytest.importorskip("PyQt5")
pytest.importorskip("pyqtgraph")
from PyQt5.QtCore import QPointF  # noqa: E402
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox  # noqa: E402

import wireframe_viewer as wv  # noqa: E402
from wireframe import Wireframe  # noqa: E402


QAPP = QApplication.instance() or QApplication([])  # keep a reference: a collected QApplication aborts Qt


@pytest.fixture
def viewer(monkeypatch):
    msgs = []
    for kind in ("critical", "warning", "information"):
        monkeypatch.setattr(QMessageBox, kind, lambda *a, kind=kind, **k: msgs.append((kind, a[2])))
    v = wv.WireframeViewer()
    v.animation_timer.stop()
    v.msgs = msgs
    return v


def test_animated_object_updates(viewer):
    viewer.on_shape_loaded(("basic", "Cube"))
    obj = viewer.scene.objects[0]
    obj.set_rotation_speed(1.0, 0.5, 0.0)
    obj.toggle_animation()
    obj.update_animation(0.1)  # used to call update_mesh(None) -> AttributeError every frame
    assert np.allclose(obj.rotation, [0.1, 0.05, 0.0])
    obj.set_scale(2, 2, 2)  # Properties dialog path, same crash


def test_text_without_supported_characters_is_rejected(viewer):
    viewer.on_shape_loaded(("text", "HELLO"))  # only A, B, 0 and ! are defined
    assert viewer.scene.objects == [] and viewer.object_list.count() == 0
    assert viewer.msgs and "HELLO" in viewer.msgs[-1][1]
    viewer.update_scene()  # used to raise on the half-added empty object every frame
    with pytest.raises(ValueError):
        Wireframe.create_text("xyz")


def test_save_and_open(viewer, tmp_path, monkeypatch):
    viewer.save_file()  # nothing loaded: a warning, not an AttributeError
    assert viewer.msgs[-1][0] == "warning"
    viewer.on_shape_loaded(("basic", "Tetrahedron"))
    path = tmp_path / "tetra.obj"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(path), ""))
    viewer.save_file()
    assert path.exists() and path.read_text().count("\nf ") + path.read_text().startswith("f ") == 4
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), ""))
    viewer.open_file()  # used to load into an unused attribute: nothing appeared
    assert len(viewer.scene.objects) == 2 and viewer.object_list.count() == 2
    assert np.allclose(viewer.scene.objects[1].wireframe.vertices, Wireframe.create_tetrahedron().vertices)


def test_mouse_picking_ray(viewer):
    viewer.view.resize(400, 300)
    start, direction = viewer.calculate_camera_ray(QPointF(200, 150))  # TypeError with pyqtgraph >= 0.13
    assert start is not None and abs(direction.length() - 1) < 1e-6
