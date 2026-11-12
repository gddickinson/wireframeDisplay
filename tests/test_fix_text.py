"""Regression tests: text supports A-Z and 0-9, glyphs advance by their width plus a gap, one glyph table."""
import json
import string
from pathlib import Path

import numpy as np

from wireframe import Wireframe

GLYPHS = json.loads((Path(__file__).resolve().parent.parent / "letter_glyphs.json").read_text())


def test_all_letters_and_digits_supported():
    text = string.ascii_uppercase + string.digits
    w = Wireframe.create_text(text.lower())  # lower case is upper-cased, as before
    assert len(w.vertices) == sum(len(GLYPHS["glyphs"][c]["vertices"]) for c in text)


def test_glyphs_do_not_overlap():
    gap = GLYPHS["gap"]
    for pair in ["AB", "WM", "10", "!I", "XY"]:
        a, b = (np.array(GLYPHS["glyphs"][c]["vertices"]) for c in pair)
        w = Wireframe.create_text(pair)
        first, second = w.vertices[:len(a)], w.vertices[len(a):]
        assert np.isclose(second[:, 0].min(), first[:, 0].max() + gap), pair  # used to start 1.5 units after A's origin
        assert np.allclose(first, a) and np.allclose(second[:, 1:], b[:, 1:])


def test_space_advance():
    a = np.array(GLYPHS["glyphs"]["A"]["vertices"])
    w = Wireframe.create_text("A B")
    assert np.isclose(w.vertices[len(a):, 0].min(), a[:, 0].max() + GLYPHS["gap"] + GLYPHS["space"])


def test_letter_definitions_reads_the_json():
    from letter_definitions import ALL_CHARACTERS
    assert sorted(ALL_CHARACTERS) == sorted(GLYPHS["glyphs"])
    v, f = ALL_CHARACTERS["Q"]
    assert np.array_equal(v, GLYPHS["glyphs"]["Q"]["vertices"]) and np.array_equal(f, GLYPHS["glyphs"]["Q"]["faces"])
