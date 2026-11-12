// Parametric surfaces, fractals and text: a line-by-line port of the matching Wireframe.create_* methods in
// wireframe.py (same parameter order, same vertex and face order). The Gyroid needs scikit-image's marching cubes,
// so it is computed by the Python server instead (api/shape/gyroid.json on the static site).
import { linspace, makeShape } from './geometry.js';
const { sin, cos, sqrt, cosh, acos, PI, max, floor, abs } = Math;
const f32 = Math.fround;

// u x v grid surface: vertex index j * uRes + i (np.meshgrid + flatten), quad faces.
function gridSurface(u0, u1, v0, v1, uRes, vRes, fn) {
  const us = linspace(u0, u1, uRes), vs = linspace(v0, v1, vRes), verts = [], faces = [];
  for (let j = 0; j < vRes; j++) for (let i = 0; i < uRes; i++) verts.push(fn(us[i], vs[j]));
  for (let i = 0; i < uRes - 1; i++) for (let j = 0; j < vRes - 1; j++)
    faces.push([j * uRes + i, j * uRes + i + 1, (j + 1) * uRes + i + 1, (j + 1) * uRes + i]);
  return makeShape(verts, faces);
}

export const mobiusStrip = (uRes = 30, vRes = 10) => gridSurface(0, 2 * PI, -1, 1, uRes, vRes,
  (u, v) => [(1 + v / 2 * cos(u / 2)) * cos(u), (1 + v / 2 * cos(u / 2)) * sin(u), v / 2 * sin(u / 2)]);
export const kleinBottle = (uRes = 30, vRes = 30) => gridSurface(0, 2 * PI, 0, 2 * PI, uRes, vRes, (u, v) => {
  const k = 2.5 + cos(u / 2) * sin(v) - sin(u / 2) * sin(2 * v);
  return [k * cos(u), k * sin(u), sin(u / 2) * sin(v) + cos(u / 2) * sin(2 * v)];
});
export const helicoid = (uRes = 30, vRes = 30) => gridSurface(-PI, PI, -1, 1, uRes, vRes, (u, v) => [v * cos(u), v * sin(u), u]);
export const catenoid = (uRes = 30, vRes = 30) => gridSurface(-PI, PI, -1, 1, uRes, vRes, (u, v) => [cosh(v) * cos(u), cosh(v) * sin(u), v]);
export const sineSurface = (uRes = 30, vRes = 30) => gridSurface(0, 2 * PI, 0, 2 * PI, uRes, vRes, (u, v) => [sin(u), sin(v), sin(u + v)]);

// Wireframe.rotation_matrix(axis, theta): Euler-Rodrigues.
export function axisRotation(axis, theta) {
  const n = sqrt(axis[0] * axis[0] + axis[1] * axis[1] + axis[2] * axis[2]);
  const ax = axis.map(x => x / n), a = cos(theta / 2), s = sin(theta / 2);
  const [b, c, d] = ax.map(x => -x * s);
  const aa = a * a, bb = b * b, cc = c * c, dd = d * d, bc = b * c, ad = a * d, ac = a * c, ab = a * b, bd = b * d, cd = c * d;
  return [[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)], [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
    [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]];
}

// Tube of 8-point circles around (2 + cos 3t)(cos 2t, sin 2t) + sin 3t z, t in [0, 2pi). tubeRadius defaults to 0.3.
export function trefoilKnot(uRes = 100, tubeRadius = 0.3) {
  const ts = linspace(0, 2 * PI, uRes, false), res = 8, ct = linspace(0, 2 * PI, res);
  const knot = ts.map(t => [(2 + cos(3 * t)) * cos(2 * t), (2 + cos(3 * t)) * sin(2 * t), sin(3 * t)]);
  const verts = [], faces = [];
  for (let i = 0; i < uRes; i++) {
    const c0 = knot[i], c1 = knot[(i + 1) % uRes], raw = [c1[0] - c0[0], c1[1] - c0[1], c1[2] - c0[2]];
    const len = Math.sqrt(raw[0] ** 2 + raw[1] ** 2 + raw[2] ** 2), nrm = raw.map(x => x / len);
    const R = axisRotation([0 * nrm[2] - 1 * nrm[1], 1 * nrm[0] - 0 * nrm[2], 0 * nrm[1] - 0 * nrm[0]], acos(nrm[2]));
    for (const t of ct) {
      const p = [tubeRadius * cos(t), tubeRadius * sin(t), 0];
      verts.push(R.map((row, k) => p[0] * row[0] + p[1] * row[1] + p[2] * row[2] + c0[k]));
    }
    for (let j = 0; j < res; j++) {
      const nj = (j + 1) % res, n = (i + 1) % uRes;
      faces.push([i * res + j, i * res + nj, n * res + nj, n * res + j]);
    }
  }
  return makeShape(verts, faces);
}

export const PARAMETRIC = {
  'Mobius Strip': mobiusStrip, 'Klein Bottle': kleinBottle, 'Trefoil Knot': u => trefoilKnot(u), // v_res is not used
  Helicoid: helicoid, Catenoid: catenoid, 'Sine Surface': sineSurface,
};

const mid = (p, q) => [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2];

export function sierpinskiTriangle(iterations = 5, size = 1.0) {
  const rec = (pts, n) => {
    if (n === 0) return [pts];
    const [p1, p2, p3] = pts, p12 = mid(p1, p2), p23 = mid(p2, p3), p31 = mid(p3, p1);
    return rec([p1, p12, p31], n - 1).concat(rec([p2, p12, p23], n - 1), rec([p3, p23, p31], n - 1));
  };
  const tris = rec([[0, 0, 0], [size, 0, 0], [size / 2, size * sqrt(3) / 2, 0]], iterations);
  return makeShape(tris.flat(), tris.map((_, i) => [i * 3, i * 3 + 1, i * 3 + 2]));
}

export function kochSnowflake(iterations = 4, size = 1.0) {
  // equilateral triangle inscribed in radius `size`, clockwise so the bumps point outwards
  let pts = [[size, 0, 0], [size * cos(4 * PI / 3), size * sin(4 * PI / 3), 0], [size * cos(2 * PI / 3), size * sin(2 * PI / 3), 0], [size, 0, 0]];
  for (let n = 0; n < iterations; n++) {
    const out = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], b = pts[i + 1], d = [(b[0] - a[0]) / 3, (b[1] - a[1]) / 3, (b[2] - a[2]) / 3];
      const c = [a[0] + d[0], a[1] + d[1], a[2] + d[2]], e = [b[0] - d[0], b[1] - d[1], b[2] - d[2]];
      const v = [-d[1], d[0], 0], s3 = sqrt(3);
      out.push(a, c, [0, 1, 2].map(k => (c[k] + e[k]) / 2 + v[k] * s3 / 2), e); // apex of an equilateral bump
    }
    out.push(pts[pts.length - 1]);
    pts = out;
  }
  return makeShape(pts, [[...Array(pts.length - 1).keys()]]);
}

const CUBE_FACES = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 4, 7, 3], [1, 5, 6, 2], [0, 1, 5, 4], [3, 2, 6, 7]];
const boxAt = (x, y, z, s) => [[x, y, z], [x + s, y, z], [x + s, y + s, z], [x, y + s, z],
  [x, y, z + s], [x + s, y, z + s], [x + s, y + s, z + s], [x, y + s, z + s]];
function boxes(list, faceList = CUBE_FACES) {
  const verts = [], faces = [];
  for (const cube of list) { const b = verts.length; verts.push(...cube); faces.push(...faceList.map(f => f.map(i => i + b))); }
  return makeShape(verts, faces);
}

export function mengerSponge(iterations = 3, size = 1.0) {
  let cubes = [[[0, 0, 0], [size, 0, 0], [0, size, 0], [size, size, 0], [0, 0, size], [size, 0, size], [0, size, size], [size, size, size]]];
  for (let n = 0; n < iterations; n++) {
    const next = [];
    for (const cube of cubes) for (const x of [-1, 0, 1]) for (const y of [-1, 0, 1]) for (const z of [-1, 0, 1]) {
      if (abs(x) + abs(y) + abs(z) > 1) next.push(cube.map(p => [p[0] * (1 / 3) + x * (size / 3), p[1] * (1 / 3) + y * (size / 3), p[2] * (1 / 3) + z * (size / 3)]));
    }
    cubes = next;
  }
  return boxes(cubes, [[0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4], [2, 3, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5]]);
}

// Circles only (vertices, no faces), as in the Python.
export function apollonianGasket(iterations = 3, size = 1) {
  const inner = ([x1, y1, r1], [x2, y2, r2], [x3, y3, r3]) => {
    const a = 1 / r1 + 1 / r2 + 1 / r3, b = x1 / r1 + x2 / r2 + x3 / r3, c = y1 / r1 + y2 / r2 + y3 / r3;
    const d = (x1 ** 2 + y1 ** 2 - r1 ** 2) / r1 + (x2 ** 2 + y2 ** 2 - r2 ** 2) / r2 + (x3 ** 2 + y3 ** 2 - r3 ** 2) / r3;
    const x = b / (2 * a), y = c / (2 * a);
    return [x, y, sqrt(x ** 2 + y ** 2 - d / a)];
  };
  const gen = (c1, c2, c3, depth) => {
    if (depth === 0) return [c1, c2, c3];
    const inn = inner(c1, c2, c3), out = [c1, c2, c3, inn];
    if (depth > 1) out.push(...gen(c1, c2, inn, depth - 1), ...gen(c1, c3, inn, depth - 1), ...gen(c2, c3, inn, depth - 1));
    return out;
  };
  const r0 = 1 / sqrt(3), verts = [];
  for (const [cx, cy, cr] of gen([0, -r0, r0], [-0.5, 1 / (2 * sqrt(3)), r0], [0.5, 1 / (2 * sqrt(3)), r0], iterations)) {
    const n = max(8, floor(32 * cr));
    for (let i = 0; i < n; i++) { const t = 2 * PI * i / n; verts.push([(cx + cr * cos(t)) * size, (cy + cr * sin(t)) * size, 0 * size]); }
  }
  return makeShape(verts, []);
}

export function jerusalemCube(iterations = 3, size = 1) {
  let cubes = [[0, 0, 0, size]];
  for (let n = 0; n < iterations; n++) cubes = cubes.flatMap(([x, y, z, s0]) => {
    const s = s0 / 3;
    return [[x, y, z, s], [x + 2 * s, y, z, s], [x, y + 2 * s, z, s], [x + 2 * s, y + 2 * s, z, s],
      [x, y, z + 2 * s, s], [x + 2 * s, y, z + 2 * s, s], [x, y + 2 * s, z + 2 * s, s], [x + 2 * s, y + 2 * s, z + 2 * s, s]];
  });
  return boxes(cubes.map(([x, y, z, s]) => boxAt(x, y, z, s)));
}

export function sierpinskiTetrahedron(iterations = 4, size = 1) {
  let tets = [[[0, 0, 0], [size, 0, 0], [size / 2, size * sqrt(3) / 2, 0], [size / 2, size * sqrt(3) / 6, size * sqrt(6) / 3]]];
  for (let n = 0; n < iterations; n++) tets = tets.flatMap(([a, b, c, d]) => {
    const ab = mid(a, b), ac = mid(a, c), ad = mid(a, d), bc = mid(b, c), bd = mid(b, d), cd = mid(c, d);
    return [[a, ab, ac, ad], [ab, b, bc, bd], [ac, bc, c, cd], [ad, bd, cd, d]];
  });
  return boxes(tets, [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]);
}

export function pythagorasTree3d(iterations = 5, size = 1, angle = PI / 4) {
  const tree = ([x, y, z], s, it) => {
    if (it === 0) return [];
    const out = [boxAt(x, y, z, s)];
    let ns = s * cos(angle);
    out.push(...tree([x + s - ns * sin(angle), y + s + ns * cos(angle), z + s], ns, it - 1));
    ns = s * sin(angle);
    out.push(...tree([x + s * cos(angle), y + s, z + s + ns], ns, it - 1));
    return out;
  };
  return boxes(tree([0, 0, 0], size, iterations));
}

export const FRACTALS = {
  'Sierpinski Triangle': sierpinskiTriangle, 'Koch Snowflake': kochSnowflake, 'Menger Sponge': mengerSponge,
  'Apollonian Gasket': apollonianGasket, 'Jerusalem Cube': jerusalemCube, 'Sierpinski Tetrahedron': sierpinskiTetrahedron,
  'Pythagoras Tree 3D': pythagorasTree3d,
};

// Wireframe.create_text. table is letter_glyphs.json ({gap, space, glyphs: {char: {vertices, faces}}}, from the API),
// the file letter_definitions.py reads: each glyph advances by its width plus gap, a space by space.
export function createText(text, table) {
  const verts = [], faces = [], G = table.glyphs;
  let offset = 0;
  for (const ch of text.toUpperCase()) {
    if (ch === ' ') { offset += table.space; continue; }
    if (!G[ch]) continue;
    const v = G[ch].vertices.map(p => p.map(f32)), base = verts.length;
    let x0 = Infinity, x1 = -Infinity;
    for (const p of v) { x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); }
    const dx = f32(offset - x0);
    verts.push(...v.map(p => [f32(p[0] + dx), p[1], p[2]]));
    faces.push(...G[ch].faces.map(face => face.map(i => i + base)));
    offset += (x1 - x0) + table.gap;
  }
  if (!verts.length) throw new Error(`No supported characters in "${text}"; defined: ${Object.keys(G).sort().join(' ')}`);
  return makeShape(verts, faces);
}
