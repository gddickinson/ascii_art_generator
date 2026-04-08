# ASCII Art Generator

@INTERFACE.md

## Quick Start
```bash
pip install -r requirements.txt
python ascii_art_generator.py input.jpg --preview
python gui_application.py  # GUI mode
```

## Testing
```bash
pytest tests/ -v
```

## Dependencies
- Pillow (image loading/processing)
- numpy (pixel array manipulation)
- opencv-python (advanced edge detection, histogram equalization)
