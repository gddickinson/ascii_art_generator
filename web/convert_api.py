"""Server-side conversion for the local web app: uploaded image bytes + settings -> ascii_pipeline.convert."""
import io
import json
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ascii_pipeline  # noqa: E402

DEMO_IMAGE = Path(__file__).resolve().parent / "static" / "demo.png"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_PIXELS = 50_000_000


def convert_bytes(data, settings_json="{}", preview=False):
    """Convert image bytes (None = the demo image) with JSON settings; raises ValueError for bad input."""
    try:
        settings = json.loads(settings_json or "{}")
    except json.JSONDecodeError as e:
        raise ValueError(f"settings are not valid JSON: {e}")
    if not isinstance(settings, dict):
        raise ValueError("settings must be a JSON object")
    s = ascii_pipeline.normalise(settings)
    if data is None:
        data = DEMO_IMAGE.read_bytes()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("image too large for the web app (25 MB); use the command line or the GUI")
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.width * img.height > MAX_PIXELS:
                raise ValueError("image has more than 50 megapixels; use the command line or the GUI")
            img.load()
            text = ascii_pipeline.convert(img, s, preview=preview)
            size = img.size
    except UnidentifiedImageError:
        raise ValueError("the file is not an image format Pillow can read")
    except (OSError, Image.DecompressionBombError) as e:
        raise ValueError(f"could not read the image: {e}")
    lines = text.split("\n")
    return {"engine": "python", "text": text, "cols": len(lines[0]) if lines else 0, "rows": len(lines),
            "image": {"w": size[0], "h": size[1]}, "settings": s}
