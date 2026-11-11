# wireframeDisplay: notes for Claude

@INTERFACE.md

- Desktop app: PyQt5 + pyqtgraph (`python wireframe_viewer.py`). Tests run Qt offscreen: `python -m pytest -q tests/`.
- Keep `wireframe.py`, `mesh_utils.py`, `scene_math.py`, `camera.py`, `shape_catalog.py` importable without Qt (the web API uses them).
- If a shape generator, the transform, the physics or the camera changes, port it to `web/static/` and rerun
  `python scripts/make_engine_fixture.py --write` and `node web/static/engine.test.mjs`.
- Web app: `python run_web.py` (port 8119); static site: `python scripts/build_static.py`.
- Update INTERFACE.md and SESSION_LOG.md when the structure changes; keep new files under 500 lines.
