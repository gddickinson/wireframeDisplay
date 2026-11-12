"""Regression tests: Play runs the scene physics in the desktop viewer, with gravity along the camera's up axis (z)."""
import numpy as np
import pytest

from scene_math import physics_step

pytest.importorskip("PyQt5")
pytest.importorskip("pyqtgraph")
from PyQt5.QtWidgets import QApplication  # noqa: E402

QAPP = QApplication.instance() or QApplication([])


def test_gravity_is_along_z():
    pos, vel, rot = np.array([0.5, -1.0, 2.0]), np.zeros(3), np.zeros(3)
    zs = []
    for _ in range(300):
        physics_step(pos, vel, rot, np.zeros(3), 0.01)
        zs.append(pos[2])
    assert pos[0] == 0.5 and pos[1] == -1.0  # x and y untouched (y used to be the falling axis)
    assert min(zs) == 0 and max(zs[100:]) > 0.2  # fell to the ground plane z = 0 and bounced


def test_play_runs_physics_in_the_viewer():
    import wireframe_viewer as wv
    v = wv.WireframeViewer()
    v.animation_timer.stop()
    v.on_shape_loaded(("basic", "Cube"))
    obj = v.scene.objects[0]
    obj.position[:] = [0, 0, 3.0]
    v.last_time = v.last_time.addMSecs(-100)
    v.update_scene()  # not playing: nothing moves
    assert obj.position[2] == 3.0
    v.toggle_animation()  # the Play button
    assert v.is_playing
    for _ in range(5):
        v.last_time = v.last_time.addMSecs(-100)
        v.update_scene()
    assert obj.position[2] < 3.0 and obj.velocity[2] < 0  # used to stay put: the physics call was commented out
    z = obj.mesh_item.opts["meshdata"].vertexes()[:, 2]
    assert np.isclose(z.min(), obj.position[2] - 1, atol=1e-4)  # the drawn cube moved with it
