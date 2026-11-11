# SESSION_LOG.md

## 2026-11-11: web interface, static site, desktop bug fixes (branch `web-interface`, not pushed)

**Comparison with the sibling repo.** `wireframe_display` is a different codebase (Pygame tutorial-style matrix
scripts, orthographic projection, keyboard transforms); this repo is the PyQt5 / pyqtgraph scene viewer. Neither is a
subset of the other; they share purpose, a few solids and the letter-A geometry. Both READMEs note the overlap.

**Bug fixes** (each its own commit with failing-first regression tests under `tests/`, offscreen Qt):
- Dodecahedron: 9 of 12 faces joined non-neighbouring vertices; now the 12 regular pentagons.
- Polygon faces: Pyramid / Prism crashed (ragged faces); quad / pentagon faces were drawn as scrambled triangles by
  GLMeshItem (now fan-triangulated, `Wireframe.triangles()`); cylinder caps used -2 / -1 indices; OBJ save / load kept
  only three indices per face. New Qt-free `mesh_utils.py`.
- Trefoil Knot from the loader used V resolution as the tube radius (tube 100x too thick).
- Trefoil Knot: NaN vertices for U = 10-18 and tilted rings (tangent not normalised); last ring duplicated the first.
- Viewer: Toggle Animation / Properties crashed every frame (`update_mesh(None)`); unsupported text left a broken
  object that raised every frame; File > Save raised AttributeError and File > Open showed nothing; mouse picking raised
  TypeError on every move with pyqtgraph >= 0.13.
- README: over-claims corrected (MRI / super-resolution loaders, physics play, display options), clone URL, LICENSE link.

**Refactor for the web (GUI behaviour unchanged):** `wireframe.py` imports pyqtgraph lazily; `scene_math.py`
(SceneObject transform, Scene physics), `camera.py` (pyqtgraph camera mirror, tested against pyqtgraph) and
`shape_catalog.py` (loader lists, ranges, display defaults) are Qt-free and imported back by the viewer / dialogs.
Desktop window verified offscreen (loads shapes, animates for 1.5 s).

**Web:** FastAPI app (`web/app.py`, port 8119) + static site; JS engine (`geometry.js`, `shapes_extra.js`, `engine.js`)
ports 24 of 25 generators, text, transform, physics, camera and OBJ / JSON; the Gyroid comes from the Python server
(exported JSON on the static site). Node test vs `tests/fixtures/engine_fixture.json`: max vertex difference 5e-13.

**Results:** `pytest tests/` 55 passed; `tests/test_web.py` 36 passed; node engine 36 checks passed; static build
27 API files, 1.1 MB; screenshots.py --static on all routes ok, phone overflow 0 px; run_web.py on 8119 + --base ok.

**Needs George's decision (not changed):**
- Text: letters are 12-18 units wide but `create_text` spaces them 1.5 apart, so "AB" overlaps; only A, B, 0, ! exist.
- Koch Snowflake starts from (origin, two points at 120 deg) rather than an equilateral triangle, and is one concave face.
- "Jerusalem Cube" keeps the 8 corner cubes (Cantor dust), not a Jerusalem cube; Menger sub-cubes are placed relative
  to the origin (geometry is distinct but offset); Gyroid vertices are in voxel units (0-29), much larger than others.
- Physics: `update_scene`'s physics version is commented out; gravity acts on -y while pyqtgraph's camera has z up.
- Display Options: only Show Faces is wired (edges / vertices / colours / sizes do nothing on the desktop).
- `WireframeViewer.load_shape` references a non-existent `shape_combo` (dead code); MRI / super-res loaders missing.
- `wireframe.py` (841 lines) and `wireframe_viewer.py` (~990 lines) exceed the 500-line budget (pre-existing; not split).
