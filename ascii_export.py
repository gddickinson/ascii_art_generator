"""
Export ASCII art as HTML or as a PNG picture (used by the GUI's "Save As..." and by the web app).

to_html keeps the GUI's page template; the text is HTML-escaped so characters such as '<' and '&' in the
'standard' set display as themselves. to_png draws every character in a fixed grid cell with a monospace
font (falling back to Pillow's default font), and draws the block characters of the 'blocks' set as shaded
cells so they look right whatever font is installed.
"""

import html

from PIL import Image, ImageDraw, ImageFont

HTML_TEMPLATE = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    '<meta charset="UTF-8">\n<title>ASCII Art</title>\n'
    "<style>pre {{ font-family: monospace; font-size: {font_px}px; "
    "line-height: 1.0; white-space: pre; }}</style>\n"
    "</head>\n<body>\n<pre>"
    "{text}</pre>\n</body>\n</html>"
)

# Share of the foreground colour in a cell for the Unicode block characters.
BLOCK_SHADES = {"░": 0.25, "▒": 0.5, "▓": 0.75, "█": 1.0}

MONOSPACE_FONTS = (
    "Menlo.ttc", "/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf",
    "DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "LiberationMono-Regular.ttf", "consola.ttf", "cour.ttf",
)


def to_html(text, font_px=10):
    """A standalone HTML page showing the text in a <pre> block."""
    return HTML_TEMPLATE.format(font_px=int(font_px), text=html.escape(text, quote=False))


def _font(size):
    for name in MONOSPACE_FONTS:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def to_png_image(text, font_size=12, fg=(0, 0, 0), bg=(255, 255, 255)):
    """Render the text to an RGB PIL image (fg on bg), one fixed-size cell per character."""
    font = _font(font_size)
    lines = text.split("\n")
    cell_w = max(1, round(font.getlength("M")))
    ascent, descent = font.getmetrics() if hasattr(font, "getmetrics") else (font_size, 0)
    cell_h = max(1, ascent + descent)
    cols = max((len(line) for line in lines), default=0)
    img = Image.new("RGB", (max(1, cols * cell_w), max(1, len(lines) * cell_h)), bg)
    draw = ImageDraw.Draw(img)
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            x, y = c * cell_w, r * cell_h
            if ch in BLOCK_SHADES:
                a = BLOCK_SHADES[ch]
                colour = tuple(round(b + (f - b) * a) for f, b in zip(fg, bg))
                draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], fill=colour)
            elif not ch.isspace():
                draw.text((x, y), ch, font=font, fill=fg)
    return img


def save_png(text, path, **kw):
    """Render the text (see to_png_image) and save it; the format follows the file extension."""
    to_png_image(text, **kw).save(path)
