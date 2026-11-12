"""Regression tests for fractal geometry: Koch snowflake, Jerusalem cube, Gyroid."""
import numpy as np
import pytest

from wireframe import Wireframe


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4])
def test_koch_snowflake_from_equilateral_triangle(n):
    w = Wireframe.create_koch_snowflake(n, 2.0)
    loop = w.vertices[w.faces[0]].astype(float)
    assert len(loop) == 3 * 4 ** n  # one polygon of 3 * 4^n segments
    seg = np.linalg.norm(np.roll(loop, -1, axis=0) - loop, axis=1)
    side = 2.0 * np.sqrt(3)  # triangle inscribed in a circle of radius `size`
    assert np.allclose(seg, side / 3 ** n, rtol=1e-5)  # all segments equal
    x, y = loop[:, 0], loop[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    tri = np.sqrt(3) / 4 * side ** 2
    expected = tri * (8 / 5 - 3 / 5 * (4 / 9) ** n)  # bumps point outwards: the snowflake grows towards 8/5
    assert np.isclose(area, expected, rtol=1e-4)


def _cubes(w):
    v = w.vertices.astype(float).reshape(-1, 8, 3)
    return v.min(axis=1), v.max(axis=1) - v.min(axis=1)


@pytest.mark.parametrize("n", [1, 2, 3])
def test_jerusalem_cube_structure(n):
    size = 3.0
    w = Wireframe.create_jerusalem_cube(n, size)
    lo, ext = _cubes(w)
    assert len(lo) == 20 ** n  # each cube -> 8 corner cubes + 12 edge cubes
    assert np.allclose(ext[:, 0], ext[:, 1], atol=1e-5) and np.allclose(ext[:, 0], ext[:, 2], atol=1e-5)  # cubes (float32)
    k = np.sqrt(2) - 1  # corner cube ratio; edge cubes are k^2
    sizes = np.unique(ext[:, 0].round(5))
    expected = np.unique([round(size * k ** (n + j), 5) for j in range(n + 1)])
    assert np.allclose(sizes, expected, atol=1e-4)
    assert lo.min() >= -1e-5 and (lo + ext).max() <= size + 1e-5


def test_jerusalem_cube_first_level_layout():
    w = Wireframe.create_jerusalem_cube(1, 1.0)
    lo, ext = _cubes(w)
    k = np.sqrt(2) - 1
    corners, edges = lo[np.isclose(ext[:, 0], k)], lo[np.isclose(ext[:, 0], k * k)]
    assert len(corners) == 8 and len(edges) == 12
    assert np.allclose(np.unique(corners.round(6)), [0, round(1 - k, 6)], atol=1e-5)
    # every edge cube sits between two corner cubes along one axis, flush with two outer faces
    for e in edges:
        assert sum(np.isclose(e, k, atol=1e-5)) == 1 and sum(np.isclose(e, 0, atol=1e-5) | np.isclose(e, 1 - k * k, atol=1e-5)) == 2
