// About: what the desktop app is and does, what the web version covers (and how it differs), how to run, credits.
import { route, app, esc, list } from './core.js';
import { loadSetup } from './scene.js';

const MOUSE = [
  ['Press on an object and drag', 'Rotate it (x from vertical drag, y from horizontal)'], ['Ctrl + drag', 'Move it in x / y'],
  ['Hover', 'The object under the pointer turns red'], ['Wheel', 'Zoom (camera distance × 0.999 per wheel step)'],
  ['Double-click a list entry', 'Centre the camera on that object'], ['Right-click a list entry', 'Rename, Delete, Properties, Toggle Animation'],
];

route('about', async () => {
  const { info, cat } = await loadSetup();
  app().innerHTML = `<p class="kicker">About</p><h1 class="glow">About the viewer</h1>
  <p class="lead">A Python tool to create, view and manipulate 3D shapes (README: "3D Wireframe Viewer and Physics Simulator"). This
  site is the web version of <a href="https://github.com/gddickinson/wireframeDisplay">wireframeDisplay</a>, a PyQt5 / pyqtgraph-OpenGL desktop app.</p>
  <p class="callout a">A sibling repository, <a href="https://github.com/gddickinson/wireframe_display">wireframe_display</a>, is a separate,
  earlier Pygame project with its own matrix maths and orthographic projection. The two share their purpose, a few solids
  (tetrahedron, octahedron, icosahedron, sphere, torus, sine surface) and the same letter-A geometry, but no code.</p>

  <h2>Shapes</h2>
  <p>${info.shapes} generators in three groups, plus text built from the ${info.characters} characters defined in
  <code>letter_definitions.py</code> (${esc(Object.keys(cat.letters).sort().join(' '))}; other characters are skipped).</p>
  <div class="scroll"><table><tr><th>Group</th><th>Shapes</th><th>Parameters (desktop loader)</th></tr>
  ${list(cat.groups, g => `<tr><td>${esc(g.title)}</td><td>${esc(g.names.join(', '))}</td><td>${g.kind === 'parametric' ? `U, V resolution ${cat.resolution[0]}-${cat.resolution[1]} (default ${cat.resolution[2]})`
    : g.kind === 'fractal' ? `iterations ${cat.iterations[0]}-${cat.iterations[1]} (default ${cat.iterations[2]}), size ${cat.size[0]}-${cat.size[1]}` : 'none'}</td></tr>`)}</table></div>

  <h2>The scene</h2>
  <p>Each loaded shape becomes a scene object with a position, rotation, scale, mass and rotation speed. Its vertices are drawn
  scaled and rotated about the shape's centre (rotation R = R<sub>z</sub>·R<sub>y</sub>·R<sub>x</sub>) and then translated:</p>
  <p><span class="eq">v' = R · (s ∘ (v − c)) + c + p</span></p>
  <p>Toggle Animation turns an object at its rotation speed (radians per second). The physics step in <code>Scene.update_physics</code>
  integrates position and rotation, applies gravity of ${cat.physics.gravity} along −y ("assuming Y is up") and bounces objects
  off y = 0, keeping ${cat.physics.restitution} of their speed. The camera is pyqtgraph's orbit camera: distance ${cat.camera.distance},
  elevation ${cat.camera.elevation}°, azimuth ${cat.camera.azimuth}°, field of view ${cat.camera.fov}° by default, with z pointing up on screen.</p>

  <h2>What the web version covers</h2>
  <ul>
    <li><code>geometry.js</code> and <code>shapes_extra.js</code> port every generator except the Gyroid line by line, and
      <code>engine.js</code> ports the object transform, the physics step, the camera and the OBJ / JSON file code; all are tested
      against numbers from the Python (see <a href="#/check">Cross-check</a>). The Gyroid is built by the Python server.</li>
    <li>Faces are painted back to front on a canvas instead of with an OpenGL depth buffer; edges are polygon outlines (the desktop
      outlines the triangles OpenGL draws). "Shading" is a web-only light term; switch it off for the desktop's flat colour.</li>
    <li>Differences from the desktop app as it stands: Play runs the physics step (the desktop's play button only toggles its label,
      the physics call is commented out); the Display Options edge, vertex, colour and size settings all work (in the desktop only
      Show Faces is wired); shapes without faces (Apollonian gasket) show their vertices; dragging empty space orbits the camera
      (pyqtgraph's default, which the desktop's own mouse handlers replace). Fractal iterations are capped in the browser where they
      grow fastest (${esc(Object.entries(cat.web_iteration_caps).filter(([, c]) => c < 8).map(([n, c]) => `${n} ${c}`).join(', '))}).</li>
    <li>Web additions: Frame scene, camera buttons and keyboard control of the 3D view (arrow keys orbit, + / − zoom, F frames).</li>
  </ul>

  <h2>Run it yourself</h2>
  <h3>Desktop app (PyQt5 + pyqtgraph)</h3>
  <pre>pip install -r requirements.txt
python wireframe_viewer.py</pre>
  <div class="scroll"><table><tr><th>Mouse</th><th>Action</th></tr>${list(MOUSE, ([k, a]) => `<tr><td>${esc(k)}</td><td>${esc(a)}</td></tr>`)}</table></div>
  <h3>Web app (this site, with the Python API)</h3>
  <pre>pip install -r requirements-web.txt
python run_web.py          # http://127.0.0.1:8119</pre>
  <p>The local app serves the loader catalogue from <code>shape_catalog.py</code> and builds shapes with the real Python generators
  for the cross-check and the Gyroid at any resolution. The static GitHub Pages site is exported by <code>scripts/build_static.py</code>.</p>

  <h2>Credits</h2>
  <p>3D Wireframe Viewer by George Dickinson, MIT licence. Thanks to the PyQt and PyQtGraph teams (README acknowledgements).
  Web version built with AI assistance from <a href="https://claude.com/">Claude (Anthropic)</a>.</p>`;
});
