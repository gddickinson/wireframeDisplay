// Shapes page: every loader entry drawn by the JS engine (the Gyroid by the Python server), with its size.
import { route, app, esc, list } from './core.js';
import { CAMERA_DEFAULTS } from './engine.js';
import { drawScene, fitCanvas } from './render.js';
import { loadSetup, loadShape, makeObject, frameScene } from './scene.js';

route('shapes', async () => {
  const { cat } = await loadSetup();
  const items = cat.shapes.concat([{ kind: 'text', name: 'WIRE 3D', params: [], slug: 'text' }]);
  const caption = s => s.kind === 'parametric' ? `U × V = ${s.params[0]} × ${s.params[1]}` : s.kind === 'fractal' ? `${s.params[0]} iterations, size ${s.params[1]}` : s.kind === 'text' ? 'Text Shapes: "WIRE 3D"' : 'loader defaults';
  app().innerHTML = `<p class="kicker">Shape loader</p><h1 class="glow">Shapes</h1>
  <p class="lead">The ${cat.shapes.length} generators of the desktop shape loader plus text, each built in your browser by the JS port of
  <code>wireframe.py</code> (the Gyroid, which needs scikit-image's marching cubes, comes from the Python server). Click one to open it in the viewer.</p>
  ${list(cat.groups.concat([{ kind: 'text', title: 'Text Shapes' }]), g => `<h2>${esc(g.title)}</h2><div class="grid gal">${list(items.filter(s => s.kind === g.kind), s => `
    <a class="card" href="#/viewer?kind=${s.kind}&name=${encodeURIComponent(s.name)}"><canvas data-slug="${s.slug}" role="img" aria-label="${esc(s.name)}"></canvas>
    <b>${esc(s.name)}</b><small id="n-${s.slug}">${caption(s)}</small></a>`)}</div>`)}`;
  const opts = { showFaces: true, showEdges: true, showVertices: false, shading: true, faceColor: cat.object_color.slice(0, 3).map(x => x * 255),
    edgeColor: [0, 0, 0], vertexColor: [255, 70, 70], edgeWidth: 1, vertexSize: 2, hoverColor: [255, 0, 0] };
  for (const s of items) {
    const canvas = app().querySelector(`canvas[data-slug="${s.slug}"]`);
    try {
      const shape = await loadShape(s.kind, s.name, s.params, cat), o = makeObject(shape, s.name);
      const cam = frameScene([o], structuredClone(CAMERA_DEFAULTS)), { ctx, w, h } = fitCanvas(canvas);
      drawScene(ctx, w, h, [o], cam, { ...opts, showEdges: shape.faces.length < 3000 });
      document.getElementById('n-' + s.slug).textContent += ` · ${shape.vertices.length} vertices, ${shape.faces.length} faces`;
    } catch (err) { canvas.replaceWith(Object.assign(document.createElement('p'), { className: 'err small', textContent: err.message })); }
  }
});
