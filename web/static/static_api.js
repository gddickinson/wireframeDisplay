// Static-site data layer: answers api() calls from the JSON files exported by scripts/build_static.py.
// /shape/<slug> exists at the loader defaults only (built by the Python generators at build time); other parameters
// and /text need the local Python server. The viewer builds every shape except the Gyroid in the browser anyway.
const files = new Map();
async function file(rel) {
  if (!files.has(rel)) files.set(rel, fetch('api/' + rel + '.json').then(r => { if (!r.ok) throw new Error(`${r.status} ${rel}`); return r.json(); }));
  return files.get(rel);
}

export async function staticApi(path) {
  const [p, qs] = path.split('?');
  const clean = p.replace(/^\/+/, '');
  if ((clean.startsWith('shape/') && qs) || clean.startsWith('text'))
    throw new Error('Shapes at other parameters from the Python generator need the local app (Python server).');
  return file(clean);
}
