"""Qt-free scene maths used by SceneObject / Scene in wireframe_viewer.py and by the web API.

rotation_matrix(rotation)      -- Rz . Ry . Rx for Euler angles (rx, ry, rz) in radians
transform_vertices(...)        -- scale about the centre, rotate about the centre, then translate (SceneObject)
physics_step(...)              -- one step of Scene.update_physics: integrate, gravity on -z, bounce at z = 0
GRAVITY, RESTITUTION, UP_AXIS  -- the constants of that step (z is up, as in pyqtgraph's orbit camera)
"""
import numpy as np

GRAVITY = 9.8       # Scene.update_physics: velocity[UP_AXIS] -= 9.8 * dt
RESTITUTION = 0.8   # bounce with damping at the ground plane z = 0
UP_AXIS = 2         # z: the up axis of the GLViewWidget camera the scene is viewed with


def rotation_matrix(rotation):
    rx, ry, rz = rotation
    rotation_x = np.array([[1, 0, 0],
                           [0, np.cos(rx), -np.sin(rx)],
                           [0, np.sin(rx), np.cos(rx)]])
    rotation_y = np.array([[np.cos(ry), 0, np.sin(ry)],
                           [0, 1, 0],
                           [-np.sin(ry), 0, np.cos(ry)]])
    rotation_z = np.array([[np.cos(rz), -np.sin(rz), 0],
                           [np.sin(rz), np.cos(rz), 0],
                           [0, 0, 1]])
    return np.dot(rotation_z, np.dot(rotation_y, rotation_x))


def transform_vertices(vertices, center, scale, rotation, position):
    """SceneObject.get_transformed_vertices: scale and rotate about `center`, then add `position`."""
    scaled_vertices = (vertices - center) * scale + center
    rotated_vertices = np.dot(scaled_vertices - center, rotation_matrix(rotation).T) + center
    return rotated_vertices + position


def physics_step(position, velocity, rotation, angular_velocity, dt):
    """Scene.update_physics for one object; updates the arrays in place."""
    position += velocity * dt
    rotation += angular_velocity * dt
    velocity[UP_AXIS] -= GRAVITY * dt
    if position[UP_AXIS] < 0:
        position[UP_AXIS] = 0
        velocity[UP_AXIS] = -velocity[UP_AXIS] * RESTITUTION
