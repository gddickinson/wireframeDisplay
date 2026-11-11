# INTERFACE.md: navigation map of wireframeDisplay

A PyQt5 / pyqtgraph-OpenGL viewer for 3D shapes, plus a web version (FastAPI + plain ES modules) whose static
GitHub Pages site runs the whole viewer in the browser.

## Desktop app (PyQt5)
| File | Contents |
|---|---|
| `wireframe_viewer.py` | `WireframeViewer` (main window: scene list, menus, sliders, mouse picking, timer), `SceneObject`, `Scene`, `DisplayOptionsDialog`, `ObjectPropertiesDialog`, `ColorButton`. Run: `python wireframe_viewer.py`. 1000+ lines (pre-existing, over the 500-line budget). |
| `shape_loader_dialog.py` | `ShapeLoaderDialog`: emits `('basic', name)`, `('parametric', (name, u, v))`, `('fractal', (name, iterations, size))`, `('text', text)`, `('mri'|'super_resolution', filename)`. |
| `wireframe.py` | `Wireframe` (vertices float32, faces): all `create_*` shape generators, `create_basic_shape` / `create_parametric_shape` / `create_fractal` / `create_text`, OBJ / JSON load and save, `triangles()`, `create_mesh_item()` (imports pyqtgraph lazily, so the module is Qt-free). 800+ lines (pre-existing). |
| `letter_definitions.py` | `ALL_CHARACTERS`: vertices + quad faces of A, B, 0 and !. |

## Qt-free modules (shared by the desktop app, the web API and the tests)
| File | Contents |
|---|---|
| `mesh_utils.py` | `face_array` (negative indices, mixed polygons -> triangles), `triangulate`, `edges_from_faces`. |
| `scene_math.py` | `rotation_matrix` (Rz.Ry.Rx), `transform_vertices` (SceneObject transform), `physics_step` (Scene.update_physics), `GRAVITY`, `RESTITUTION`. |
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
| `scripts/make_engine_fixture.py` | Writes `tests/fixtures/engine_fixture.json` from wireframe.py, scene_math.py, camera.py. |
| `scripts/build_static.py` | Exports `site/` (front end + API JSON) for GitHub Pages. |
| `scripts/screenshots.py` | Playwright smoke test (console errors, phone width) and README images (`docs/img/`). |
| `tests/test_web.py` | API, static build, node engine test, fixture-is-current. |
| `tests/test_scene_math.py` | scene_math vs the original SceneObject code; camera.py vs pyqtgraph (skips without PyQt5 / pyqtgraph). |
| `tests/test_fix_*.py` | Regression tests for the desktop bug fixes (offscreen Qt). `tests/conftest.py` sets `QT_QPA_PLATFORM=offscreen` and pins pyqtgraph to PyQt5. |
| `.github/workflows/pages.yml` | Builds and publishes the static site on push to main. |

## How the pieces connect
`wireframe_viewer.py` -> `shape_loader_dialog.py` -> `wireframe.py` (-> `letter_definitions.py`, `mesh_utils.py`);
`SceneObject` / `Scene` -> `scene_math.py`; dialogs -> `shape_catalog.py`.
`web/app.py` -> `wireframe.py`, `shape_catalog.py`, `scene_math.py`, `camera.py`, `letter_definitions.py`.
Browser: `main.js` -> pages -> `scene.js` / `render.js` -> `engine.js` -> `geometry.js` + `shapes_extra.js`.
