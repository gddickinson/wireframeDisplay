"""Web interface for the 3D Wireframe Viewer.

app.py          FastAPI app: static front end + JSON API (/api/info, /api/catalog, /api/shape/<slug>, /api/text)
static/         ES-module front end (no build step); engine.js + geometry.js + shapes_extra.js are the JS port of
                the shape generators, SceneObject maths and pyqtgraph camera, tested by engine.test.mjs
"""
