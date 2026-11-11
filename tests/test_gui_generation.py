"""Regression tests for the GUI's generation path (ASCIIArtApp._generate_ascii_art) without opening a window.

The method is called on a stand-in object that has the GUI's tk variables replaced by plain values, so the test
exercises exactly the code that runs when the user clicks "Generate Preview" / "Generate Full".
"""

import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("tkinter")
from ascii_art_generator import ASCIIArtGenerator  # noqa: E402
import gui_application  # noqa: E402


class Var:
    def __init__(self, v):
        self.v = v

    def get(self):
        return self.v


class FakeText:
    def __init__(self):
        self.text = ""

    def config(self, **kw):
        pass

    def delete(self, *a):
        self.text = ""

    def insert(self, _pos, text):
        self.text = text


def fake_app(path, **over):
    vals = dict(char_set="standard", custom_chars=ASCIIArtGenerator.CHAR_SETS["standard"], invert=False,
                dither=False, contrast=1.0, brightness=1.0, sharpness=1.0, hist_equal=False, enhance_edges=False,
                edge_mode="standard", unsharp_mask=False, unsharp_radius=2.0, unsharp_amount=1.5,
                adaptive_thresh=False, thresh_block=11, thresh_c=2, font_size=10)
    vals.update(over)
    app = SimpleNamespace(input_image_path=str(path), ascii_text=FakeText(), ascii_result=None)
    for k, v in vals.items():
        setattr(app, k + "_var", Var(v))
    return app


@pytest.fixture
def colour_image(tmp_path):
    """Green left half, red right half, a blue band: grey levels that the red channel alone gets wrong."""
    arr = np.zeros((40, 60, 3), np.uint8)
    arr[:, :30] = (0, 200, 0)
    arr[:, 30:] = (220, 0, 0)
    arr[15:25, :] = (40, 40, 250)
    path = tmp_path / "colour.png"
    Image.fromarray(arr).save(path)
    return path


def gui_convert(path, width, height, **over):
    app = fake_app(path, **over)
    gui_application.ASCIIArtApp._generate_ascii_art(app, width, height)
    return app.ascii_result


@pytest.mark.parametrize("opts", [{}, {"invert": True}, {"dither": True}, {"invert": True, "dither": True}])
def test_gui_matches_command_line_conversion(colour_image, opts):
    """With no extra processing the GUI must give the same text as the CLI (grey levels, invert, dither, size)."""
    cli = ASCIIArtGenerator(width=24, debug=False, **opts).convert_image(str(colour_image))
    assert gui_convert(colour_image, 24, None, **opts) == cli


def test_gui_auto_height_uses_character_aspect(colour_image):
    """Generate Full with auto height must give width * aspect * 0.5 rows, like the height shown in the GUI."""
    rows = gui_convert(colour_image, 30, None).split("\n")
    assert len(rows) == 10 and len(rows[0]) == 30


def test_gui_custom_chars_do_not_change_shared_char_sets(colour_image):
    before = dict(ASCIIArtGenerator.CHAR_SETS)
    out = gui_convert(colour_image, 12, 4, char_set="custom", custom_chars=" #")
    assert set(out.replace("\n", "")) <= {" ", "#"}
    assert ASCIIArtGenerator.CHAR_SETS == before
