#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 17:03:51 2024

@author: george

Text glyphs for Wireframe.create_text, read from letter_glyphs.json (written by scripts/make_glyphs.py). The same JSON
is served to the web viewer by web/app.py, so desktop and browser draw identical text.

ALL_CHARACTERS        {char: (vertices (N, 3), faces (M, 4))} for A-Z, 0-9 and !
LETTER_DEFINITIONS, NUMBER_DEFINITIONS, SYMBOL_DEFINITIONS  the same split by kind
GLYPH_TABLE           the raw JSON (height, depth, gap, space, glyphs)
GAP, SPACE            text layout: a glyph advances by its width + GAP; a space advances by SPACE
"""
import json
from pathlib import Path

import numpy as np

GLYPH_TABLE = json.loads((Path(__file__).resolve().parent / "letter_glyphs.json").read_text())
GAP = GLYPH_TABLE["gap"]
SPACE = GLYPH_TABLE["space"]

ALL_CHARACTERS = {ch: (np.array(g["vertices"]), np.array(g["faces"])) for ch, g in GLYPH_TABLE["glyphs"].items()}
LETTER_DEFINITIONS = {k: v for k, v in ALL_CHARACTERS.items() if k.isalpha()}
NUMBER_DEFINITIONS = {k: v for k, v in ALL_CHARACTERS.items() if k.isdigit()}
SYMBOL_DEFINITIONS = {k: v for k, v in ALL_CHARACTERS.items() if not k.isalnum()}
