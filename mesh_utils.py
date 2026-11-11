"""Qt-free mesh helpers shared by wireframe.py (desktop) and the web API.

face_array  -- normalise a face list: negative indices counted from the end, mixed polygon sizes fan-triangulated
triangulate -- fan-triangulate (N, k) polygon faces into (M, 3) triangles (what OpenGL draws)
edges_from_faces -- the unique undirected polygon edges of a face list
"""
import numpy as np


def triangulate(faces):
    """Fan-triangulate polygon faces (each [v0, v1, ..., vk-1]) into triangles [v0, vi, vi+1]."""
    tris = [[f[0], f[i], f[i + 1]] for f in faces for i in range(1, len(f) - 1)]
    return np.array(tris, dtype=np.int32).reshape(-1, 3)


def face_array(faces, n_vertices):
    """Faces as an int32 array; ragged lists (e.g. a pyramid's 4 triangles + 1 square) become triangles."""
    if faces is None:
        return None
    rows = [[int(i) + n_vertices if int(i) < 0 else int(i) for i in f] for f in faces]
    if not rows:
        return np.zeros((0, 3), dtype=np.int32)
    if len({len(r) for r in rows}) == 1:
        return np.array(rows, dtype=np.int32)
    return triangulate(rows)


def edges_from_faces(faces):
    """Sorted unique (i, j) pairs, i < j, along every polygon outline."""
    seen = set()
    for f in faces if faces is not None else []:
        f = [int(i) for i in f]
        for a, b in zip(f, f[1:] + f[:1]):
            if a != b:
                seen.add((min(a, b), max(a, b)))
    return sorted(seen)
