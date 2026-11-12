"""The module split keeps the public names and every Python file under the 500-line budget."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_python_files_under_500_lines():
    files = [p for p in ROOT.rglob("*.py") if ".git" not in p.parts and "site" not in p.parts]
    long = {str(p.relative_to(ROOT)): n for p in files if (n := len(p.read_text().splitlines())) >= 500}
    assert long == {}  # wireframe.py (869) and wireframe_viewer.py (1021) used to exceed it


def test_public_names_still_import():
    from wireframe import Wireframe
    for name in ["create_cube", "create_dodecahedron", "create_klein_bottle", "create_gyroid", "create_menger_sponge",
                 "create_text", "create_basic_shape", "create_parametric_shape", "create_fractal", "load_from_obj",
                 "load_mri", "rotation_matrix", "marching_cubes"]:
        assert callable(getattr(Wireframe, name)), name
    assert len(Wireframe.create_fractal("Jerusalem Cube", 1, 1.0).vertices) == 160
    pytest.importorskip("PyQt5")
    import wireframe_viewer as wv
    for name in ["WireframeViewer", "SceneObject", "Scene", "DisplayOptionsDialog", "ObjectPropertiesDialog", "ColorButton"]:
        assert hasattr(wv, name), name
