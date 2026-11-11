// Mesh helpers and the basic shapes: a line-by-line port of wireframe.py (Wireframe.create_*) and mesh_utils.py.
// A shape is { vertices: [[x, y, z], ...], faces: [[i, j, k, ...], ...] }. Like the Python, which stores vertices as
// float32 (np.array(vertices, dtype=np.float32)), every coordinate is rounded to float32 with Math.fround.
const f32 = Math.fround;
const { sin, cos, sqrt, PI } = Math;

// np.linspace(start, stop, n): i * step + start, last element exactly stop.
export function linspace(start, stop, n, endpoint = true) {
  const div = endpoint ? n - 1 : n, step = (stop - start) / div;
  const out = Array.from({ length: n }, (_, i) => i * step + start);
  if (endpoint && n > 1) out[n - 1] = stop;
  return out;
}

// Fan-triangulate polygon faces into triangles [v0, vi, vi+1] (mesh_utils.triangulate).
export function triangulate(faces) {
  const out = [];
  for (const f of faces) for (let i = 1; i < f.length - 1; i++) out.push([f[0], f[i], f[i + 1]]);
  return out;
}

// mesh_utils.face_array: negative indices count from the end; mixed polygon sizes are fan-triangulated.
export function faceArray(faces, nVertices) {
  if (faces == null) return null;
  const rows = faces.map(f => Array.from(f, i => (i < 0 ? i + nVertices : i)));
  if (!rows.length) return [];
  return new Set(rows.map(r => r.length)).size === 1 ? rows : triangulate(rows);
}

// Unique undirected polygon edges (mesh_utils.edges_from_faces).
export function edgesFromFaces(faces) {
  const seen = new Set(), out = [];
  for (const f of faces || []) for (let k = 0; k < f.length; k++) {
    const a = f[k], b = f[(k + 1) % f.length];
    if (a === b) continue;
    const i = Math.min(a, b), j = Math.max(a, b), key = i * 1e7 + j;
    if (!seen.has(key)) { seen.add(key); out.push([i, j]); }
  }
  return out;
}

// Wireframe.__init__: float32 vertices, normalised faces.
export function makeShape(vertices, faces) {
  const v = vertices.map(p => [f32(p[0]), f32(p[1]), f32(p[2])]);
  return { vertices: v, faces: faceArray(faces, v.length) };
}

export function cube() {
  return makeShape([[1, 1, 1], [-1, 1, 1], [-1, -1, 1], [1, -1, 1], [1, 1, -1], [-1, 1, -1], [-1, -1, -1], [1, -1, -1]],
    [[0, 1, 2], [0, 2, 3], [0, 3, 7], [0, 7, 4], [0, 4, 5], [0, 5, 1], [6, 2, 1], [6, 1, 5], [6, 5, 4], [6, 4, 7], [6, 7, 3], [6, 3, 2]]);
}

export function sphere(rows = 20, cols = 20) {
  const v = [], f = [];
  for (let i = 0; i <= rows; i++) {
    const theta = i * PI / rows;
    for (let j = 0; j < cols; j++) {
      const phi = j * 2 * PI / cols;
      v.push([sin(theta) * cos(phi), sin(theta) * sin(phi), cos(theta)]);
    }
  }
  for (let i = 0; i < rows; i++) for (let j = 0; j < cols; j++) {
    const p1 = i * cols + j, p2 = j < cols - 1 ? p1 + 1 : i * cols;
    const p3 = (i + 1) * cols + j, p4 = j < cols - 1 ? p3 + 1 : (i + 1) * cols;
    f.push([p1, p2, p3], [p2, p4, p3]);
  }
  return makeShape(v, f);
}

export function tetrahedron() {
  return makeShape([[1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]], [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]]);
}

export function octahedron() {
  return makeShape([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]],
    [[0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2], [1, 2, 5], [1, 5, 3], [1, 3, 4], [1, 4, 2]]);
}

export function icosahedron() {
  const p = (1 + sqrt(5)) / 2;
  return makeShape([[-1, p, 0], [1, p, 0], [-1, -p, 0], [1, -p, 0], [0, -1, p], [0, 1, p], [0, -1, -p], [0, 1, -p],
    [p, 0, -1], [p, 0, 1], [-p, 0, -1], [-p, 0, 1]],
  [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]]);
}

export function dodecahedron() {
  const p = (1 + sqrt(5)) / 2, q = 1 / p;
  return makeShape([[-1, -1, -1], [1, -1, -1], [-1, 1, -1], [1, 1, -1], [-1, -1, 1], [1, -1, 1], [-1, 1, 1], [1, 1, 1],
    [0, -p, -q], [0, p, -q], [0, -p, q], [0, p, q], [-q, 0, -p], [q, 0, -p], [-q, 0, p], [q, 0, p],
    [-p, -q, 0], [p, -q, 0], [-p, q, 0], [p, q, 0]],
  [[0, 8, 10, 4, 16], [0, 12, 13, 1, 8], [0, 16, 18, 2, 12], [1, 13, 3, 19, 17], [1, 17, 5, 10, 8], [2, 9, 3, 13, 12],
    [2, 18, 6, 11, 9], [3, 9, 11, 7, 19], [4, 10, 5, 15, 14], [4, 14, 6, 18, 16], [5, 17, 19, 7, 15], [6, 14, 15, 7, 11]]);
}

export function torus(R = 1, r = 0.3, steps = 20, rings = 20) {
  const v = [], f = [];
  for (let i = 0; i < rings; i++) for (let j = 0; j < steps; j++) {
    const theta = 2 * PI * i / rings, phi = 2 * PI * j / steps;
    v.push([(R + r * cos(phi)) * cos(theta), (R + r * cos(phi)) * sin(theta), r * sin(phi)]);
  }
  for (let i = 0; i < rings; i++) for (let j = 0; j < steps; j++) {
    const i1 = i, i2 = (i + 1) % rings, j1 = j, j2 = (j + 1) % steps;
    f.push([i1 * steps + j1, i1 * steps + j2, i2 * steps + j2], [i1 * steps + j1, i2 * steps + j2, i2 * steps + j1]);
  }
  return makeShape(v, f);
}

export function cylinder(radius = 1, height = 2, segments = 20) {
  const v = [], f = [];
  for (let i = 0; i < segments; i++) {
    const t = 2 * PI * i / segments;
    v.push([radius * cos(t), radius * sin(t), -height / 2], [radius * cos(t), radius * sin(t), height / 2]);
  }
  v.push([0, 0, -height / 2], [0, 0, height / 2]);
  for (let i = 0; i < segments; i++) {
    const i1 = i * 2, i2 = (i * 2 + 2) % (segments * 2);
    f.push([i1, i2, i2 + 1], [i1, i2 + 1, i1 + 1], [i1, -2, i2], [i1 + 1, i2 + 1, -1]);
  }
  return makeShape(v, f);
}

export function cone(radius = 1, height = 2, segments = 20) {
  const v = [[0, 0, 0]], f = [];
  for (let i = 0; i < segments; i++) { const t = 2 * PI * i / segments; v.push([radius * cos(t), radius * sin(t), 0]); }
  v.push([0, 0, height]);
  for (let i = 1; i <= segments; i++) f.push([0, i, i % segments + 1], [i, segments + 1, i % segments + 1]);
  return makeShape(v, f);
}

export function pyramid(baseSize = 1, height = 1) {
  const h = baseSize / 2;
  return makeShape([[-h, -h, 0], [h, -h, 0], [h, h, 0], [-h, h, 0], [0, 0, height]],
    [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4], [0, 3, 2, 1]]);
}

export function prism(baseSize = 1, height = 1, nSides = 6) {
  const base = linspace(0, 2 * PI, nSides, false).map(a => [cos(a) * baseSize / 2, sin(a) * baseSize / 2, 0 * baseSize / 2]);
  const v = base.concat(base.map(([x, y, z]) => [x, y, z + height])), f = [];
  for (let i = 0; i < nSides; i++) f.push([i, (i + 1) % nSides, nSides + (i + 1) % nSides, nSides + i]);
  f.push([...Array(nSides).keys()], [...Array(nSides).keys()].map(i => i + nSides));
  return makeShape(v, f);
}

export const BASIC = {
  Cube: cube, Sphere: sphere, Tetrahedron: tetrahedron, Octahedron: octahedron, Icosahedron: icosahedron,
  Dodecahedron: dodecahedron, Torus: torus, Cylinder: cylinder, Cone: cone, Pyramid: pyramid, Prism: prism,
};
