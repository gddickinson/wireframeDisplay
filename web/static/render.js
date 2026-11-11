// Canvas renderer: projects scene objects through the orbit camera (engine.project) and paints them back to front.
// The desktop draws with OpenGL (depth buffer, flat colour, black triangle edges); here polygons are depth-sorted
// (painter's algorithm), outlines are the polygon edges and "shading" is an optional web-only light term.
import { project, transformVertices } from './engine.js';
import { edgesFromFaces } from './geometry.js';

export const rgb = c => `rgb(${c.map(x => Math.round(x)).join(',')})`;
export const hexToRgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
export const rgbToHex = c => '#' + c.map(x => Math.round(x).toString(16).padStart(2, '0')).join('');

// World position of every vertex of a scene object (SceneObject.get_transformed_vertices).
export function worldVertices(o) {
  if (!o._key || o._key !== key(o)) { o._world = transformVertices(o.shape.vertices, o.centre, o.scale, o.rotation, o.position); o._key = key(o); }
  return o._world;
}
const key = o => [...o.position, ...o.rotation, ...o.scale].join(',');

// Fit the canvas backing store to its CSS size (crisp on high-DPI screens); returns the CSS size.
export function fitCanvas(canvas) {
  const r = canvas.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = Math.max(50, Math.round(r.width)), h = Math.max(50, Math.round(r.height));
  if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
  }
  const ctx = canvas.getContext('2d');
  ctx.setTransform(canvas.width / w, 0, 0, canvas.height / h, 0, 0);
  return { ctx, w, h };
}

// opts: showFaces, showEdges, showVertices, faceColor, edgeColor, vertexColor ([r, g, b] 0-255), edgeWidth,
// vertexSize, shading, hoverColor, background.
export function drawScene(ctx, w, h, objects, cam, opts, hovered = null) {
  ctx.fillStyle = opts.background || '#000';
  ctx.fillRect(0, 0, w, h);
  const polys = [], dots = [], lines = [];
  for (const o of objects) {
    const pts = worldVertices(o), { xy, depth } = project(pts, cam, w, h);
    const colour = o === hovered ? opts.hoverColor : (o.color || opts.faceColor);
    const faces = o.shape.faces || [];
    if (opts.showFaces && faces.length) {
      for (const f of faces) {
        let d = 0, behind = false;
        for (const i of f) { d += depth[i]; if (depth[i] <= cam.distance * 0.001) behind = true; }
        if (!behind) polys.push({ f, xy, d: d / f.length, colour, pts });
      }
    } else if (opts.showEdges && faces.length) {
      o._edges = o._edges || edgesFromFaces(faces);
      for (const [a, b] of o._edges) if (depth[a] > 0 && depth[b] > 0) lines.push([xy[a], xy[b]]);
    }
    if (opts.showVertices || !faces.length) for (let i = 0; i < xy.length; i++) if (depth[i] > 0) dots.push([xy[i], o === hovered ? opts.hoverColor : opts.vertexColor]);
  }
  polys.sort((a, b) => b.d - a.d);
  ctx.lineJoin = 'round';
  ctx.lineWidth = opts.edgeWidth;
  ctx.strokeStyle = rgb(opts.edgeColor);
  for (const p of polys) {
    ctx.beginPath();
    p.f.forEach((i, k) => (k ? ctx.lineTo(p.xy[i][0], p.xy[i][1]) : ctx.moveTo(p.xy[i][0], p.xy[i][1])));
    ctx.closePath();
    ctx.fillStyle = rgb(opts.shading ? shade(p, cam) : p.colour);
    ctx.fill();
    if (opts.showEdges) ctx.stroke();
  }
  if (lines.length) {
    ctx.beginPath();
    for (const [a, b] of lines) { ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); }
    ctx.stroke();
  }
  const r = Math.max(0.5, opts.vertexSize / 2);
  for (const [[x, y], c] of dots) { ctx.fillStyle = rgb(c); ctx.fillRect(x - r, y - r, 2 * r, 2 * r); }
}

// Web-only shading: brightness from how squarely the face points at the camera (Newell normal, two-sided).
function shade(p, cam) {
  const n = [0, 0, 0], f = p.f, P = p.pts;
  for (let k = 0; k < f.length; k++) {
    const a = P[f[k]], b = P[f[(k + 1) % f.length]];
    n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1]);
  }
  const el = cam.elevation * Math.PI / 180, az = cam.azimuth * Math.PI / 180;
  const eye = [Math.cos(el) * Math.cos(az), Math.cos(el) * Math.sin(az), Math.sin(el)]; // pyqtgraph camera direction
  const len = Math.hypot(...n) || 1, lam = Math.abs((n[0] * eye[0] + n[1] * eye[1] + n[2] * eye[2]) / len);
  return p.colour.map(c => c * (0.35 + 0.65 * lam));
}

// SceneObject under the pointer: the desktop casts a ray and picks the object whose centre is closest to it,
// if within 1.0 world unit. Same rule here, measured at the centre's depth.
export function pick(objects, cam, w, h, mx, my) {
  let best = null, bestD = Infinity;
  for (const o of objects) {
    const c = o.centre.map((x, k) => x + o.position[k]);
    const { xy, depth } = project([c], cam, w, h);
    if (depth[0] <= 0) continue;
    const perPx = 2 * depth[0] * Math.tan(cam.fov * Math.PI / 360) / w;
    const d = Math.hypot(xy[0][0] - mx, xy[0][1] - my) * perPx;
    if (d < bestD) { bestD = d; best = o; }
  }
  return bestD < 1.0 ? best : null;
}
