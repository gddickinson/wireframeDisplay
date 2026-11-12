// Cross-check: shapes built by the JS engine in this browser against the same shapes built by wireframe.py on the
// server (on the static site: built by the Python code when the site was exported).
import { route, app, api, esc, isStatic } from './core.js';
import { buildShape } from './engine.js';
import { loadSetup } from './scene.js';

route('check', async () => {
  const { cat } = await loadSetup();
  app().innerHTML = `<p class="kicker">Cross-check</p><h1 class="glow">JS engine vs Python</h1>
  <p class="lead">Each row builds the shape twice: in your browser with the JS port, and with the desktop app's
  <code>Wireframe</code> class in Python (${isStatic() ? 'exported when this static site was built' : 'live from the local server'}).
  The Python vertices are float32 and sent rounded to 7 decimals, so differences up to 5 × 10⁻⁸ are rounding.</p>
  <p>The repository's node test (<code>web/static/engine.test.mjs</code>) goes further: it checks every generator, the object
  transforms, 150 physics steps and the pyqtgraph camera matrices against <code>tests/fixtures/engine_fixture.json</code>,
  which <code>scripts/make_engine_fixture.py</code> writes from the Python code; agreement is within 10⁻¹².</p>
  <div class="scroll"><table><thead><tr><th>Shape</th><th>Parameters</th><th>Vertices</th><th>Faces</th><th>Max |Δ|</th><th>Result</th></tr></thead>
  <tbody id="rows"></tbody></table></div><p id="summary" class="mono"></p>`;
  let ok = 0, n = 0;
  for (const s of cat.shapes) {
    const row = document.createElement('tr');
    document.getElementById('rows').appendChild(row);
    try {
      const py = await api('/shape/' + s.slug);
      if (s.server_only) {
        row.innerHTML = `<td>${esc(s.name)}</td><td class="mono">${py.params.join(', ')}</td><td>${py.vertices.length}</td><td>${py.faces.length}</td><td>-</td><td class="mute">Python only (marching cubes)</td>`;
        continue;
      }
      const js = buildShape(s.kind, s.name, s.params, cat.glyphs);
      let d = 0;
      js.vertices.forEach((v, i) => v.forEach((x, k) => { d = Math.max(d, Math.abs(x - py.vertices[i][k])); }));
      const same = js.vertices.length === py.vertices.length && JSON.stringify(js.faces) === JSON.stringify(py.faces) && d < 1e-6;
      n++; ok += same;
      row.innerHTML = `<td>${esc(s.name)}</td><td class="mono">${s.params.join(', ') || '-'}</td><td>${js.vertices.length} / ${py.vertices.length}</td>
        <td>${js.faces.length} / ${py.faces.length}</td><td class="mono">${d.toExponential(1)}</td><td class="${same ? 'ok' : 'bad'}">${same ? 'match' : 'DIFFERENT'}</td>`;
    } catch (err) { row.innerHTML = `<td>${esc(s.name)}</td><td colspan="5" class="err">${esc(err.message)}</td>`; }
  }
  document.getElementById('summary').textContent = `${ok} of ${n} shapes match (vertex counts JS / Python, identical faces).`;
});
