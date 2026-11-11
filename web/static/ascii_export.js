// Export helpers, mirroring ascii_export.py: the GUI's HTML page template (text HTML-escaped) and a PNG drawn on a
// canvas with one fixed cell per character (the block characters drawn as shaded cells, as in Python).
export const BLOCK_SHADES = { '░': 0.25, '▒': 0.5, '▓': 0.75, '█': 1 };

// html.escape(text, quote=False)
const escapeHtml = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export function toHtml(text, fontPx = 10) {
  return '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n<title>ASCII Art</title>\n'
    + `<style>pre { font-family: monospace; font-size: ${Math.trunc(fontPx)}px; line-height: 1.0; white-space: pre; }</style>\n`
    + `</head>\n<body>\n<pre>${escapeHtml(text)}</pre>\n</body>\n</html>`;
}

const hex = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));

// Draw the text on a canvas: fg characters on a bg background, fontSize px monospace.
export function toCanvas(text, { fontSize = 12, fg = '#000000', bg = '#ffffff' } = {}) {
  const lines = text.split('\n').map(l => Array.from(l));
  const font = `${fontSize}px ui-monospace, Menlo, Consolas, "DejaVu Sans Mono", monospace`;
  const probe = document.createElement('canvas').getContext('2d');
  probe.font = font;
  const cw = Math.max(1, Math.ceil(probe.measureText('M').width)), ch = Math.max(1, Math.round(fontSize * 1.2));
  const cols = Math.max(1, ...lines.map(l => l.length));
  const canvas = document.createElement('canvas');
  canvas.width = cols * cw; canvas.height = Math.max(1, lines.length) * ch;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.font = font; ctx.textBaseline = 'middle'; ctx.textAlign = 'center';
  const [f0, f1, f2] = hex(fg), [b0, b1, b2] = hex(bg);
  lines.forEach((line, r) => line.forEach((c, i) => {
    const x = i * cw, y = r * ch;
    if (c in BLOCK_SHADES) {
      const a = BLOCK_SHADES[c];
      ctx.fillStyle = `rgb(${Math.round(b0 + (f0 - b0) * a)},${Math.round(b1 + (f1 - b1) * a)},${Math.round(b2 + (f2 - b2) * a)})`;
      ctx.fillRect(x, y, cw, ch);
    } else if (c.trim()) {
      ctx.fillStyle = fg; ctx.fillText(c, x + cw / 2, y + ch / 2);
    }
  }));
  return canvas;
}

export const toPngBlob = (text, opts) => new Promise((res, rej) =>
  toCanvas(text, opts).toBlob(b => (b ? res(b) : rej(new Error('The picture is too large to save as PNG.'))), 'image/png'));

export async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch (e) { /* fall back below */ }
  const ta = document.createElement('textarea');
  ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta); ta.select();
  const ok = document.execCommand('copy'); ta.remove();
  return ok;
}
