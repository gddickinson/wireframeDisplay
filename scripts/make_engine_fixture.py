"""Reference numbers from the repo's Python code for the JS engine test (web/static/engine.test.mjs).

Shapes come from wireframe.Wireframe (the desktop generators), object transforms and physics from scene_math.py
(what SceneObject / Scene call), the camera from camera.py (checked against pyqtgraph in tests/test_camera.py).
tests/test_web.py recomputes this and checks the committed tests/fixtures/engine_fixture.json is still current.

Run: python scripts/make_engine_fixture.py [--write]
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import camera  # noqa: E402
from letter_definitions import ALL_CHARACTERS  # noqa: E402
from scene_math import physics_step, rotation_matrix, transform_vertices  # noqa: E402
from wireframe import Wireframe  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "engine_fixture.json"

# (kind, name, params) as the shape loader emits them; params are kept small so the fixture stays compact
SHAPE_CASES = [("basic", n, None) for n in ["Cube", "Sphere", "Tetrahedron", "Octahedron", "Icosahedron",
                                             "Dodecahedron", "Torus", "Cylinder", "Cone", "Pyramid", "Prism"]]
SHAPE_CASES += [("parametric", n, [12, 10]) for n in ["Mobius Strip", "Klein Bottle", "Trefoil Knot", "Helicoid",
                                                      "Catenoid", "Sine Surface"]]
SHAPE_CASES += [("fractal", n, [2, 1.5]) for n in ["Sierpinski Triangle", "Koch Snowflake", "Menger Sponge",
                                                   "Apollonian Gasket", "Jerusalem Cube", "Sierpinski Tetrahedron",
                                                   "Pythagoras Tree 3D"]]
SHAPE_CASES += [("fractal", "Koch Snowflake", [3, 1.0]), ("fractal", "Pythagoras Tree 3D", [4, 1.0]),
                ("text", "AB 0!?", None)]
TRANSFORMS = [  # (shape, scale, rotation, position)
    ("Cube", [1, 1, 1], [0, 0, 0], [0, 0, 0]),
    ("Torus", [1.5, 0.5, 2.0], [0.3, -1.2, 2.5], [1.0, -2.0, 0.5]),
    ("Dodecahedron", [0.7, 0.7, 0.7], [3.0, 0.1, -0.4], [-4.9, 4.9, 0.0]),
]
CAMERAS = [
    (dict(camera.DEFAULTS), 640, 480),
    ({"distance": 6.5, "elevation": -20.0, "azimuth": 200.0, "fov": 60.0, "center": [0.5, -1.0, 0.25]}, 900, 600),
    ({"distance": 25.0, "elevation": 89.0, "azimuth": -45.0, "fov": 35.0, "center": [0, 0, 0]}, 390, 520),
]
PROBE = [[0, 0, 0], [1, 1, 1], [-1, 2, 0.5], [3, -2, -1], [0.2, 0.1, 4]]


def build(kind, name, params):
    if kind == "basic":
        return Wireframe.create_basic_shape(name)
    if kind == "parametric":
        return Wireframe.create_parametric_shape(name, *params)
    if kind == "fractal":
        return Wireframe.create_fractal(name, *params)
    return Wireframe.create_text(name)


def shapes():
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for kind, name, params in SHAPE_CASES:
            w = build(kind, name, params)
            out.append({"kind": kind, "name": name, "params": params,
                        "vertices": np.asarray(w.vertices, float).round(12).tolist(),
                        "faces": np.asarray(w.faces).tolist()})
    return out


def transforms():
    out = []
    for name, scale, rot, pos in TRANSFORMS:
        w = Wireframe.create_basic_shape(name)
        center = np.mean(w.vertices, axis=0)
        v = transform_vertices(w.vertices, center, np.array(scale, float), np.array(rot, float), np.array(pos, float))
        out.append({"name": name, "scale": scale, "rotation": rot, "position": pos,
                    "matrix": rotation_matrix(rot).round(15).tolist(), "vertices": v.round(12).tolist()})
    return out


def physics():
    pos, vel = np.array([0.0, 3.0, 0.0]), np.array([0.5, 2.0, -0.25])
    rot, ang = np.zeros(3), np.array([0.1, 0.2, 0.3])
    traj = []
    for _ in range(150):
        physics_step(pos, vel, rot, ang, 1 / 60)
        traj.append(np.r_[pos, vel, rot].round(12).tolist())
    return {"start": [[0.0, 3.0, 0.0], [0.5, 2.0, -0.25], [0.1, 0.2, 0.3]], "dt": 1 / 60, "traj": traj}


def cameras():
    out = []
    for cam, w, h in CAMERAS:
        xy, depth = camera.project(PROBE, cam, w, h)
        c = cam.get("center", [0, 0, 0])
        out.append({"cam": cam, "width": w, "height": h,
                    "view": camera.view_matrix(cam["distance"], cam["elevation"], cam["azimuth"], c).round(12).tolist(),
                    "proj": camera.projection_matrix(cam["distance"], cam["fov"], w, h).round(12).tolist(),
                    "xy": xy.round(9).tolist(), "depth": depth.round(12).tolist()})
    orbit = camera.orbit(dict(camera.DEFAULTS), -37.0, 75.0)
    zoom = camera.zoom(dict(camera.DEFAULTS), 360)
    return {"cases": out, "probe": PROBE, "orbit": orbit, "zoom": zoom, "defaults": camera.DEFAULTS}


def fixture():
    letters = {k: [np.asarray(v).tolist(), np.asarray(f).tolist()] for k, (v, f) in ALL_CHARACTERS.items()}
    return {"shapes": shapes(), "transforms": transforms(), "physics": physics(), "camera": cameras(),
            "letters": letters}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    text = json.dumps(fixture(), separators=(",", ":"))
    if ap.parse_args().write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text)
        print(f"wrote {OUT.relative_to(ROOT)} ({len(text) / 1e3:.0f} kB)")
    else:
        print(text[:400] + " ...")


if __name__ == "__main__":
    main()
