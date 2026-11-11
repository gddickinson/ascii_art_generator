# ASCII Art Generator

@INTERFACE.md

## Quick Start
```bash
pip install -r requirements.txt
python ascii_art_generator.py input.jpg --preview
python gui_application.py  # GUI mode
python run_web.py          # web app, http://127.0.0.1:8174
```

## Testing
```bash
pytest tests/ -v
node web/static/ascii_engine.test.mjs   # JS port vs Python fixture
python scripts/make_ascii_fixture.py      # after changing ascii_pipeline / the JS engine
```
Keep `web/static/ascii_engine.js` (+ pil_ops.js, cv_ops.js) in step with `ascii_pipeline.py`.

## Dependencies
- Pillow (image loading/processing)
- numpy (pixel array manipulation)
- opencv-python (advanced edge detection, histogram equalization)
