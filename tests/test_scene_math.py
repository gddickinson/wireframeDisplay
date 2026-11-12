"""The Qt-free scene maths and camera mirror match what the desktop app computes."""
import numpy as np
import pytest

import camera
from scene_math import physics_step, transform_vertices
from wireframe import Wireframe


def original_transform(vertices, center, scale, rotation, position):
    """SceneObject.get_transformed_vertices as it was written before scene_math.py existed."""
    scaled = (vertices - center) * scale + center
    rx = np.array([[1, 0, 0], [0, np.cos(rotation[0]), -np.sin(rotation[0])], [0, np.sin(rotation[0]), np.cos(rotation[0])]])
    ry = np.array([[np.cos(rotation[1]), 0, np.sin(rotation[1])], [0, 1, 0], [-np.sin(rotation[1]), 0, np.cos(rotation[1])]])
    rz = np.array([[np.cos(rotation[2]), -np.sin(rotation[2]), 0], [np.sin(rotation[2]), np.cos(rotation[2]), 0], [0, 0, 1]])
    r = np.dot(rz, np.dot(ry, rx))
    return np.dot(scaled - center, r.T) + center + position


def test_transform_matches_original_code():
    w = Wireframe.create_torus()
    c = np.mean(w.vertices, axis=0)
    args = (np.array([1.5, 0.5, 2.0]), np.array([0.3, -1.2, 2.5]), np.array([1.0, -2.0, 0.5]))
    assert np.array_equal(transform_vertices(w.vertices, c, *args), original_transform(w.vertices, c, *args))


def test_physics_bounces():
    pos, vel, rot = np.array([0.0, 0.0, 1.0]), np.zeros(3), np.zeros(3)
    ys = []
    for _ in range(200):
        physics_step(pos, vel, rot, np.zeros(3), 0.01)
        ys.append(pos[2])
    assert min(ys) == 0 and max(ys[60:]) > 0.1  # hit the floor and came back up


def test_scene_object_uses_scene_math():
    qt = pytest.importorskip("PyQt5.QtWidgets")
    pytest.importorskip("pyqtgraph")
    app = qt.QApplication.instance() or qt.QApplication([])  # noqa: F841
    import wireframe_viewer as wv
    o = wv.SceneObject(Wireframe.create_cube())
    o.position[:] = [1, 2, 3]
    o.rotation[:] = [0.1, 0.2, 0.3]
    o.scale[:] = [2, 1, 0.5]
    assert np.allclose(o.get_transformed_vertices(),
                       original_transform(o.wireframe.vertices, o.center, o.scale, o.rotation, o.position))


@pytest.mark.parametrize("cam,w,h", [(dict(camera.DEFAULTS), 640, 480),
                                     ({"distance": 6.5, "elevation": -20.0, "azimuth": 200.0, "fov": 35.0,
                                       "center": [0.5, -1.0, 0.25]}, 900, 600)])
def test_camera_matches_pyqtgraph(cam, w, h):
    qt = pytest.importorskip("PyQt5.QtWidgets")
    pytest.importorskip("pyqtgraph")
    from PyQt5.QtGui import QVector3D
    import pyqtgraph.opengl as gl
    app = qt.QApplication.instance() or qt.QApplication([])  # noqa: F841
    view = gl.GLViewWidget()
    view.opts.update({k: cam[k] for k in ("distance", "elevation", "azimuth", "fov")})
    view.opts["center"] = QVector3D(*cam.get("center", [0, 0, 0]))
    vm = np.array(view.viewMatrix().data()).reshape(4, 4).T  # QMatrix4x4.data() is column-major
    pm = np.array(view.projectionMatrix((0, 0, w, h), (0, 0, w, h)).data()).reshape(4, 4).T
    assert np.allclose(vm, camera.view_matrix(cam["distance"], cam["elevation"], cam["azimuth"], cam.get("center", [0, 0, 0])), atol=1e-5)
    assert np.allclose(pm, camera.projection_matrix(cam["distance"], cam["fov"], w, h), rtol=1e-5, atol=1e-7)
