"""FastAPI web app for the ASCII Art Generator: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8174, local only). `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes below. POST
/api/convert runs the repo's Python pipeline (ascii_pipeline.py); the static site converts in the browser with the JS
port (static/ascii_engine.js) instead.
"""
import json
import sys
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ascii_pipeline  # noqa: E402
from ascii_art_generator import ASCIIArtGenerator  # noqa: E402
from web.convert_api import MAX_UPLOAD_BYTES, convert_bytes  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
FIXTURE = ROOT / "tests" / "fixtures" / "ascii_fixture.json"

app = FastAPI(title="ASCII Art Generator")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

# Control labels and help, worded as in the desktop GUI (gui_settings.py) and README.
LABELS = {
    "width": ("Width", "Number of characters per line"),
    "height": ("Height", "Number of lines (auto keeps the aspect ratio)"),
    "char_set": ("Character set", "Character collection, from darkest to brightest pixel"),
    "custom_chars": ("Custom characters", "Your own density map, from darkest to lightest"),
    "contrast": ("Contrast", "Adjust image contrast"),
    "brightness": ("Brightness", "Adjust image brightness"),
    "sharpness": ("Sharpness", "Adjust image sharpness"),
    "hist_equal": ("Histogram equalization", "Improve contrast across the entire range"),
    "enhance_edges": ("Enhance edges", "Highlight edges"),
    "edge_mode": ("Edge mode", "standard (Pillow FIND_EDGES), sobel (gradient magnitude) or canny (OpenCV)"),
    "unsharp_mask": ("Unsharp mask", "Enhance edges while preserving appearance"),
    "unsharp_radius": ("Radius", "Unsharp mask radius"),
    "unsharp_amount": ("Amount", "Unsharp mask strength"),
    "adaptive_thresh": ("Adaptive thresholding", "Better detail in varied lighting (black/white result)"),
    "thresh_block": ("Block size", "Neighbourhood size for the threshold (odd)"),
    "thresh_c": ("Constant", "Subtracted from the neighbourhood mean"),
    "invert": ("Invert colors", "Reverse dark and light values"),
    "dither": ("Apply dithering", "Floyd-Steinberg dithering to black and white, adds texture"),
}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Character sets, defaults, ranges and labels for the pages (from ascii_pipeline / ASCIIArtGenerator)."""
    n_cases = len(json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]) if FIXTURE.exists() else 0
    return {
        "title": "ASCII Art Generator",
        "description": "A Python application for converting images to high-quality ASCII art.",
        "repo": "ascii_art_generator",
        "char_sets": ASCIIArtGenerator.CHAR_SETS,
        "defaults": ascii_pipeline.DEFAULTS,
        "ranges": {k: list(v) for k, v in ascii_pipeline.RANGES.items()},
        "edge_modes": list(ascii_pipeline.EDGE_MODES),
        "preview_max": {"width": ascii_pipeline.PREVIEW_MAX_WIDTH, "height": ascii_pipeline.PREVIEW_MAX_HEIGHT},
        "labels": {k: {"label": a, "help": b} for k, (a, b) in LABELS.items()},
        "font_size": {"default": 10, "min": 4, "max": 24},
        "js_test_cases": n_cases,
    }


@app.post("/api/convert")
async def convert(file: UploadFile | None = File(None), settings: str = Form("{}"), preview: bool = Form(False)):
    """Convert an uploaded image (or the demo image when no file is sent) with ascii_pipeline.convert."""
    data = await file.read(MAX_UPLOAD_BYTES + 1) if file is not None else None
    try:
        return convert_bytes(data, settings, preview)
    except ValueError as e:
        raise HTTPException(400, str(e))


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info"]
