# ASCII Art Generator -- Roadmap

## Current State
A functional image-to-ASCII converter with three modules: `ascii_art_generator.py` (core logic), `gui_application.py` (Tkinter GUI), and `image_processor.py` (preprocessing). Supports multiple character sets, dithering, contrast/brightness adjustment, and output to text/HTML/image. Has CLI and GUI interfaces. Has `requirements.txt`, `.gitignore`, pytest tests, and `INTERFACE.md`.

## Short-term Improvements
- [x] Add `requirements.txt` listing Pillow and any other dependencies
- [x] Add unit tests for `ascii_art_generator.py` -- test character mapping, width/height calculations, edge cases (empty images, very small images)
- [x] Fix the `-h` flag conflict in CLI (README shows `-h` for both help and height)
- [ ] Add input validation in `ascii_art_generator.py` for unsupported image formats and corrupt files
- [ ] Add proper error messages when Tkinter is unavailable (headless environments)
- [ ] Extract CLI argument parsing from `ascii_art_generator.py` into a separate `cli.py` module
- [x] Remove test artifacts (`test_ascii.txt`, `test.jpeg`) from the repository or move to `tests/` directory

## Feature Enhancements
- [ ] Add color ASCII art output (ANSI terminal colors and colored HTML)
- [ ] Support animated GIF input -- convert to ASCII animation frame by frame
- [ ] Add batch processing mode to convert entire directories of images
- [ ] Implement video-to-ASCII conversion (MP4/AVI input)
- [ ] Add drag-and-drop support in `gui_application.py`
- [ ] Add undo/redo for parameter changes in the GUI
- [ ] Add a "copy to clipboard" button for quick ASCII sharing
- [ ] Support Unicode block characters for higher-resolution output

## Long-term Vision
- [ ] Publish to PyPI as an installable package with `pyproject.toml`
- [ ] Build a web version using Flask/FastAPI backend with the same core engine
- [ ] Add ML-based edge detection in `image_processor.py` for better detail preservation
- [ ] Create VS Code extension for inline ASCII art generation
- [ ] Add style transfer preprocessing -- convert photos to line art before ASCII conversion

## Technical Debt
- [x] `usage_examples.py` should be moved to an `examples/` directory
- [x] `gui_application.py` likely exceeds 500 lines -- split into separate widget modules
- [ ] No separation between presentation and logic in the GUI -- extract a controller layer
- [ ] `image_processor.py` and `ascii_art_generator.py` have overlapping image loading code -- deduplicate
- [ ] Add logging instead of print statements for debugging
- [x] No `.gitignore` to exclude `__pycache__/` and generated output files
