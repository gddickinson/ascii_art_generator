"""Unit tests for ImageProcessor (image_processor.py)."""

import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image_processor import ImageProcessor  # noqa: E402


def _noise_image():
    rng = np.random.RandomState(3)
    return Image.fromarray((rng.rand(24, 32) * 255).astype(np.uint8), "L")


def _processor(img):
    p = ImageProcessor()
    p.debug_mode = False
    return p.from_pil_image(img)


def test_unsharp_mask_with_fractional_amount():
    """amount=1.5 (the GUI default) gave percent=150.0, which Pillow rejects ('float' ... integer)."""
    img = _noise_image()
    out = _processor(img).apply_unsharp_mask(radius=2, amount=1.5).get_processed_image()
    expected = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
    assert np.array_equal(np.array(out), np.array(expected))


def test_unsharp_mask_rounds_percent():
    img = _noise_image()
    out = _processor(img).apply_unsharp_mask(radius=1.0, amount=1.234).get_processed_image()
    expected = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=123))
    assert np.array_equal(np.array(out), np.array(expected))


def test_pipeline_steps_keep_size_and_mode():
    img = _noise_image()
    p = _processor(img)
    p.apply_histogram_equalization().detect_edges("sobel").apply_adaptive_thresholding(11, 2)
    out = p.get_processed_image()
    assert out.size == img.size and out.mode == "L"
