"""Qt-free mirror of the pyqtgraph GLViewWidget orbit camera that the desktop viewer draws with.

The desktop app uses gl.GLViewWidget with its defaults (distance 10, elevation 30 deg, azimuth 45 deg, horizontal
field of view 60 deg, centre at the origin). These functions rebuild the same view and projection matrices with NumPy
(tests/test_camera.py checks them against pyqtgraph itself) so the web viewer can be tested against Python numbers.

view_matrix, projection_matrix, project -- the matrices and world -> pixel mapping (y down, like Qt widgets)
orbit, zoom                              -- the mouse-drag and wheel updates of GLViewWidget
"""
import numpy as np

DEFAULTS = {"distance": 10.0, "elevation": 30.0, "azimuth": 45.0, "fov": 60.0, "center": [0.0, 0.0, 0.0]}


def _translate(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def _rotate(angle_deg, x, y, z):
    """QMatrix4x4.rotate: right-handed rotation by angle_deg about the axis (x, y, z)."""
    a = np.radians(angle_deg)
    u = np.array([x, y, z], float) / np.linalg.norm([x, y, z])
    c, s = np.cos(a), np.sin(a)
    k = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    m = np.eye(4)
    m[:3, :3] = c * np.eye(3) + s * k + (1 - c) * np.outer(u, u)
    return m


def view_matrix(distance, elevation, azimuth, center=(0, 0, 0)):
    """GLViewWidget.viewMatrix (default 'euler' rotation method)."""
    return (_translate(0, 0, -distance) @ _rotate(elevation - 90, 1, 0, 0) @ _rotate(azimuth + 90, 0, 0, -1)
            @ _translate(-center[0], -center[1], -center[2]))


def projection_matrix(distance, fov, width, height):
    """GLViewWidget.projectionMatrix for the full viewport: an OpenGL frustum with near = distance/1000."""
    near, far = distance * 0.001, distance * 1000.0
    r = near * np.tan(0.5 * np.radians(fov))
    t = r * height / width
    left, right, bottom, top = -r, r, -t, t
    return np.array([[2 * near / (right - left), 0, (right + left) / (right - left), 0],
                     [0, 2 * near / (top - bottom), (top + bottom) / (top - bottom), 0],
                     [0, 0, -(far + near) / (far - near), -2 * far * near / (far - near)],
                     [0, 0, -1, 0]])


def project(points, cam, width, height):
    """World points (N, 3) -> pixel coordinates (N, 2), x right and y down, plus eye-space depth (N,)."""
    pts = np.c_[np.asarray(points, float), np.ones(len(points))]
    eye = pts @ view_matrix(cam["distance"], cam["elevation"], cam["azimuth"], cam.get("center", (0, 0, 0))).T
    clip = eye @ projection_matrix(cam["distance"], cam["fov"], width, height).T
    ndc = clip[:, :3] / clip[:, 3:4]
    xy = np.c_[(ndc[:, 0] + 1) * 0.5 * width, (1 - ndc[:, 1]) * 0.5 * height]
    return xy, -eye[:, 2]


def orbit(cam, d_azim, d_elev):
    """GLViewWidget.orbit: azimuth += d_azim, elevation clipped to [-90, 90]. A left-drag calls orbit(-dx, dy)."""
    cam["azimuth"] += d_azim
    cam["elevation"] = float(np.clip(cam["elevation"] + d_elev, -90.0, 90.0))
    return cam


def zoom(cam, wheel_delta):
    """GLViewWidget.wheelEvent: distance *= 0.999 ** delta (one wheel notch is delta = 120)."""
    cam["distance"] *= 0.999 ** wheel_delta
    return cam
