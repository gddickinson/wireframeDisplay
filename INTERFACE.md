# INTERFACE.md: navigation map of wireframeDisplay

A PyQt5 / pyqtgraph-OpenGL viewer for 3D shapes, plus a web version (FastAPI + plain ES modules) whose static
GitHub Pages site runs the whole viewer in the browser.

## Desktop app (PyQt5)
| File | Contents |
|---|---|
| `wireframe_viewer.py` | `WireframeViewer` main window (scene list, menus, sliders, display options wiring, timer: animation + physics on Play). Run: `python wireframe_viewer.py`. Re-exports `SceneObject`, `Scene`, the dialogs and `Wireframe`. |
| `scene_objects.py` | `SceneObject` (wireframe + position / rotation / scale / physics state; GL items: faces `GLMeshItem`, polygon edges `GLLinePlotItem`, vertices `GLScatterPlotItem`), `Scene` (objects, `update_physics`), `default_style`, `display_style`. |
| `viewer_dialogs.py` | `ColorButton`, `DisplayOptionsDialog`, `ObjectPropertiesDialog`. |
| `viewer_mouse.py` | `ViewerMouseMixin`: hover, press-to-pick, drag rotate / Ctrl-drag move, double-click centring, camera-ray picking. |
| `viewer_files.py` | `ViewerFilesMixin`: shape loader signal (`on_shape_loaded`, `create_wireframe`, `add_wireframe`), File > Open / Save, legacy `load_*` helpers. |
| `shape_loader_dialog.py` | `ShapeLoaderDialog`: emits `('basic', name)`, `('parametric', (name, u, v))`, `('fractal', (name, iterations, size))`, `('text', text)`, `('mri', filename)`. |
| `letter_definitions.py` | Loads `letter_glyphs.json`: `ALL_CHARACTERS` (A-Z, 0-9, !), `GLYPH_TABLE`, `GAP`, `SPACE`. |
| `letter_glyphs.json` | The one glyph table (vertices + quad faces per character, gap, space), also served to the web viewer by `/api/catalog`. Written by `scripts/make_glyphs.py`. |

## Qt-free modules (shared by the desktop app, the web API and the tests)
| File | Contents |
|---|---|
| `wireframe.py` | `Wireframe` (vertices float32, faces): construction, `triangles()`, `create_mesh_item()` (lazy pyqtgraph import), translate / scale, OBJ / JSON, `create_character` / `create_text`, dispatchers `create_basic_shape` / `create_parametric_shape` / `create_fractal`, `load_mri` (NIfTI isosurface via nibabel + marching cubes). |
| `shapes_basic.py`, `shapes_parametric.py`, `shapes_fractal.py` | Generator mixins of `Wireframe`: basic solids; parametric surfaces (+ `marching_cubes`, `rotation_matrix`); fractals. |
| `mesh_utils.py` | `face_array` (negative indices, mixed polygons -> triangles), `triangulate`, `edges_from_faces`. |
| `scene_math.py` | `rotation_matrix` (Rz.Ry.Rx), `transform_vertices` (SceneObject transform), `physics_step` (Scene.update_physics: gravity along -z, bounce at z = 0), `GRAVITY`, `RESTITUTION`, `UP_AXIS`. |
| `camera.py` | NumPy mirror of pyqtgraph's GLViewWidget camera: `view_matrix`, `projection_matrix`, `project`, `orbit`, `zoom`, `DEFAULTS`. |
| `shape_catalog.py` | Loader lists and ranges, display / slider / property defaults (read by the dialogs, the viewer and the web API). |

## Web interface
| File | Contents |
|---|---|
| `run_web.py` | Starts uvicorn on 127.0.0.1:8119. |
| `web/app.py` | FastAPI: `/api/info`, `/api/catalog`, `/api/shape/{slug}` (Python-built shape, optional `u`, `v`, `iterations`, `size`), `/api/text`; `STATIC_ENDPOINTS` for the static export. |
| `web/static/index.html`, `style.css` (kit), `style_app.css`, `core.js` (kit router / api), `main.js`, `static_api.js`, `icon.svg` | Shell, theme, router, static-site data layer. |
| `web/static/geometry.js` | JS port: `linspace`, `faceArray`, `triangulate`, `edgesFromFaces`, `makeShape`, the 11 basic shapes (`BASIC`). |
| `web/static/shapes_extra.js` | JS port: parametric surfaces (`PARAMETRIC`, all but the Gyroid), fractals (`FRACTALS`), `createText`, `axisRotation`. |
| `web/static/engine.js` | `buildShape`, `centreOf`, `rotationMatrix`, `transformVertices`, `physicsStep`, camera (`viewMatrix`, `projectionMatrix`, `project`, `orbit`, `zoom`), OBJ / JSON (`parseObj`, `toObj`, `parseJson`, `toJson`). |
| `web/static/render.js` | Canvas painter (`drawScene`, depth-sorted polygons), `fitCanvas`, `pick` (hover / press picking), colour helpers. |
| `web/static/scene.js` | `loadSetup` (info + catalog), `makeObject`, `loadShape` (JS, or API for the Gyroid), `objectName`, `frameScene`. |
| `web/static/viewer.js`, `viewer_panel.js` | Viewer page: canvas, mouse / wheel / keys, sliders, loop; control panel (list, loader, files, display options, properties). |
| `web/static/home.js`, `shapes.js`, `check.js`, `about.js` | Other pages. |
| `web/static/engine.test.mjs` | Node test of the JS engine against `tests/fixtures/engine_fixture.json`. |

## Scripts and tests
| File | Contents |
|---|---|
| `scripts/make_glyphs.py` | Builds `letter_glyphs.json` (George's A, B, ! plus stroke glyphs for the rest). |
| `scripts/make_engine_fixture.py` | Writes `tests/fixtures/engine_fixture.json` from wireframe.py, scene_math.py, camera.py. |
| `scripts/build_static.py` | Exports `site/` (front end + API JSON) for GitHub Pages. |
| `scripts/screenshots.py` | Playwright smoke test (console errors, phone width) and README images (`docs/img/`). |
| `tests/test_web.py` | API, static build, node engine test, fixture-is-current. |
| `tests/test_scene_math.py` | scene_math vs the original SceneObject code; camera.py vs pyqtgraph (skips without PyQt5 / pyqtgraph). |
| `tests/test_fix_*.py` | Regression tests for the bug fixes (dodecahedron, polygon faces, trefoil, viewer, text, fractals, physics, display options, MRI; offscreen Qt). `tests/test_split.py`: public names and the 500-line budget. `tests/conftest.py` sets `QT_QPA_PLATFORM=offscreen` and pins pyqtgraph to PyQt5. |
| `.github/workflows/pages.yml` | Builds and publishes the static site on push to main. |

## How the pieces connect
`wireframe_viewer.py` (+ `viewer_files.py`, `viewer_mouse.py`, `viewer_dialogs.py`, `scene_objects.py`) -> `shape_loader_dialog.py` -> `wireframe.py`
(-> `shapes_*.py`, `letter_definitions.py` -> `letter_glyphs.json`, `mesh_utils.py`); `scene_objects.py` -> `scene_math.py`; dialogs -> `shape_catalog.py`.
`web/app.py` -> `wireframe.py`, `shape_catalog.py`, `scene_math.py`, `camera.py`, `letter_definitions.py`.
Browser: `main.js` -> pages -> `scene.js` / `render.js` -> `engine.js` -> `geometry.js` + `shapes_extra.js`.
