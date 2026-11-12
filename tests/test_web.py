"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- project-specific API tests ---------------------------------------------------------------------------------------
import json  # noqa: E402

import numpy as np  # noqa: E402

import shape_catalog as cat  # noqa: E402
from wireframe import Wireframe  # noqa: E402


def test_catalog_comes_from_python():
    d = client.get("/api/catalog").json()
    assert [g["names"] for g in d["groups"]] == [cat.BASIC_SHAPES, cat.PARAMETRIC_SHAPES, cat.FRACTALS]
    assert d["resolution"] == list(cat.PARAM_RESOLUTION) and d["camera"]["fov"] == 60
    assert len(d["glyphs"]["glyphs"]) == 37 and d["glyphs"]["gap"] > 0 and d["physics"]["gravity"] == 9.8
    assert len(d["shapes"]) == 25 and sum(s["server_only"] for s in d["shapes"]) == 1


def test_shape_matches_generator():
    r = client.get("/api/shape/klein-bottle?u=12&v=14").json()
    ref = Wireframe.create_klein_bottle(12, 14)
    assert np.allclose(r["vertices"], ref.vertices, atol=1e-6) and r["faces"] == ref.faces.tolist()
    g = client.get("/api/shape/gyroid").json()
    assert len(g["vertices"]) > 1000 and all(len(f) == 3 for f in g["faces"])
    assert client.get("/api/shape/nope").status_code == 404
    assert client.get("/api/shape/menger-sponge?iterations=9").status_code == 422
    assert client.get("/api/shape/menger-sponge?iterations=8").json()["params"][0] == 3  # web cap


def test_text_endpoint():
    assert len(client.get("/api/text?t=AB").json()["vertices"]) == 40
    assert len(client.get("/api/text?t=HI").json()["vertices"]) == 6 * 8
    assert client.get("/api/text?t=%3F%23").status_code == 422


def test_info_counts():
    d = client.get("/api/info").json()
    assert (d["basic"], d["parametric"], d["fractals"], d["characters"], d["shapes"]) == (11, 7, 7, 37, 25)


def test_js_fixture_is_current():
    """tests/fixtures/engine_fixture.json (read by engine.test.mjs) still matches the Python code."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_engine_fixture
    now = json.loads(json.dumps(make_engine_fixture.fixture()))
    emb = json.loads((ROOT / "tests" / "fixtures" / "engine_fixture.json").read_text())
    assert emb["glyphs"] == now["glyphs"]
    for a, b in zip(emb["shapes"], now["shapes"], strict=True):
        assert (a["kind"], a["name"], a["params"], a["faces"]) == (b["kind"], b["name"], b["params"], b["faces"])
        assert np.allclose(a["vertices"], b["vertices"], rtol=1e-9, atol=1e-12)
    for a, b in zip(emb["transforms"], now["transforms"], strict=True):
        assert np.allclose(a["vertices"], b["vertices"], rtol=1e-9, atol=1e-12)
    assert np.allclose(emb["physics"]["traj"], now["physics"]["traj"], rtol=1e-9, atol=1e-12)
    for a, b in zip(emb["camera"]["cases"], now["camera"]["cases"], strict=True):
        for k in ("view", "proj", "xy", "depth"):
            assert np.allclose(a[k], b[k], rtol=1e-9, atol=1e-9)
