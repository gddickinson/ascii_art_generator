# Session log

## 2026-11-11 -- web interface and GitHub Pages site (branch `web-interface`)
- Added a local web app (`python run_web.py`, FastAPI, port 8174) and a static GitHub Pages site (`scripts/build_static.py`,
  `.github/workflows/pages.yml`) from the shared web kit. Pages: home, converter, gallery, about.
- The static site converts the user's own image in the browser (nothing uploaded) with every option of the GUI pipeline.
  The conversion was ported to JS (`web/static/ascii_engine.js`, `pil_ops.js`, `cv_ops.js`) from Pillow 13 / OpenCV 5.0
  C sources. `scripts/make_ascii_fixture.py` converts two generated test images with 38 option combinations each
  (76 cases); the node test requires the JS text to equal Python's exactly: 76/76 identical (57,092 characters).
  The local app can convert with Python and shows a JS-vs-Python cross-check (identical on the demo, a PNG and a JPEG).
- Downloads: .txt, .html (GUI template) and .png (canvas); copy to clipboard. Demo image drawn by `scripts/make_demo_image.py`.
- Bugs found and fixed in existing code (separate commits, regression tests first):
  1. `ASCIIArtGenerator` stored the auto height on `self` (wrong height for a second image) and crashed with 0 rows
     for very wide images.
  2. `ImageProcessor.apply_unsharp_mask` passed a float percent; Pillow raises TypeError, so the GUI option always failed.
  3. GUI generation ignored Invert/Dither, used only the red channel of colour images, and "Generate Full" with auto
     height was twice as tall; custom characters overwrote the class-wide `CHAR_SETS['custom']`. Fixed by moving the
     steps into the new GUI-free `ascii_pipeline.py` (the GUI now matches the CLI for the CLI options).
  4. GUI Save as HTML did not escape `<`/`&` (art partly hidden); Save as Image called the non-existent `Image.grab`.
     New `ascii_export.py`.
  5. README: `-h HEIGHT` -> `-H`, install all requirements, clone URL.
- Note for George: the GUI's output for colour images changes (grey instead of red channel) and its full-size height
  halves; both are the bug fixes above. `ascii_pipeline.DEFAULTS['custom_chars']` is the built-in "custom" set, so
  `char_set='custom'` matches `--char-set custom` (the GUI passes its own field text).
