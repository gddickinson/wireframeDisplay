"""FastAPI web app for the 3D Wireframe Viewer: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8119, local only). `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes below.

Everything comes from the desktop app's own Qt-free modules: shape_catalog.py (loader lists, ranges and display
defaults), wireframe.py (the shape generators), letter_definitions.py (text characters), scene_math.py (physics
constants) and camera.py (the pyqtgraph camera defaults). The browser builds shapes with a JS port of the same
generators; the Python shapes served here are used by the cross-check page and for the Gyroid, which needs
scikit-image's marching cubes.
"""
import re
import sys
import warnings
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import camera  # noqa: E402
import scene_math  # noqa: E402
import shape_catalog as cat  # noqa: E402
from letter_definitions import ALL_CHARACTERS  # noqa: E402
from wireframe import Wireframe  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
TITLE = "3D Wireframe Viewer"
# The desktop loader allows 1-8 iterations for every fractal; some grow as 20^n or 8^n, so the browser caps them.
WEB_ITERATION_CAPS = {"Sierpinski Triangle": 8, "Koch Snowflake": 6, "Menger Sponge": 3, "Apollonian Gasket": 7,
                      "Jerusalem Cube": 4, "Sierpinski Tetrahedron": 6, "Pythagoras Tree 3D": 8}
# Parameters of the server-built shapes exported to the static site (/shape/<slug>): the loader defaults, with
# fractal iterations reduced where 4 would be too large to ship as JSON.
GALLERY_ITERATIONS = {"Menger Sponge": 2, "Jerusalem Cube": 3}

app = FastAPI(title=TITLE)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _entries():
    u = cat.PARAM_RESOLUTION[2]
    out = [{"kind": "basic", "name": n, "params": []} for n in cat.BASIC_SHAPES]
    out += [{"kind": "parametric", "name": n, "params": [u, u]} for n in cat.PARAMETRIC_SHAPES]
    out += [{"kind": "fractal", "name": n, "params": [GALLERY_ITERATIONS.get(n, cat.FRACTAL_ITERATIONS[2]),
                                                       cat.FRACTAL_SIZE[2]]} for n in cat.FRACTALS]
    for e in out:
        e["slug"] = slug(e["name"])
        e["server_only"] = e["name"] == "Gyroid"
    return out


SHAPES = {e["slug"]: e for e in _entries()}


def build(kind, name, params):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if kind == "basic":
            return Wireframe.create_basic_shape(name)
        if kind == "parametric":
            return Wireframe.create_parametric_shape(name, *params)
        return Wireframe.create_fractal(name, *params)


def shape_json(w, **extra):
    faces = [] if w.faces is None else np.asarray(w.faces).tolist()
    return {**extra, "vertices": np.asarray(w.vertices, float).round(7).tolist(), "faces": faces,
            "source": "wireframe.Wireframe (Python)"}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Project summary and counts for the home page."""
    return {"title": TITLE, "version": "1", "basic": len(cat.BASIC_SHAPES), "parametric": len(cat.PARAMETRIC_SHAPES),
            "fractals": len(cat.FRACTALS), "characters": len(ALL_CHARACTERS),
            "shapes": len(cat.BASIC_SHAPES) + len(cat.PARAMETRIC_SHAPES) + len(cat.FRACTALS)}


@app.get("/api/catalog")
def catalog():
    """Shape loader groups and ranges, display/slider/property defaults, camera, physics and text characters."""
    return {
        "groups": [{"kind": "basic", "title": "Basic Shapes", "names": cat.BASIC_SHAPES},
                   {"kind": "parametric", "title": "Parametric Shapes", "names": cat.PARAMETRIC_SHAPES},
                   {"kind": "fractal", "title": "Fractal Patterns", "names": cat.FRACTALS}],
        "shapes": list(SHAPES.values()),
        "resolution": cat.PARAM_RESOLUTION, "iterations": cat.FRACTAL_ITERATIONS, "size": cat.FRACTAL_SIZE,
        "web_iteration_caps": WEB_ITERATION_CAPS,
        "display": cat.DISPLAY, "object_color": cat.OBJECT_COLOR, "hover_color": cat.HOVER_COLOR,
        "translation_slider": cat.TRANSLATION_SLIDER, "scale_slider": cat.SCALE_SLIDER,
        "property_ranges": cat.PROPERTY_RANGES,
        "camera": camera.DEFAULTS, "physics": {"gravity": scene_math.GRAVITY, "restitution": scene_math.RESTITUTION},
        "letters": {k: [np.asarray(v).tolist(), np.asarray(f).tolist()] for k, (v, f) in ALL_CHARACTERS.items()},
    }


@app.get("/api/shape/{name}")
def shape(name: str, u: int | None = Query(None, ge=cat.PARAM_RESOLUTION[0], le=cat.PARAM_RESOLUTION[1]),
          v: int | None = Query(None, ge=cat.PARAM_RESOLUTION[0], le=cat.PARAM_RESOLUTION[1]),
          iterations: int | None = Query(None, ge=1, le=8), size: float | None = Query(None, ge=0.1, le=10)):
    """A shape built by the real Python generator (loader defaults unless parameters are given)."""
    if name not in SHAPES:
        raise HTTPException(404, f"unknown shape {name!r}")
    e = SHAPES[name]
    params = list(e["params"])
    if e["kind"] == "parametric":
        params = [u or params[0], v or params[1]]
    elif e["kind"] == "fractal":
        params = [min(iterations or params[0], WEB_ITERATION_CAPS[e["name"]]), size or params[1]]
    return shape_json(build(e["kind"], e["name"], params), kind=e["kind"], name=e["name"], params=params)


@app.get("/api/text")
def text(t: str = Query(..., min_length=1, max_length=40)):
    """Wireframe.create_text (only the characters in letter_definitions.py are drawn)."""
    try:
        return shape_json(Wireframe.create_text(t), kind="text", name=t, params=[])
    except ValueError as err:
        raise HTTPException(422, str(err))


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info", "/catalog"] + [f"/shape/{s}" for s in SHAPES]
