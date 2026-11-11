"""Regression test: every dodecahedron face is a regular pentagon (all five edges the same length)."""
import numpy as np

from wireframe import Wireframe


def test_dodecahedron_faces_are_regular_pentagons():
    d = Wireframe.create_dodecahedron()
    v = np.asarray(d.vertices, dtype=float)
    faces = np.asarray(d.faces)
    assert faces.shape == (12, 5)
    edge = 2 / ((1 + 5 ** 0.5) / 2)  # 2/phi for this vertex set
    for f in faces:
        p = v[f]
        lengths = [np.linalg.norm(p[i] - p[(i + 1) % 5]) for i in range(5)]
        assert np.allclose(lengths, edge, rtol=1e-5), (f.tolist(), lengths)
    # each vertex is shared by exactly three faces, each edge by two
    assert np.bincount(faces.ravel(), minlength=20).tolist() == [3] * 20
