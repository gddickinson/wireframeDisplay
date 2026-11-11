// Viewer page: the desktop WireframeViewer window in the browser. Scene and shapes come from the JS engine; the
// panel lives in viewer_panel.js. Mouse: press on an object and drag to rotate it (Shift/Ctrl + drag moves it), as in
// the desktop app; drag on empty space orbits the camera and the wheel zooms, as pyqtgraph's GLViewWidget does.
import { route, app, animate, $ } from './core.js';
import { orbit, zoom, physicsStep, CAMERA_DEFAULTS } from './engine.js';
import { drawScene, fitCanvas, pick, rgb } from './render.js';
import { loadSetup, frameScene } from './scene.js';
import { panelHTML, wirePanel } from './viewer_panel.js';

route('viewer', async (_args, query) => {
  const { cat } = await loadSetup();
  const [tmin, tmax, tinit, tstep] = cat.translation_slider, [smin, smax, sinit, sstep] = cat.scale_slider;
  const slider = (id, label, min, max, v, step) => `<div class="ctl"><label for="${id}">${label} <b id="${id}v">${(+v).toFixed(1)}</b></label>
    <input type="range" id="${id}" min="${min}" max="${max}" step="${step}" value="${v}"></div>`;
  app().innerHTML = `<p class="kicker">Viewer</p><h1 class="glow">3D Wireframe Viewer</h1>
  <p class="lead">Load shapes into the scene, drag to turn them or orbit the camera, scroll to zoom, animate and drop them with gravity.</p>
  <div class="vw">
    <aside class="controls" aria-label="Viewer controls">${panelHTML(cat)}</aside>
    <section class="view">
      <canvas id="view" tabindex="0" role="img" aria-label="3D view of the scene. Arrow keys orbit the camera, plus and minus zoom, F frames the scene."></canvas>
      <div class="btnrow"><span class="seg" role="group" aria-label="Drag mode">
        <button data-m="auto" class="on">Drag: auto</button><button data-m="camera">Camera</button><button data-m="object">Object</button></span>
        <button class="alt" id="zin" aria-label="Zoom in">+</button><button class="alt" id="zout" aria-label="Zoom out">−</button>
        <button class="alt" id="frame">Frame scene</button><button class="alt" id="rcam">Reset camera</button></div>
      <p class="readout" id="camread"></p>
      <p class="small mute">Play runs the scene physics: gravity along −y and a bounce at y = 0 (raise objects with the Y slider first).</p>
      <h3>Transformation (applies to every object)</h3>
      <div class="sliders">${slider('tx', 'X', tmin, tmax, tinit, tstep)}${slider('ty', 'Y', tmin, tmax, tinit, tstep)}${slider('tz', 'Z', tmin, tmax, tinit, tstep)}${slider('ts', 'Scale', smin, smax, sinit, sstep)}</div>
      <button class="alt" id="reset">Reset transformation</button>
    </section>
  </div>`;

  const S = { objects: [], selected: -1, hovered: null, cam: structuredClone(CAMERA_DEFAULTS), playing: false, mode: 'auto',
    opts: { hoverColor: cat.hover_color.slice(0, 3).map(x => x * 255), background: '#000' }, last: null };
  const canvas = $('#view');
  let dirty = true;
  const redraw = () => { dirty = true; };
  wirePanel(S, cat, redraw);

  // transformation sliders: WireframeViewer.apply_transformation resets every object to this position and scale
  const apply = () => {
    const t = ['tx', 'ty', 'tz'].map(id => +$('#' + id).value), s = +$('#ts').value;
    ['tx', 'ty', 'tz', 'ts'].forEach(id => { $('#' + id + 'v').textContent = (+$('#' + id).value).toFixed(1); });
    for (const o of S.objects) { o.position = [...t]; o.scale = [s, s, s]; }
    redraw();
  };
  ['tx', 'ty', 'tz', 'ts'].forEach(id => $('#' + id).addEventListener('input', apply));
  $('#reset').addEventListener('click', () => {
    ['tx', 'ty', 'tz'].forEach(id => { $('#' + id).value = tinit; }); $('#ts').value = sinit;
    for (const o of S.objects) { o.position = [0, 0, 0]; o.scale = [1, 1, 1]; o.rotation = [0, 0, 0]; o.velocity = [0, 0, 0]; }
    apply();
  });

  // camera buttons and drag mode
  document.querySelectorAll('.seg button[data-m]').forEach(b => b.addEventListener('click', () => {
    S.mode = b.dataset.m; document.querySelectorAll('.seg button[data-m]').forEach(x => x.classList.toggle('on', x === b));
  }));
  $('#zin').addEventListener('click', () => { zoom(S.cam, 120); redraw(); });
  $('#zout').addEventListener('click', () => { zoom(S.cam, -120); redraw(); });
  $('#frame').addEventListener('click', () => { frameScene(S.objects, S.cam, canvas.clientHeight / Math.max(1, canvas.clientWidth)); redraw(); });
  $('#rcam').addEventListener('click', () => { S.cam = structuredClone(CAMERA_DEFAULTS); redraw(); });

  // mouse / touch
  let drag = null;
  const at = e => { const r = canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top, r.width, r.height]; };
  canvas.addEventListener('pointerdown', e => {
    const [x, y, w, h] = at(e);
    const hit = S.mode === 'camera' ? null : pick(S.objects, S.cam, w, h, x, y);
    if (hit) { S.selected = S.objects.indexOf(hit); S.refreshList(); }
    drag = { x, y, obj: S.mode === 'object' ? (hit || S.objects[S.selected]) : hit };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', e => {
    const [x, y, w, h] = at(e);
    if (!drag) {
      const hov = pick(S.objects, S.cam, w, h, x, y);
      if (hov !== S.hovered) { S.hovered = hov; redraw(); }
      return;
    }
    const dx = x - drag.x, dy = y - drag.y;
    drag.x = x; drag.y = y;
    if (drag.obj) { // WireframeViewer.mouseMoveEvent
      const o = drag.obj;
      if (e.ctrlKey || e.shiftKey) { o.position[0] += -dx * 0.01; o.position[1] += dy * 0.01; } else { o.rotation[0] += -dy * 0.01; o.rotation[1] += -dx * 0.01; }
    } else orbit(S.cam, -dx, dy); // GLViewWidget.mouseMoveEvent
    redraw();
  });
  const end = () => { drag = null; };
  canvas.addEventListener('pointerup', end); canvas.addEventListener('pointercancel', end);
  canvas.addEventListener('pointerleave', () => { if (!drag && S.hovered) { S.hovered = null; redraw(); } });
  canvas.addEventListener('wheel', e => { e.preventDefault(); zoom(S.cam, Math.max(-240, Math.min(240, -e.deltaY * 1.2))); redraw(); }, { passive: false });
  canvas.addEventListener('keydown', e => {
    const k = { ArrowLeft: [5, 0], ArrowRight: [-5, 0], ArrowUp: [0, -5], ArrowDown: [0, 5] }[e.key];
    if (k) orbit(S.cam, ...k);
    else if (e.key === '+' || e.key === '=') zoom(S.cam, 120);
    else if (e.key === '-') zoom(S.cam, -120);
    else if (e.key === 'f' || e.key === 'F') frameScene(S.objects, S.cam, canvas.clientHeight / Math.max(1, canvas.clientWidth));
    else return;
    e.preventDefault(); redraw();
  });

  // render loop: per-object rotation animation (SceneObject.update_animation) and, while playing, physics
  animate(t => {
    const dt = S.last == null ? 0 : Math.min(0.05, (t - S.last) / 1000);
    S.last = t;
    for (const o of S.objects) if (o.animated) { for (let k = 0; k < 3; k++) o.rotation[k] += o.rotationSpeed[k] * dt; dirty = true; }
    if (S.playing && S.objects.length) { for (const o of S.objects) physicsStep(o, dt); dirty = true; }
    if (!dirty) return;
    dirty = false;
    const { ctx, w, h } = fitCanvas(canvas);
    drawScene(ctx, w, h, S.objects, S.cam, S.opts, S.hovered);
    const c = S.cam;
    $('#camread').innerHTML = `distance <b>${c.distance.toFixed(2)}</b> · elevation <b>${c.elevation.toFixed(0)}°</b> · azimuth <b>${(c.azimuth % 360).toFixed(0)}°</b> · fov ${c.fov}° · ${S.objects.length} object${S.objects.length === 1 ? '' : 's'}`;
    if (S.hovered) ctx.fillStyle = rgb(S.opts.hoverColor), ctx.font = '12px ui-monospace, monospace', ctx.fillText(S.hovered.name, 8, 18);
  });
  addEventListener('resize', redraw);

  // start with the shape named in the URL (from the Shapes page), or one icosahedron
  const k = query.kind || 'basic', name = query.name || 'Icosahedron', g = cat.shapes.find(s => s.kind === k && s.name === name);
  await S.add(k, name, g ? g.params : []);
  if (query.kind) frameScene(S.objects, S.cam, canvas.clientHeight / Math.max(1, canvas.clientWidth));
});
