"""Write tests/fixtures/ascii_fixture.json: Python pipeline output for the JS engine test (ascii_engine.test.mjs).

Two small generated RGB test images (gradients, discs, stripes, seeded noise) are converted by ascii_pipeline with
many option combinations; the JS port must reproduce every text exactly. Cases marked "float" go through
Pillow/OpenCV float32 arithmetic (enhance blends, the smoothing filter, OpenCV's float Gaussian), whose last bit
can differ between builds; tests/test_web.py allows a small mismatch for those when re-running on other machines.

Run: python scripts/make_ascii_fixture.py
"""
import base64
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ascii_export  # noqa: E402
import ascii_pipeline  # noqa: E402
from ascii_art_generator import ASCIIArtGenerator  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "ascii_fixture.json"
FLOAT_KEYS = ("contrast", "brightness", "sharpness", "adaptive_thresh")


def test_image(w, h, seed):
    """Deterministic RGB test picture: colour gradients, two discs, stripes and uniform noise."""
    y, x = np.mgrid[0:h, 0:w].astype(float)
    r = 255 * x / (w - 1)
    g = 255 * y / (h - 1)
    b = 128 + 100 * np.sin(x / 3.0) * np.cos(y / 4.0)
    img = np.stack([r, g, b], -1)
    img[(x - w * 0.3) ** 2 + (y - h * 0.4) ** 2 < (h * 0.22) ** 2] = (250, 240, 30)
    img[(x - w * 0.7) ** 2 + (y - h * 0.65) ** 2 < (h * 0.18) ** 2] = (10, 20, 60)
    img[:, int(w * 0.85):][(np.arange(h) // 2 % 2 == 0)] = 255
    img += np.random.RandomState(seed).uniform(-25, 25, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def cases():
    c = [{}, {"width": 90}, {"width": 58, "height": 5}, {"width": 24, "height": 40}, {"width": 100, "preview": True},
         {"height": 30, "preview": True}]
    c += [{"char_set": k} for k in ("basic", "blocks", "custom")]
    c += [{"char_set": "custom", "custom_chars": " #"}, {"char_set": "custom", "custom_chars": " ·•●"}]
    c += [{"contrast": 1.7}, {"contrast": 0.4}, {"brightness": 1.3}, {"brightness": 0.6}, {"brightness": 2.9},
          {"sharpness": 2.5}, {"sharpness": 0.3}, {"sharpness": 5.0}]
    c += [{"hist_equal": True}, {"invert": True}, {"dither": True}, {"invert": True, "dither": True}]
    c += [{"enhance_edges": True, "edge_mode": m} for m in ascii_pipeline.EDGE_MODES]
    c += [{"enhance_edges": True, "edge_mode": "canny", "width": 60}]
    c += [{"unsharp_mask": True}, {"unsharp_mask": True, "unsharp_radius": 0.5, "unsharp_amount": 3.0},
          {"unsharp_mask": True, "unsharp_radius": 5.0, "unsharp_amount": 0.7}]
    c += [{"adaptive_thresh": True}, {"adaptive_thresh": True, "thresh_block": 3, "thresh_c": 0},
          {"adaptive_thresh": True, "thresh_block": 7}, {"adaptive_thresh": True, "thresh_block": 25, "thresh_c": 5},
          {"adaptive_thresh": True, "thresh_block": 51, "thresh_c": 10}]
    c += [{"sharpness": 1.8, "contrast": 1.3, "brightness": 0.9, "hist_equal": True, "enhance_edges": True,
           "edge_mode": "sobel", "unsharp_mask": True, "invert": True, "char_set": "basic"},
          {"contrast": 2.2, "unsharp_mask": True, "unsharp_radius": 1.5, "adaptive_thresh": True, "dither": True},
          {"hist_equal": True, "enhance_edges": True, "edge_mode": "standard", "invert": True, "width": 45}]
    return c


def run_case(img, case):
    settings = {"width": 30, **{k: v for k, v in case.items() if k != "preview"}}
    s = ascii_pipeline.normalise(settings)
    text = ascii_pipeline.convert(img, s, preview=case.get("preview", False))
    return s, text


def build():
    images = [("synthetic 61x47", test_image(61, 47, 1)), ("synthetic 37x52", test_image(37, 52, 2))]
    out = {"char_sets": ASCIIArtGenerator.CHAR_SETS, "images": [], "cases": []}
    for i, (name, img) in enumerate(images):
        rgba = np.array(img.convert("RGBA"))
        out["images"].append({"name": name, "w": img.width, "h": img.height,
                              "rgba": base64.b64encode(rgba.tobytes()).decode()})
        for case in cases():
            s, text = run_case(img, case)
            out["cases"].append({"image": i, "case": case, "settings": s, "preview": case.get("preview", False),
                                 "float": any(s[k] not in (1.0, False) for k in FLOAT_KEYS), "text": text})
    sample = out["cases"][0]["text"] + "\n<il> & \"q\" 'a'"
    out["html_sample"] = {"text": sample, "font_px": 10, "html": ascii_export.to_html(sample, 10)}
    return out, images


def main():
    data, _ = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=0))
    print(f"{len(data['cases'])} cases -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
