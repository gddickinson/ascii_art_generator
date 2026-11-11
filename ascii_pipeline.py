"""
GUI-free conversion pipeline: image + settings -> ASCII text.

Used by the Tkinter GUI (gui_application.py) and the web app (web/), so both run the same steps in the same
order. The steps reuse ImageProcessor and ASCIIArtGenerator:

    resize (Lanczos) -> greyscale -> sharpness -> contrast -> brightness -> histogram equalisation
    -> edge detection -> unsharp mask -> adaptive thresholding -> invert -> dither -> map to characters

With only the command-line options set (width, height, char set, contrast, brightness, invert, dither) the
result is identical to ASCIIArtGenerator.direct_convert. The JavaScript port in web/static/ascii_engine.js
follows the same order and is tested against this module (tests/fixtures/ascii_fixture.json).
"""

from PIL import Image

from ascii_art_generator import ASCIIArtGenerator
from image_processor import ImageProcessor

EDGE_MODES = ("standard", "sobel", "canny")

# Defaults (the GUI's "Reset to Defaults" values). height None = automatic from the aspect ratio.
DEFAULTS = {
    "width": 100, "height": None, "char_set": "standard",
    "custom_chars": ASCIIArtGenerator.CHAR_SETS["standard"],
    "invert": False, "dither": False,
    "contrast": 1.0, "brightness": 1.0, "sharpness": 1.0,
    "hist_equal": False, "enhance_edges": False, "edge_mode": "standard",
    "unsharp_mask": False, "unsharp_radius": 2.0, "unsharp_amount": 1.5,
    "adaptive_thresh": False, "thresh_block": 11, "thresh_c": 2,
}

# Numeric ranges, as offered by the GUI's spinboxes and sliders.
RANGES = {
    "width": (1, 500, 1), "height": (1, 500, 1),
    "contrast": (0.1, 3.0, 0.1), "brightness": (0.1, 3.0, 0.1), "sharpness": (0.1, 5.0, 0.1),
    "unsharp_radius": (0.5, 5.0, 0.5), "unsharp_amount": (0.5, 3.0, 0.1),
    "thresh_block": (3, 51, 2), "thresh_c": (0, 10, 1),
}
INT_KEYS = ("width", "height", "thresh_block", "thresh_c")
BOOL_KEYS = ("invert", "dither", "hist_equal", "enhance_edges", "unsharp_mask", "adaptive_thresh")

# The GUI's "Generate Preview" limits.
PREVIEW_MAX_WIDTH = 80
PREVIEW_MAX_HEIGHT = 40


def normalise(settings=None):
    """Return a complete, validated settings dict (missing keys take DEFAULTS). Raises ValueError."""
    s = dict(DEFAULTS)
    s.update({k: v for k, v in (settings or {}).items() if k in DEFAULTS})
    for k in BOOL_KEYS:
        v = s[k]
        s[k] = v.lower() in ("1", "true", "yes", "on") if isinstance(v, str) else bool(v)
    if s["height"] in ("", 0, "auto"):
        s["height"] = None
    for k, (lo, hi, _step) in RANGES.items():
        if s[k] is None:
            continue
        try:
            v = float(s[k])
        except (TypeError, ValueError):
            raise ValueError(f"{k} must be a number")
        if not lo <= v <= hi:
            raise ValueError(f"{k} must be between {lo} and {hi}")
        s[k] = int(v) if k in INT_KEYS else v
    if s["char_set"] not in ASCIIArtGenerator.CHAR_SETS:
        raise ValueError(f"unknown character set {s['char_set']!r}")
    if s["edge_mode"] not in EDGE_MODES:
        raise ValueError(f"edge_mode must be one of {', '.join(EDGE_MODES)}")
    if s["char_set"] == "custom" and not s["custom_chars"]:
        raise ValueError("custom characters cannot be empty")
    return s


def chars_for(settings):
    """Characters, from darkest to brightest pixel, for normalised settings."""
    if settings["char_set"] == "custom":
        return settings["custom_chars"]
    return ASCIIArtGenerator.CHAR_SETS[settings["char_set"]]


def output_size(image_size, settings):
    """(columns, rows) of the result for an image of image_size = (width, height)."""
    width = settings["width"]
    height = settings["height"]
    if height is None:
        height = ASCIIArtGenerator.auto_height(image_size[0], image_size[1], width)
    return width, height


def preview_size(image_size, settings):
    """(columns, rows) for the GUI's quick preview: width at most 80, a fixed height at most 40."""
    width = min(PREVIEW_MAX_WIDTH, settings["width"])
    if settings["height"] is None:
        return width, ASCIIArtGenerator.auto_height(image_size[0], image_size[1], width)
    return width, min(PREVIEW_MAX_HEIGHT, settings["height"])


def prepare(image):
    """Image modes other than L and RGB (palette, RGBA, ...) are converted to RGB; alpha is dropped."""
    return image if image.mode in ("L", "RGB") else image.convert("RGB")


def process(image, settings, size=None):
    """Run the image steps; returns the processed greyscale ('L') PIL image of the output size."""
    s = normalise(settings)
    image = prepare(image)
    width, height = size or output_size(image.size, s)
    p = ImageProcessor()
    p.debug_mode = False
    p.from_pil_image(image)
    p.resize(width, height)
    p.to_grayscale()
    if s["sharpness"] != 1.0:
        p.adjust_sharpness(s["sharpness"])
    if s["contrast"] != 1.0:
        p.adjust_contrast(s["contrast"])
    if s["brightness"] != 1.0:
        p.adjust_brightness(s["brightness"])
    if s["hist_equal"]:
        p.apply_histogram_equalization()
    if s["enhance_edges"]:
        p.detect_edges(s["edge_mode"])
    if s["unsharp_mask"]:
        p.apply_unsharp_mask(radius=s["unsharp_radius"], amount=s["unsharp_amount"])
    if s["adaptive_thresh"]:
        p.apply_adaptive_thresholding(block_size=s["thresh_block"], c=s["thresh_c"])
    if s["invert"]:
        p.invert()
    if s["dither"]:
        p.apply_dithering()
    return p.get_processed_image()


def to_ascii(gray, chars):
    """Map a greyscale image to text with ASCIIArtGenerator's character mapping."""
    gen = ASCIIArtGenerator(debug=False)
    gen.chars = chars
    return "\n".join("".join(row) for row in gen._map_pixels_to_ascii(gray))


def convert(image, settings=None, preview=False):
    """Convert a PIL image to ASCII text with the given settings (see DEFAULTS)."""
    s = normalise(settings)
    image = prepare(image)
    size = preview_size(image.size, s) if preview else output_size(image.size, s)
    return to_ascii(process(image, s, size), chars_for(s))


def convert_file(path, settings=None, preview=False):
    with Image.open(path) as img:
        img.load()
        return convert(img, settings, preview)
