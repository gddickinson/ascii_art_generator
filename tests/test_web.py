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


# --- project-specific API tests -------------------------------------------------------------------------------------
import json  # noqa: E402

import ascii_pipeline  # noqa: E402
from ascii_art_generator import ASCIIArtGenerator  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "ascii_fixture.json"
DEMO = STATIC / "demo.png"


def test_info_lists_every_option():
    info = client.get("/api/info").json()
    assert info["char_sets"] == ASCIIArtGenerator.CHAR_SETS
    assert info["defaults"] == ascii_pipeline.DEFAULTS
    assert set(info["labels"]) == set(ascii_pipeline.DEFAULTS)
    assert info["js_test_cases"] == len(json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"])


def test_convert_demo_matches_pipeline():
    settings = {"width": 50, "char_set": "blocks", "invert": True}
    r = client.post("/api/convert", data={"settings": json.dumps(settings)})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["engine"] == "python" and body["cols"] == 50
    assert body["text"] == ascii_pipeline.convert_file(DEMO, settings)


def test_convert_upload_and_preview():
    with DEMO.open("rb") as fh:
        r = client.post("/api/convert", files={"file": ("pic.png", fh, "image/png")},
                        data={"settings": json.dumps({"width": 200}), "preview": "true"})
    assert r.status_code == 200 and r.json()["cols"] == ascii_pipeline.PREVIEW_MAX_WIDTH


@pytest.mark.parametrize("files, settings", [
    ({"file": ("notes.txt", b"not an image", "text/plain")}, "{}"),
    (None, '{"width": 0}'),
    (None, '{"char_set": "nope"}'),
    (None, '{"char_set": "custom", "custom_chars": ""}'),
    (None, "not json"),
])
def test_convert_rejects_bad_input(files, settings):
    r = client.post("/api/convert", files=files, data={"settings": settings})
    assert r.status_code == 400 and r.json()["detail"]


def test_fixture_is_current():
    """The JS test fixture still matches what the Python pipeline produces.

    Integer-only cases must match exactly. Cases through Pillow/OpenCV float32 arithmetic may differ in the last bit on
    another platform (e.g. Linux CI vs the macOS machine that wrote the fixture), so they may differ in a few characters.
    """
    import base64

    import numpy as np
    from PIL import Image
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_ascii_fixture
    old = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert old["char_sets"] == ASCIIArtGenerator.CHAR_SETS
    sample = old["html_sample"]
    import ascii_export
    assert ascii_export.to_html(sample["text"], sample["font_px"]) == sample["html"]
    images, regenerated = [], [make_ascii_fixture.test_image(61, 47, 1), make_ascii_fixture.test_image(37, 52, 2)]
    for im, regen in zip(old["images"], regenerated):
        rgba = np.frombuffer(base64.b64decode(im["rgba"]), np.uint8).reshape(im["h"], im["w"], 4)
        # the stored pixels are what the generator draws (sin/cos may differ by a level across platforms)
        assert np.abs(rgba[..., :3].astype(int) - np.array(regen)).max() <= 1
        images.append(Image.fromarray(np.ascontiguousarray(rgba[..., :3]), "RGB"))
    cases = make_ascii_fixture.cases()
    assert len(old["cases"]) == len(cases) * len(images)
    for a in old["cases"]:
        s, text = make_ascii_fixture.run_case(images[a["image"]], a["case"])
        assert a["settings"] == s
        if a["text"] == text:
            continue
        assert a["float"], f"integer-only case changed: {a['case']}"
        same = sum(x == y for x, y in zip(a["text"], text))
        assert len(a["text"]) == len(text) and same >= 0.97 * len(a["text"]), a["case"]
