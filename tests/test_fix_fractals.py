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
