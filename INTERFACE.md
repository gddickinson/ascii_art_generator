# ASCII Art Generator -- Interface Map

## Modules
- `ascii_art_generator.py` -- `ASCIIArtGenerator` class; core conversion logic (character mapping, preprocessing, CLI entry point)
- `image_processor.py` -- `ImageProcessor` class; advanced image preprocessing (edge detection, histogram equalization, thresholding)
- `ascii_pipeline.py` -- GUI-free conversion pipeline (settings dict -> text) used by the GUI and the web app
- `ascii_export.py` -- `to_html()` (GUI page template, escaped) and `to_png_image()` / `save_png()` (text rendered on a grid)
- `gui_application.py` -- `ASCIIArtApp` (Tkinter); main GUI application with preview, generation, and save
- `gui_settings.py` -- GUI settings panel creation and toggle/update callbacks (extracted from gui_application)
- `run_web.py` -- starts the local web app (uvicorn, http://127.0.0.1:8174)

## Key Classes / Functions
- `ASCIIArtGenerator` (ascii_art_generator.py)
  - `convert_image(path)` -- Convert image file to ASCII string
  - `direct_convert(pil_image)` -- Convert PIL Image to ASCII string
  - `auto_height(img_w, img_h, width)` -- rows for a width (aspect ratio x 0.5, at least 1)
  - `save_to_file(ascii_art, path)` -- Save output to text file
  - `CHAR_SETS` -- Dict of available character density maps
- `ImageProcessor` (image_processor.py)
  - Chainable methods: `load()`, `resize()`, `to_grayscale()`, `adjust_contrast()`, etc.
  - `get_processed_image()` -- Return processed PIL Image
- `ascii_pipeline` -- `DEFAULTS`, `RANGES`, `EDGE_MODES`, `normalise(settings)`, `process(image, settings)` (greyscale
  PIL image), `convert(image, settings, preview=False)`, `convert_file(path, ...)`, `output_size()`, `preview_size()`
  Step order: resize -> grey -> sharpness -> contrast -> brightness -> hist. eq. -> edges -> unsharp -> threshold -> invert -> dither -> map
- `ASCIIArtApp._generate_ascii_art` (gui_application.py) calls `ascii_pipeline.convert_file`; Save As uses `ascii_export`

## Web interface (`web/`)
- `web/app.py` -- FastAPI: `GET /api/info` (char sets, defaults, ranges, labels), `POST /api/convert` (multipart image +
  JSON settings -> Python pipeline); `STATIC_ENDPOINTS` exported to JSON for the static site
- `web/convert_api.py` -- `convert_bytes(data, settings_json, preview)` (upload limits, demo image when no file)
- `web/static/` -- plain ES modules, no build step:
  - `core.js`, `style.css` (shared web kit, unchanged), `style_app.css`, `index.html`, `main.js` (router), `static_api.js`
  - pages: `home.js`, `convert.js` (+ `convert_controls.js`, `convert_output.js`), `gallery.js` (+ `presets.js`), `about.js`
  - JS port of the pipeline: `ascii_engine.js` (steps + mapping) on `pil_ops.js` (Pillow: Lanczos resize, RGB->L,
    ImageEnhance blends, 3x3 filters, box-blur Gaussian / unsharp mask, Floyd-Steinberg) and `cv_ops.js` (OpenCV:
    equalizeHist, Sobel, Canny, adaptiveThreshold); `ascii_engine.test.mjs` checks it against the fixture
  - `ascii_export.js` (HTML template, PNG via canvas, copy), `image_load.js` (file -> RGBA in the browser)
  - `demo.png` drawn by `scripts/make_demo_image.py`
- `scripts/build_static.py` (GitHub Pages export to site/), `scripts/screenshots.py` (smoke test, docs/img),
  `scripts/make_ascii_fixture.py` (writes `tests/fixtures/ascii_fixture.json`), `scripts/make_demo_image.py`
- `.github/workflows/pages.yml` -- tests, builds and publishes the static site on push to main

## CLI Usage
```
python ascii_art_generator.py input.jpg -w 120 -H 60 --char-set basic --preview
```
Note: `-H` for height (not `-h`, which is reserved for help).

## Tests
- `tests/test_ascii_art_generator.py` -- pytest unit tests for ASCIIArtGenerator
- `tests/test_image_processor.py` -- ImageProcessor (unsharp mask percent, step chaining)
- `tests/test_gui_generation.py` -- the GUI's generate/save code paths without a window (pipeline, HTML/PNG export)
- `tests/test_web.py` -- web API, static build, node test of the JS engine, fixture still current

## Examples
- `examples/usage_examples.py` -- Scripted usage examples
