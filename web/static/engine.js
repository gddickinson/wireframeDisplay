// Scene engine: builds shapes by loader name, transforms scene objects, steps the physics and projects through the
// orbit camera. Ports of scene_math.py (SceneObject / Scene), camera.py (pyqtgraph GLViewWidget) and the OBJ / JSON
// file code in wireframe.py. Pure functions, no DOM: tested in node by engine.test.mjs.
import { BASIC, makeShape, faceArray } from './geometry.js';
import { PARAMETRIC, FRACTALS, createText } from './shapes_extra.js';
const { sin, cos, tan, PI, min, max } = Math;
const f32 = Math.fround;
const rad = d => d * PI / 180;

// kind: 'basic' | 'parametric' | 'fractal' | 'text'; params as the shape loader emits them.
export function buildShape(kind, name, params = [], glyphs = { glyphs: {} }) {
  if (kind === 'basic' && BASIC[name]) return BASIC[name]();
  if (kind === 'parametric' && PARAMETRIC[name]) return PARAMETRIC[name](...params);
  if (kind === 'fractal' && FRACTALS[name]) return FRACTALS[name](...params);
  if (kind === 'text') return createText(name, glyphs);
  throw new Error(`Unknown ${kind} shape: ${name}`);
}

// np.mean(float32 array, axis=0): float32 accumulation, row by row.
export function centreOf(vertices) {
  const s = [0, 0, 0];
  for (const v of vertices) for (let k = 0; k < 3; k++) s[k] = f32(s[k] + v[k]);
  return s.map(x => f32(x / vertices.length));
}

// scene_math.rotation_matrix: Rz . Ry . Rx
export function rotationMatrix([rx, ry, rz]) {
  const X = [[1, 0, 0], [0, cos(rx), -sin(rx)], [0, sin(rx), cos(rx)]];
  const Y = [[cos(ry), 0, sin(ry)], [0, 1, 0], [-sin(ry), 0, cos(ry)]];
  const Z = [[cos(rz), -sin(rz), 0], [sin(rz), cos(rz), 0], [0, 0, 1]];
  return mul3(Z, mul3(Y, X));
}
function mul3(A, B) {
  return A.map(row => [0, 1, 2].map(j => row[0] * B[0][j] + row[1] * B[1][j] + row[2] * B[2][j]));
}

// scene_math.transform_vertices: scale and rotate about centre, then translate.
export function transformVertices(vertices, centre, scale, rotation, position) {
  const R = rotationMatrix(rotation);
  return vertices.map(v => {
    const d = [0, 1, 2].map(k => f32(v[k] - centre[k]) * scale[k] + centre[k] - centre[k]);
    return [0, 1, 2].map(k => d[0] * R[k][0] + d[1] * R[k][1] + d[2] * R[k][2] + centre[k] + position[k]);
  });
}

// scene_math.physics_step: integrate, gravity on -z (the camera's up axis), bounce at z = 0 with restitution 0.8.
export const GRAVITY = 9.8, RESTITUTION = 0.8, UP = 2;
export function physicsStep(o, dt) {
  for (let k = 0; k < 3; k++) { o.position[k] += o.velocity[k] * dt; o.rotation[k] += o.angularVelocity[k] * dt; }
  o.velocity[UP] -= GRAVITY * dt;
  if (o.position[UP] < 0) { o.position[UP] = 0; o.velocity[UP] = -o.velocity[UP] * RESTITUTION; }
}

// --- camera (camera.py = pyqtgraph GLViewWidget) ---------------------------------------------------------------------
export const CAMERA_DEFAULTS = { distance: 10, elevation: 30, azimuth: 45, fov: 60, center: [0, 0, 0] };
const I4 = () => [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]];
const mul4 = (A, B) => A.map(row => [0, 1, 2, 3].map(j => row[0] * B[0][j] + row[1] * B[1][j] + row[2] * B[2][j] + row[3] * B[3][j]));
function translate4(x, y, z) { const m = I4(); m[0][3] = x; m[1][3] = y; m[2][3] = z; return m; }
function rotate4(deg, x, y, z) {
  const a = rad(deg), n = Math.hypot(x, y, z), u = [x / n, y / n, z / n], c = cos(a), s = sin(a);
  const K = [[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]], m = I4();
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) m[i][j] = c * (i === j) + s * K[i][j] + (1 - c) * u[i] * u[j];
  return m;
}
export function viewMatrix({ distance, elevation, azimuth, center = [0, 0, 0] }) {
  return mul4(mul4(mul4(translate4(0, 0, -distance), rotate4(elevation - 90, 1, 0, 0)), rotate4(azimuth + 90, 0, 0, -1)),
    translate4(-center[0], -center[1], -center[2]));
}
export function projectionMatrix({ distance, fov }, width, height) {
  const n = distance * 0.001, f = distance * 1000, r = n * tan(0.5 * rad(fov)), t = r * height / width;
  return [[n / r, 0, 0, 0], [0, n / t, 0, 0], [0, 0, -(f + n) / (f - n), -2 * f * n / (f - n)], [0, 0, -1, 0]];
}
// World points -> { xy: [[px, py]] (y down), depth: [eye-space distance] }
export function project(points, cam, width, height) {
  const V = viewMatrix(cam), P = projectionMatrix(cam, width, height), M = mul4(P, V);
  const xy = [], depth = [];
  for (const [x, y, z] of points) {
    const e2 = V[2][0] * x + V[2][1] * y + V[2][2] * z + V[2][3];
    const c = [0, 1, 3].map(i => M[i][0] * x + M[i][1] * y + M[i][2] * z + M[i][3]);
    xy.push([(c[0] / c[2] + 1) * 0.5 * width, (1 - c[1] / c[2]) * 0.5 * height]);
    depth.push(-e2);
  }
  return { xy, depth };
}
// GLViewWidget.orbit (a left-drag calls orbit(-dx, dy)) and wheelEvent (distance *= 0.999 ** delta).
export function orbit(cam, dAzim, dElev) { cam.azimuth += dAzim; cam.elevation = min(90, max(-90, cam.elevation + dElev)); return cam; }
export function zoom(cam, delta) { cam.distance *= 0.999 ** delta; return cam; }

// --- files (Wireframe.load_from_obj / save_to_obj / save_to_json / load_from_json) -----------------------------------
export function parseObj(text) {
  const v = [], f = [];
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('v ')) v.push(line.trim().split(/\s+/).slice(1, 4).map(Number));
    else if (line.startsWith('f ')) f.push(line.trim().split(/\s+/).slice(1).map(x => parseInt(x.split('/')[0], 10) - 1));
  }
  if (v.some(p => p.length < 3 || p.some(Number.isNaN))) throw new Error('bad vertex line in OBJ file');
  return makeShape(v, f);
}
export function toObj(vertices, faces) {
  return vertices.map(p => `v ${p.join(' ')}`).concat((faces || []).map(fc => 'f ' + fc.map(i => i + 1).join(' '))).join('\n') + '\n';
}
export function toJson(vertices, faces) { return JSON.stringify({ vertices, faces: faces && faces.length ? faces : null, edges: null }); }
export function parseJson(text) {
  const d = JSON.parse(text);
  if (!Array.isArray(d.vertices)) throw new Error('JSON needs a "vertices" list');
  const shape = makeShape(d.vertices, d.faces || []);
  shape.faces = faceArray(d.faces || [], shape.vertices.length) || [];
  return shape;
}
