"""Write letter_glyphs.json: the one glyph table read by letter_definitions.py (desktop, API) and, through the API,
by the web viewer.

A, B and ! keep George's original hand-made geometry (formerly literal arrays in letter_definitions.py). Every
other letter A-Z and digit 0-9 is drawn from straight strokes on a 12 x 24 grid: each stroke becomes a box of
thickness STROKE (extended by half a stroke at both ends so joints close) and depth DEPTH, i.e. 8 vertices and
6 quad faces, the same 24-unit height and 2-unit depth as the original glyphs. Text layout: each glyph advances by
its width plus GAP; a space advances by SPACE.

Run: python scripts/make_glyphs.py      (rewrites letter_glyphs.json)
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "letter_glyphs.json"
STROKE, DEPTH, GAP, SPACE = 2.0, 2.0, 4.0, 10.0
L, M, R, B, C, T = 1, 6, 11, 1, 12, 23  # stroke centre lines: left / middle / right, bottom / centre / top

LEGACY = {  # letter_definitions.py before 2026-11-11, unchanged (its "0" was a solid block; now drawn from strokes)
    "A": ([[0, 0, 0], [4, 0, 0], [0, 0, 2], [4, 0, 2], [14, 0, 0], [18, 0, 0], [14, 0, 2], [18, 0, 2], [5, 6, 0], [13, 6, 0],
           [5, 6, 2], [13, 6, 2], [7, 13, 0], [11, 13, 0], [7, 13, 2], [11, 13, 2], [9, 17, 0], [9, 17, 2], [7, 24, 0],
           [11, 24, 0], [7, 24, 2], [11, 24, 2]],
          [[0, 1, 3, 2], [4, 5, 7, 6], [8, 9, 11, 10], [12, 13, 15, 14], [18, 19, 21, 20], [0, 2, 20, 18], [5, 7, 21, 19],
           [1, 3, 10, 8], [4, 6, 11, 9], [12, 14, 17, 16], [13, 15, 17, 16]]),
    "B": ([[0, 0, 0], [0, 24, 0], [0, 0, 2], [0, 24, 2], [12, 0, 0], [12, 12, 0], [12, 24, 0], [12, 0, 2], [12, 12, 2],
           [12, 24, 2], [14, 2, 0], [14, 10, 0], [14, 14, 0], [14, 22, 0], [14, 2, 2], [14, 10, 2], [14, 14, 2], [14, 22, 2]],
          [[0, 1, 3, 2], [0, 4, 7, 2], [1, 6, 9, 3], [4, 5, 8, 7], [5, 6, 9, 8], [4, 10, 14, 7], [5, 12, 16, 8],
           [10, 11, 15, 14], [12, 13, 17, 16], [11, 5, 8, 15], [13, 6, 9, 17]]),
    "!": ([[0, 20, 0], [2, 20, 0], [0, 24, 0], [2, 24, 0], [0, 20, 2], [2, 20, 2], [0, 24, 2], [2, 24, 2], [0, 0, 0], [2, 0, 0],
           [0, 2, 0], [2, 2, 0], [0, 0, 2], [2, 0, 2], [0, 2, 2], [2, 2, 2]],
          [[0, 1, 3, 2], [4, 5, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5], [0, 1, 5, 4], [2, 3, 7, 6], [8, 9, 11, 10],
           [12, 13, 15, 14], [8, 10, 14, 12], [9, 11, 15, 13], [8, 9, 13, 12], [10, 11, 15, 14]]),
}


def path(*pts):
    """Consecutive strokes along a polyline."""
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


BOX = path((L, B), (R, B), (R, T), (L, T), (L, B))
STROKES = {
    "C": path((R, T), (L, T), (L, B), (R, B)),
    "D": path((L, B), (L, T), (7, T), (R, 18), (R, 6), (7, B), (L, B)),
    "E": path((R, T), (L, T), (L, B), (R, B)) + [((L, C), (9, C))],
    "F": path((R, T), (L, T), (L, B)) + [((L, C), (9, C))],
    "G": path((R, T), (L, T), (L, B), (R, B), (R, C), (M, C)),
    "H": [((L, B), (L, T)), ((R, B), (R, T)), ((L, C), (R, C))],
    "I": [((M, B), (M, T)), ((3, T), (9, T)), ((3, B), (9, B))],
    "J": path((R, T), (R, B), (L, B), (L, 7)),
    "K": [((L, B), (L, T)), ((L, C), (R, T)), ((L, C), (R, B))],
    "L": path((L, T), (L, B), (R, B)),
    "M": path((L, B), (L, T), (M, C), (R, T), (R, B)),
    "N": path((L, B), (L, T), (R, B), (R, T)),
    "O": BOX,
    "P": path((L, B), (L, T), (R, T), (R, C), (L, C)),
    "Q": BOX + [((7, 6), (R, B))],
    "R": path((L, B), (L, T), (R, T), (R, C), (L, C)) + [((M, C), (R, B))],
    "S": path((R, T), (L, T), (L, C), (R, C), (R, B), (L, B)),
    "T": [((L, T), (R, T)), ((M, T), (M, B))],
    "U": path((L, T), (L, B), (R, B), (R, T)),
    "V": path((L, T), (M, B), (R, T)),
    "W": path((L, T), (3.5, B), (M, C), (8.5, B), (R, T)),
    "X": [((L, B), (R, T)), ((L, T), (R, B))],
    "Y": [((L, T), (M, C)), ((R, T), (M, C)), ((M, C), (M, B))],
    "Z": path((L, T), (R, T), (L, B), (R, B)),
    "0": BOX + [((R, T), (L, B))],
    "1": [((M, B), (M, T)), ((M, T), (3, 19)), ((3, B), (9, B))],
    "2": path((L, T), (R, T), (R, C), (L, C), (L, B), (R, B)),
    "3": path((L, T), (R, T), (R, B), (L, B)) + [((3, C), (R, C))],
    "4": path((L, T), (L, C), (R, C)) + [((R, T), (R, B))],
    "5": path((R, T), (L, T), (L, C), (R, C), (R, B), (L, B)),
    "6": path((R, T), (L, T), (L, B), (R, B), (R, C), (L, C)),
    "7": path((L, T), (R, T), (4, B)),
    "8": BOX + [((L, C), (R, C))],
    "9": path((R, C), (L, C), (L, T), (R, T), (R, B), (L, B)),
}


def stroke_box(p, q):
    p, q = np.array(p, float), np.array(q, float)
    d = (q - p) / np.linalg.norm(q - p)
    n = np.array([-d[1], d[0]]) * STROKE / 2
    p, q = p - d * STROKE / 2, q + d * STROKE / 2
    quad = [p - n, q - n, q + n, p + n]
    return [[x, y, z] for z in (0.0, DEPTH) for x, y in quad]


BOX_FACES = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]


def glyph(strokes):
    verts, faces = [], []
    for p, q in strokes:
        base = len(verts)
        verts += stroke_box(p, q)
        faces += [[i + base for i in f] for f in BOX_FACES]
    x0 = min(v[0] for v in verts)
    return [[round(v[0] - x0, 6) + 0.0, round(v[1], 6) + 0.0, v[2]] for v in verts], faces


def table():
    glyphs = {ch: {"vertices": [[float(c) for c in p] for p in v], "faces": f} for ch, (v, f) in LEGACY.items()}
    for ch, strokes in STROKES.items():
        v, f = glyph(strokes)
        glyphs[ch] = {"vertices": v, "faces": f}
    return {"height": 24.0, "depth": DEPTH, "gap": GAP, "space": SPACE,
            "glyphs": dict(sorted(glyphs.items()))}


if __name__ == "__main__":
    data = table()
    OUT.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print(f"wrote {OUT.name}: {len(data['glyphs'])} glyphs")
