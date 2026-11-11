// Viewer control panel: the desktop app's left panel (scene list, Load Shape, Remove, Play), its shape loader
// dialog, File > Open / Save, the Display Options dialog and the object Properties dialog, as one HTML form.
import { esc, list, $, download } from './core.js';
import { parseObj, parseJson, toObj, toJson } from './engine.js';
import { hexToRgb, rgbToHex } from './render.js';
import { makeObject, loadShape, objectName } from './scene.js';

const num = (id, label, v, min, max, step) =>
  `<div><label for="${id}">${label}</label><input type="number" id="${id}" value="${v}" min="${min}" max="${max}" step="${step}"></div>`;

export function panelHTML(cat) {
  const d = cat.display, [rmin, rmax, rdef] = cat.resolution, [imin, , idef] = cat.iterations, [smin, smax, sdef, sstep] = cat.size;
  return `
  <h3>Scene objects</h3>
  <ul class="objlist" id="objlist" aria-label="Scene objects"></ul>
  <div class="btnrow"><button class="alt" id="rm">Remove</button><button class="alt" id="ren">Rename</button>
    <button class="alt" id="anim">Toggle animation</button><button id="play">Play</button></div>
  <p class="small mute" id="status" role="status"></p>
  <h3>Load shape</h3>
  <label for="grp">Group</label><select id="grp">${list(cat.groups, g => `<option value="${g.kind}">${esc(g.title)}</option>`)}<option value="text">Text Shapes</option></select>
  <div id="namebox"><label for="shape">Shape</label><select id="shape"></select></div>
  <div class="props" id="pparams">${num('pu', 'U resolution', rdef, rmin, rmax, 1)}${num('pv', 'V resolution', rdef, rmin, rmax, 1)}</div>
  <div class="props" id="fparams">${num('fit', 'Iterations', idef, imin, 8, 1)}${num('fsz', 'Size', sdef, smin, smax, sstep)}</div>
  <div id="tparams"><label for="txt">Text (defined: ${esc(Object.keys(cat.letters).sort().join(' '))})</label><input id="txt" maxlength="40" value="AB0!"></div>
  <p class="small mute" id="capnote"></p>
  <button id="load">Load shape</button>
  <h3>File</h3>
  <label for="open">Open an .obj or .json file</label><input type="file" id="open" accept=".obj,.json">
  <div class="btnrow"><button class="alt" id="sobj">Save OBJ</button><button class="alt" id="sjson">Save JSON</button></div>
  <h3>Display options</h3>
  <div class="checks"><label><input type="checkbox" id="sf" ${d.show_faces ? 'checked' : ''}> Faces</label>
    <label><input type="checkbox" id="se" ${d.show_edges ? 'checked' : ''}> Edges</label>
    <label><input type="checkbox" id="sv" ${d.show_vertices ? 'checked' : ''}> Vertices</label>
    <label><input type="checkbox" id="sh" checked> Shading (web)</label></div>
  <div class="colours"><div><label for="cf">Faces</label><input type="color" id="cf" value="${rgbToHex(cat.object_color.slice(0, 3).map(x => x * 255))}"></div>
    <div><label for="ce">Edges</label><input type="color" id="ce" value="${rgbToHex(d.edge_color)}"></div>
    <div><label for="cv">Vertices</label><input type="color" id="cv" value="${rgbToHex(d.vertex_color)}"></div></div>
  <div class="props">${num('ew', 'Edge width', d.edge_width[2], d.edge_width[0], d.edge_width[1], 1)}${num('vs', 'Vertex size', d.vertex_size[2], d.vertex_size[0], d.vertex_size[1], 1)}</div>
  <h3>Properties of the selected object</h3>
  <div id="props"></div>`;
}

export function wirePanel(S, cat, redraw) {
  const status = msg => { $('#status').textContent = msg; };
  const sel = () => S.objects[S.selected] || null;

  function refreshList() {
    $('#objlist').innerHTML = S.objects.length
      ? list(S.objects, (o, i) => `<li><button data-i="${i}" class="${i === S.selected ? 'on' : ''}" aria-pressed="${i === S.selected}">${esc(o.name)}${o.animated ? ' ⟳' : ''}</button></li>`)
      : '<li class="empty">No objects: load a shape below.</li>';
    $('#play').textContent = S.playing ? 'Pause' : 'Play';
    props();
  }
  S.refreshList = refreshList;
  $('#objlist').addEventListener('click', e => {
    const b = e.target.closest('button[data-i]');
    if (b) { S.selected = +b.dataset.i; refreshList(); redraw(); }
  });
  $('#objlist').addEventListener('dblclick', e => { // WireframeViewer.center_view_on_object
    const b = e.target.closest('button[data-i]'), o = b && S.objects[+b.dataset.i];
    if (o) { S.cam.center = o.centre.map((x, k) => x + o.position[k]); redraw(); }
  });

  // --- loader ---------------------------------------------------------------------------------------------------
  const kind = () => $('#grp').value;
  function syncLoader() {
    const k = kind(), g = cat.groups.find(x => x.kind === k);
    $('#namebox').hidden = k === 'text'; $('#tparams').hidden = k !== 'text';
    $('#pparams').hidden = k !== 'parametric'; $('#fparams').hidden = k !== 'fractal';
    if (g) $('#shape').innerHTML = list(g.names, n => `<option>${esc(n)}</option>`);
    syncCap();
  }
  function syncCap() {
    const cap = cat.web_iteration_caps[$('#shape').value];
    $('#fit').max = cap || 8;
    $('#capnote').textContent = kind() === 'fractal' && cap < 8 ? `The desktop allows 1-8 iterations; the browser stops at ${cap} for this fractal.` : '';
  }
  $('#grp').addEventListener('change', syncLoader);
  $('#shape').addEventListener('change', syncCap);
  syncLoader();

  async function add(k, name, params) {
    try {
      const shape = await loadShape(k, name, params, cat);
      S.objects.push(makeObject(shape, objectName(k, name, params)));
      S.selected = S.objects.length - 1;
      status(`Loaded ${S.objects[S.selected].name}: ${shape.vertices.length} vertices, ${shape.faces.length} faces.`);
      refreshList(); redraw();
    } catch (err) { status(`Failed to load shape: ${err.message}`); }
  }
  S.add = add;
  $('#load').addEventListener('click', () => {
    const k = kind(), clamp = (el) => Math.min(+el.max, Math.max(+el.min, +el.value || +el.min));
    if (k === 'text') return $('#txt').value ? add('text', $('#txt').value, []) : status('Please enter some text');
    if (k === 'basic') return add(k, $('#shape').value, []);
    if (k === 'parametric') return add(k, $('#shape').value, [Math.round(clamp($('#pu'))), Math.round(clamp($('#pv')))]);
    return add(k, $('#shape').value, [Math.round(clamp($('#fit'))), clamp($('#fsz'))]);
  });

  // --- scene list buttons ---------------------------------------------------------------------------------------
  $('#rm').addEventListener('click', () => {
    if (!sel()) return status('Select an object first.');
    S.objects.splice(S.selected, 1); S.selected = Math.min(S.selected, S.objects.length - 1); refreshList(); redraw();
  });
  $('#ren').addEventListener('click', () => {
    const o = sel(); if (!o) return status('Select an object first.');
    const n = prompt('Enter new name:', o.name); if (n) { o.name = n; refreshList(); }
  });
  $('#anim').addEventListener('click', () => {
    const o = sel(); if (!o) return status('Select an object first.');
    o.animated = !o.animated;
    status(o.animated && !o.rotationSpeed.some(Boolean) ? 'Animation on: set a rotation speed in Properties to see it turn.' : '');
    refreshList();
  });
  $('#play').addEventListener('click', () => { S.playing = !S.playing; S.last = null; refreshList(); });

  // --- files -----------------------------------------------------------------------------------------------------
  $('#open').addEventListener('change', async e => {
    const f = e.target.files[0]; if (!f) return;
    try {
      const text = await f.text(), shape = f.name.toLowerCase().endsWith('.json') ? parseJson(text) : parseObj(text);
      S.objects.push(makeObject(shape, `file: ${f.name}`)); S.selected = S.objects.length - 1;
      status(`Opened ${f.name}: ${shape.vertices.length} vertices, ${shape.faces.length} faces.`); refreshList(); redraw();
    } catch (err) { status(`Failed to open file: ${err.message}`); }
    e.target.value = '';
  });
  const save = (fmt) => {
    const o = sel() || S.objects[S.objects.length - 1]; if (!o) return status('No wireframe to save');
    const base = o.name.replace(/[^\w.-]+/g, '_').replace(/^_+|_+$/g, '') || 'wireframe';
    if (fmt === 'obj') download(base + '.obj', toObj(o.shape.vertices, o.shape.faces));
    else download(base + '.json', toJson(o.shape.vertices, o.shape.faces), 'application/json');
  };
  $('#sobj').addEventListener('click', () => save('obj'));
  $('#sjson').addEventListener('click', () => save('json'));

  // --- display options -------------------------------------------------------------------------------------------
  const syncDisplay = () => {
    Object.assign(S.opts, {
      showFaces: $('#sf').checked, showEdges: $('#se').checked, showVertices: $('#sv').checked, shading: $('#sh').checked,
      faceColor: hexToRgb($('#cf').value), edgeColor: hexToRgb($('#ce').value), vertexColor: hexToRgb($('#cv').value),
      edgeWidth: +$('#ew').value || 1, vertexSize: +$('#vs').value || 5,
    });
    redraw();
  };
  ['sf', 'se', 'sv', 'sh', 'cf', 'ce', 'cv', 'ew', 'vs'].forEach(id => $('#' + id).addEventListener('input', syncDisplay));
  syncDisplay();

  // --- properties (ObjectPropertiesDialog) -----------------------------------------------------------------------
  function props() {
    const o = sel(), host = $('#props');
    if (!o) { host.innerHTML = '<p class="small mute">Select an object in the list.</p>'; return; }
    const r = cat.property_ranges, [smin, smax, sst] = r.scale, [wmin, wmax, wst] = r.rotation_speed;
    host.innerHTML = `<label for="pn">Name</label><input id="pn" value="${esc(o.name)}">
      <div class="props">${num('pm', 'Mass', o.mass, r.mass[0], r.mass[1], 0.1)}</div>
      <div class="props">${['X', 'Y', 'Z'].map((a, k) => num('psc' + k, 'Scale ' + a, o.scale[k], smin, smax, sst)).join('')}</div>
      <div class="props">${['X', 'Y', 'Z'].map((a, k) => num('prs' + k, 'Spin ' + a + ' (rad/s)', o.rotationSpeed[k], wmin, wmax, wst)).join('')}</div>
      <button id="papply">Apply</button>`;
    $('#papply').addEventListener('click', () => {
      const c = (id, lo, hi) => Math.min(hi, Math.max(lo, +$('#' + id).value || 0));
      o.name = $('#pn').value || o.name;
      o.mass = Math.max(0.1, c('pm', r.mass[0], r.mass[1]));
      o.scale = [0, 1, 2].map(k => c('psc' + k, smin, smax));
      o.rotationSpeed = [0, 1, 2].map(k => c('prs' + k, wmin, wmax));
      refreshList(); redraw();
    });
  }
  refreshList();
}
