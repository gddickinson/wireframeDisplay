// Scene objects and shape loading shared by the pages. A scene object mirrors SceneObject in wireframe_viewer.py:
// shape (vertices + faces), centre (mean vertex), position, rotation (radians), scale, velocity, angular velocity,
// mass, rotation speed and the "animated" flag of Toggle Animation.
import { api } from './core.js';
import { buildShape, centreOf, CAMERA_DEFAULTS } from './engine.js';
import { worldVertices } from './render.js';

let setup = null;
export async function loadSetup() {
  if (!setup) setup = Promise.all([api('/info'), api('/catalog')]).then(([info, cat]) => ({ info, cat }));
  return setup;
}

export function makeObject(shape, name) {
  return {
    shape, name, centre: centreOf(shape.vertices), position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1],
    velocity: [0, 0, 0], angularVelocity: [0, 0, 0], mass: 1.0, rotationSpeed: [0, 0, 0], animated: false, color: null,
  };
}

// Build a loader entry in the browser (JS port), or fetch it from the Python server (Gyroid: marching cubes).
export async function loadShape(kind, name, params, cat) {
  if (kind === 'parametric' && name === 'Gyroid') {
    const slug = 'gyroid', [u, v] = params, def = cat.resolution[2];
    const d = await api(`/shape/${slug}` + (u === def && v === def ? '' : `?u=${u}&v=${v}`));
    return { vertices: d.vertices, faces: d.faces };
  }
  return buildShape(kind, name, params, cat.letters);
}

// The loader names objects "<kind>: <info>" (WireframeViewer.on_shape_loaded).
export function objectName(kind, name, params) {
  if (kind === 'basic' || kind === 'text') return `${kind}: ${name}`;
  const py = x => (Number.isInteger(x) ? `${x}.0` : String(x)); // Python prints the float size as 1.0
  const [a, b] = params;
  return `${kind}: ('${name}', ${a}, ${kind === 'fractal' ? py(b) : b})`;
}

// Web addition: point the camera at the middle of the scene and pull back until everything fits.
export function frameScene(objects, cam, aspect = 0.75) { // aspect = height / width of the view
  const pts = objects.flatMap(o => worldVertices(o));
  if (!pts.length) return Object.assign(cam, structuredClone(CAMERA_DEFAULTS));
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const p of pts) for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], p[k]); hi[k] = Math.max(hi[k], p[k]); }
  cam.center = lo.map((x, k) => (x + hi[k]) / 2);
  const radius = Math.max(1e-6, Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / 2);
  const half = Math.atan(Math.tan(cam.fov * Math.PI / 360) * Math.min(1, aspect)); // fov is horizontal
  cam.distance = radius / Math.sin(half) * 1.1;
  return cam;
}
