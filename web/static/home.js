// Home page: hero with a live scene, counts from the API, entry cards.
import { route, api, app, esc, list, animate } from './core.js';
import { buildShape, CAMERA_DEFAULTS } from './engine.js';
import { drawScene, fitCanvas } from './render.js';
import { loadSetup, makeObject, frameScene } from './scene.js';

const DOORS = [
  ['#/viewer', 'Viewer', 'The full app: load shapes, drag to rotate them or orbit the camera, zoom, per-object spin, gravity and bounce, faces / edges / vertices, OBJ and JSON files.'],
  ['#/shapes', 'Shapes', 'Every generator in the shape loader: basic solids, parametric surfaces, fractals and text, each drawn live.'],
  ['#/check', 'Cross-check', 'The browser engine against the Python generators: the same shapes built by NumPy on the server, compared vertex by vertex.'],
  ['#/about', 'About', 'What the desktop app does, what the web version covers, how to run both, credits.'],
];

route('home', async () => {
  const [info, { cat }] = await Promise.all([api('/info'), loadSetup()]);
  app().innerHTML = `
  <section class="hero two heroview">
    <div>
      <p class="kicker">Solids · surfaces · fractals</p>
      <h1 class="glow">3D Wireframe Viewer</h1>
      <p class="lead">Create, view and manipulate 3D shapes: Platonic solids, parametric surfaces such as the Klein bottle and
      trefoil knot, fractals from the Menger sponge to the Pythagoras tree, and extruded text. Everything runs in your browser,
      ported from the PyQt5 / pyqtgraph desktop app.</p>
      <a class="btn" href="#/viewer">Open the viewer</a><a class="btn alt" href="#/shapes">Browse the shapes</a>
    </div>
    <figure class="fig"><canvas id="hero" role="img" aria-label="Live 3D view: a dodecahedron and a torus turning slowly"></canvas>
      <figcaption class="small mute">Dodecahedron and torus with per-object rotation speeds, through the desktop app's default camera angles.</figcaption></figure>
  </section>
  <div class="tiles">
    <div class="tile"><b>${info.basic}</b><span>basic shapes</span></div>
    <div class="tile"><b>${info.parametric}</b><span>parametric surfaces</span></div>
    <div class="tile"><b>${info.fractals}</b><span>fractal patterns</span></div>
    <div class="tile"><b>${info.characters}</b><span>text characters</span></div>
  </div>
  <div class="grid wide">${list(DOORS, ([href, t, d]) => `<a class="card door" href="${href}"><b>${t}</b><span>${d}</span></a>`)}</div>
  ${list(cat.groups, g => `<h2>${esc(g.title)}</h2><p>${list(g.names, n => `<a class="tag a" href="#/viewer?kind=${g.kind}&name=${encodeURIComponent(n)}">${esc(n)}</a>`)}</p>`)}`;
  hero(cat);
});

function hero(cat) {
  const canvas = document.getElementById('hero');
  const a = makeObject(buildShape('basic', 'Dodecahedron'), 'dodecahedron'), b = makeObject(buildShape('basic', 'Torus'), 'torus');
  a.position = [-1.3, 1.3, 0]; b.position = [1.3, -1.3, 0]; a.rotationSpeed = [0.3, 0.5, 0]; b.rotationSpeed = [0.6, 0, 0.25];
  const cam = frameScene([a, b], structuredClone(CAMERA_DEFAULTS)), objs = [a, b];
  const opts = { showFaces: true, showEdges: true, showVertices: false, shading: true, faceColor: cat.object_color.slice(0, 3).map(x => x * 255),
    edgeColor: [0, 0, 0], vertexColor: [255, 0, 0], edgeWidth: 1, vertexSize: 5, hoverColor: [255, 0, 0] };
  const draw = () => { const { ctx, w, h } = fitCanvas(canvas); drawScene(ctx, w, h, objs, cam, opts); };
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { a.rotation = [0.6, 1, 0]; b.rotation = [1.2, 0, 0.5]; draw(); return; }
  let last = null;
  animate(t => {
    const dt = last == null ? 0 : Math.min(0.05, (t - last) / 1000); last = t;
    for (const o of objs) for (let k = 0; k < 3; k++) o.rotation[k] += o.rotationSpeed[k] * dt;
    draw();
  });
}
