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

**Needs George's decision:** see the follow-up below (text, Koch, Jerusalem, Gyroid and physics now fixed).
- `WireframeViewer.load_shape` references a non-existent `shape_combo` (dead code).
- Super-resolution loading: removed (no format defined here); wireframe_display's `loadNIKONFile` (tab-separated Nikon N-STORM export, Xc / Yc / Zc columns) is a candidate format.
- Menger sub-cubes are placed relative to the origin (distinct but offset from the parent cube).

## 2026-11-11 (follow-up): George: "fix any other problems you come across"

Fast-forwarded `web-interface` to `main`, then five fixes, each with failing-first tests and Python and JS kept identical
(engine fixture regenerated, node test passing):
- Text: glyphs advance by their width + a gap of 4 (a space by 10) instead of a fixed 1.5 (letters overlapped); A-Z, 0-9
  and ! defined. One table, `letter_glyphs.json` (from `scripts/make_glyphs.py`: George's A, B, ! kept, the solid-block 0
  and all other characters drawn from strokes), read by `letter_definitions.py` and served to the web viewer.
- Koch snowflake: equilateral seed traversed so bumps point outwards, and each peak at the apex of an equilateral bump
  (it sat over the first third point): 3*4^n equal segments.
- Jerusalem cube: 8 corner cubes (k = sqrt2 - 1) + 12 edge cubes (k^2) per cube, 20^n cubes (was 8 corner cubes of 1/3:
  Cantor dust). Browser cap 3 iterations, gallery 2.
- Gyroid: world coordinates in [-pi, pi] (were voxel indices) and x / y no longer swapped (meshgrid 'xy' indexing).
- Desktop Play now runs Scene.update_physics; gravity along -z (the camera's up axis), bounce at z = 0; same in the JS.

Checks: `pytest tests/` 72 passed; node engine 38 checks passed (max vertex diff 5.1e-13); screenshots --static on every
route ok, phone overflow 0 px; run_web.py on 8119 + --base ok (stopped); desktop offscreen run ok; README screenshots
refreshed.

## 2026-11-11 (second follow-up)

- Fix Display Options: every option now reaches the GL items (faces GLMeshItem in the face colour, polygon edges
  GLLinePlotItem with colour / width, vertices GLScatterPlotItem with colour / size); face-less shapes show vertices.
- Fix MRI loading: `Wireframe.load_mri` (nibabel 5.5.0, first volume of 4D files, Otsu threshold, marching cubes,
  affine to scanner mm). The super-resolution button (no file format anywhere in this repo) was removed; README corrected.
- Split: wireframe.py -> wireframe.py + shapes_basic / shapes_parametric / shapes_fractal; wireframe_viewer.py ->
  wireframe_viewer.py + scene_objects / viewer_dialogs / viewer_mouse / viewer_files. All .py files < 500 lines.

Checks: `pytest tests/` 81 passed; node engine 38 checks passed; screenshots --static (all routes) ok, phone 0 px;
run_web.py on 8119 + --base ok (stopped); `python wireframe_viewer.py` runs offscreen. GL drawing itself cannot be
seen offscreen: the tests check the items' visibility, colours, widths, sizes and positions.
