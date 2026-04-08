# ASCII Art Generator -- Interface Map

## Modules
- `ascii_art_generator.py` -- `ASCIIArtGenerator` class; core conversion logic (character mapping, preprocessing, CLI entry point)
- `image_processor.py` -- `ImageProcessor` class; advanced image preprocessing (edge detection, histogram equalization, thresholding)
- `gui_application.py` -- `ASCIIArtApp` (Tkinter); main GUI application with preview, generation, and save
- `gui_settings.py` -- GUI settings panel creation and toggle/update callbacks (extracted from gui_application)

## Key Classes
- `ASCIIArtGenerator` (ascii_art_generator.py)
  - `convert_image(path)` -- Convert image file to ASCII string
  - `direct_convert(pil_image)` -- Convert PIL Image to ASCII string
  - `save_to_file(ascii_art, path)` -- Save output to text file
  - `CHAR_SETS` -- Dict of available character density maps
- `ImageProcessor` (image_processor.py)
  - Chainable methods: `load()`, `resize()`, `to_grayscale()`, `adjust_contrast()`, etc.
  - `get_processed_image()` -- Return processed PIL Image

## CLI Usage
```
python ascii_art_generator.py input.jpg -w 120 -H 60 --char-set basic --preview
```
Note: `-H` for height (not `-h`, which is reserved for help).

## Tests
- `tests/test_ascii_art_generator.py` -- pytest unit tests for ASCIIArtGenerator

## Examples
- `examples/usage_examples.py` -- Scripted usage examples
