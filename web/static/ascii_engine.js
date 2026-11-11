// ASCII art engine: the JS port of ascii_pipeline.py (same steps, same order, same character mapping), built on
// pil_ops.js (Pillow) and cv_ops.js (OpenCV). Node-tested against the Python pipeline: ascii_engine.test.mjs.
//
//   resize (Lanczos) -> greyscale -> sharpness -> contrast -> brightness -> histogram equalisation
//   -> edge detection -> unsharp mask -> adaptive thresholding -> invert -> dither -> characters
import * as P from './pil_ops.js';
import * as C from './cv_ops.js';

// ASCIIArtGenerator.CHAR_SETS (darkest pixel first). The test checks these against the Python dict.
export const CHAR_SETS = {
  basic: ' .:-=+*#%@',
  standard: ' .`^",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
  blocks: ' ░▒▓█',
  custom: ' .",:;!~+-xmo*#W&8%B@$',
};
export const PREVIEW_MAX = { width: 80, height: 40 };

// ASCIIArtGenerator.auto_height: rows keeping the aspect ratio for character cells about twice as tall as wide.
export const autoHeight = (imgW, imgH, width) => Math.max(1, Math.trunc(width * (imgH / imgW) * 0.5));

export function outputSize(imgW, imgH, s, preview = false) {
  if (preview) {
    const w = Math.min(PREVIEW_MAX.width, s.width);
    return [w, s.height == null ? autoHeight(imgW, imgH, w) : Math.min(PREVIEW_MAX.height, s.height)];
  }
  return [s.width, s.height == null ? autoHeight(imgW, imgH, s.width) : s.height];
}

export const charsFor = s => (s.char_set === 'custom' ? s.custom_chars : CHAR_SETS[s.char_set]);

// The image steps after resizing to greyscale (ascii_pipeline.process from p.to_grayscale() on).
export function processGray(g, s) {
  if (s.sharpness !== 1) g = P.sharpness(g, s.sharpness);
  if (s.contrast !== 1) g = P.contrast(g, s.contrast);
  if (s.brightness !== 1) g = P.brightness(g, s.brightness);
  if (s.hist_equal) g = C.equalizeHist(g);
  if (s.enhance_edges) {
    g = s.edge_mode === 'sobel' ? C.sobelEdges(g) : s.edge_mode === 'canny' ? C.canny(g, 100, 200) : P.findEdges(g);
  }
  if (s.unsharp_mask) g = P.unsharpMask(g, s.unsharp_radius, Math.round(s.unsharp_amount * 100), 3);
  if (s.adaptive_thresh) g = C.adaptiveThreshold(g, s.thresh_block, s.thresh_c);
  if (s.invert) g = P.invert(g);
  if (s.dither) g = P.dither(g);
  return g;
}

// ASCIIArtGenerator._map_pixels_to_ascii: index = int(value * (n - 1) / 255).
export function toAscii(g, chars) {
  const cs = Array.from(chars), n = cs.length, lines = [];
  for (let y = 0; y < g.h; y++) {
    let line = '';
    for (let x = 0; x < g.w; x++) line += cs[Math.max(0, Math.min(Math.trunc(g.data[y * g.w + x] * (n - 1) / 255), n - 1))];
    lines.push(line);
  }
  return lines.join('\n');
}

// A converter for one RGBA image (canvas ImageData layout). The resized greyscale image is cached per output
// size, so changing any other option only reruns the cheap steps.
export function makeConverter(rgba, imgW, imgH) {
  const cache = new Map();
  const resized = (w, h) => {
    const key = w + 'x' + h;
    if (!cache.has(key)) { if (cache.size > 6) cache.clear(); cache.set(key, P.resizeRGBAtoL(rgba, imgW, imgH, w, h)); }
    return cache.get(key);
  };
  return function convert(s, { preview = false } = {}) {
    const chars = charsFor(s);
    if (!chars || !Array.from(chars).length) throw new Error('custom characters cannot be empty');
    const [w, h] = outputSize(imgW, imgH, s, preview);
    const g = processGray(resized(w, h), s);
    return { text: toAscii(g, chars), cols: w, rows: h, gray: g };
  };
}

export const convertRGBA = (rgba, imgW, imgH, s, opts) => makeConverter(rgba, imgW, imgH)(s, opts);
