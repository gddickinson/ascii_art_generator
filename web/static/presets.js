// Named combinations of the real options, shown on the gallery and home pages (each opens in the converter).
export const PRESETS = [
  { name: 'standard', note: 'The default 70-character set.', s: {} },
  { name: 'basic', note: 'Ten characters, bold shapes.', s: { char_set: 'basic' } },
  { name: 'blocks', note: 'Unicode shade blocks ░▒▓█.', s: { char_set: 'blocks' } },
  { name: 'custom set', note: 'The built-in mid-detail "custom" set.', s: { char_set: 'custom' } },
  { name: 'inverted', note: 'Dark and light swapped, for dark text on paper.', s: { invert: true } },
  { name: 'dithered', note: 'Floyd–Steinberg dithering to black and white.', s: { char_set: 'basic', dither: true } },
  { name: 'edges: standard', note: 'Pillow FIND_EDGES filter.', s: { enhance_edges: true, edge_mode: 'standard' } },
  { name: 'edges: sobel', note: 'Sobel gradient magnitude (OpenCV).', s: { enhance_edges: true, edge_mode: 'sobel', char_set: 'basic' } },
  { name: 'edges: canny', note: 'Canny edge detector (OpenCV), thresholds 100/200.', s: { enhance_edges: true, edge_mode: 'canny', char_set: 'basic' } },
  { name: 'equalized', note: 'Histogram equalization spreads the grey levels.', s: { hist_equal: true } },
  { name: 'sharpened', note: 'Unsharp mask and more contrast.', s: { unsharp_mask: true, contrast: 1.5 } },
  { name: 'thresholded', note: 'Adaptive thresholding, block 11, constant 2.', s: { adaptive_thresh: true, char_set: 'basic' } },
];

export function presetQuery(p) {
  return Object.entries(p.s).map(([k, v]) => `${k}=${encodeURIComponent(v === true ? 1 : v)}`).join('&');
}
