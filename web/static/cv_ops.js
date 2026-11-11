// OpenCV operations used by image_processor.py, ported to JS from OpenCV 5.0's imgproc sources:
// equalizeHist (histogram.cpp), Sobel magnitude + normalize(NORM_MINMAX) (the "sobel" edge mode), Canny(100, 200)
// (canny.cpp) and adaptiveThreshold(GAUSSIAN_C, THRESH_BINARY) (thresh.cpp; float32 Gaussian blur via sepFilter2D).
// Images are { w, h, data: Uint8Array }.
import { gray } from './pil_ops.js';

const f = Math.fround;
// cvRound for float: round half to even (lrint), then saturate to 0..255.
function roundEven(v) { const r = Math.round(v); return (Math.abs(v % 1) === 0.5 && r % 2 !== 0) ? r - 1 : r; }
const sat8 = v => (v < 0 ? 0 : v > 255 ? 255 : v);

export function equalizeHist(im) {
  const hist = new Int32Array(256), n = im.data.length;
  for (const v of im.data) hist[v]++;
  let i = 0;
  while (i < 255 && !hist[i]) i++;
  if (hist[i] === n) return gray(im.w, im.h, new Uint8Array(n).fill(i));
  const scale = f(255 / (n - hist[i]));
  const lut = new Uint8Array(256);
  let sum = 0;
  for (lut[i++] = 0; i < 256; i++) { sum += hist[i]; lut[i] = sat8(roundEven(f(sum * scale))); }
  return gray(im.w, im.h, im.data.map(v => lut[v]));
}

// Border index helpers.
const reflect101 = (p, n) => (n === 1 ? 0 : p < 0 ? -p : p >= n ? 2 * n - 2 - p : p);
const replicate = (p, n) => (p < 0 ? 0 : p >= n ? n - 1 : p);

// 3x3 Sobel derivatives dx, dy (integers) with the given border mode.
function sobel(im, border) {
  const { w, h, data } = im, dx = new Int32Array(w * h), dy = new Int32Array(w * h);
  const at = (x, y) => data[border(y, h) * w + border(x, w)];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const a = at(x - 1, y - 1), b = at(x, y - 1), c = at(x + 1, y - 1);
      const d = at(x - 1, y), e = at(x + 1, y);
      const g = at(x - 1, y + 1), hh = at(x, y + 1), k = at(x + 1, y + 1);
      dx[y * w + x] = (c - a) + 2 * (e - d) + (k - g);
      dy[y * w + x] = (g - a) + 2 * (hh - b) + (k - c);
    }
  }
  return { dx, dy };
}

// image_processor "sobel": hypot(Sobel x, Sobel y), normalize to 0..255 (NORM_MINMAX), astype(uint8).
export function sobelEdges(im) {
  const { dx, dy } = sobel(im, reflect101);
  const mag = new Float64Array(dx.length);
  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i < mag.length; i++) {
    const m = Math.sqrt(dx[i] * dx[i] + dy[i] * dy[i]);
    mag[i] = m; if (m < lo) lo = m; if (m > hi) hi = m;
  }
  const scale = 255 * (hi - lo > 2.220446049250313e-16 ? 1 / (hi - lo) : 0), shift = 0 - lo * scale;
  return gray(im.w, im.h, Uint8Array.from(mag, m => {
    const v = m * scale + shift;
    return v <= 0 ? 0 : v >= 255 ? 255 : Math.trunc(v);
  }));
}

// cv2.Canny(img, low, high): L1 gradient, aperture 3.
export function canny(im, low = 100, high = 200) {
  const { w, h } = im, { dx, dy } = sobel(im, replicate);
  const mag = new Int32Array(w * h);
  for (let i = 0; i < mag.length; i++) mag[i] = Math.abs(dx[i]) + Math.abs(dy[i]);
  const M = (x, y) => (x < 0 || x >= w || y < 0 || y >= h ? 0 : mag[y * w + x]);
  const mw = w + 2, map = new Uint8Array(mw * (h + 2)).fill(1), stack = [];
  const TG22 = 13573;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const m = mag[y * w + x], p = (y + 1) * mw + x + 1;
      let edge = false;
      if (m > low) {
        const xs = dx[y * w + x], ys = dy[y * w + x];
        const ax = Math.abs(xs), ay = Math.abs(ys) * 32768, tg22x = ax * TG22;
        if (ay < tg22x) edge = m > M(x - 1, y) && m >= M(x + 1, y);
        else if (ay > tg22x + ax * 65536) edge = m > M(x, y - 1) && m >= M(x, y + 1);
        else { const s = (xs ^ ys) < 0 ? -1 : 1; edge = m > M(x - s, y - 1) && m > M(x + s, y + 1); }
      }
      if (!edge) { map[p] = 1; continue; }
      if (m > high) { map[p] = 2; stack.push(p); } else map[p] = 0;
    }
  }
  const nb = [-mw - 1, -mw, -mw + 1, -1, 1, mw - 1, mw, mw + 1];
  while (stack.length) {
    const p = stack.pop();
    for (const o of nb) if (map[p + o] === 0) { map[p + o] = 2; stack.push(p + o); }
  }
  const out = gray(w, h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) out.data[y * w + x] = map[(y + 1) * mw + x + 1] === 2 ? 255 : 0;
  return out;
}

// cv::getGaussianKernel(n, sigma <= 0, CV_32F).
const SMALL_KERNELS = { 3: [0.25, 0.5, 0.25], 5: [0.0625, 0.25, 0.375, 0.25, 0.0625],
  7: [0.03125, 0.109375, 0.21875, 0.28125, 0.21875, 0.109375, 0.03125],
  9: [4, 13, 30, 51, 60, 51, 30, 13, 4].map(v => v / 256) };
export function gaussianKernel(n) {
  if (SMALL_KERNELS[n]) return SMALL_KERNELS[n].map(f);
  const sigma = n * 0.15 + 0.35, scale2X = -0.125 / (sigma * sigma), n2 = (n - 1) >> 1;
  const values = []; let sum = 0;
  for (let i = 0, x = 1 - n; i < n2; i++, x += 2) { const t = Math.exp(x * x * scale2X); values.push(t); sum += t; }
  sum = sum * 2 + 1;
  const mul1 = 1 / sum, k = new Array(n);
  for (let i = 0; i < n2; i++) k[i] = k[n - 1 - i] = f(values[i] * mul1);
  k[n2] = f(mul1);
  return k;
}

// GaussianBlur on float32 with BORDER_REPLICATE (separable: row pass, then symmetric column pass, fused muladds).
function gaussianBlurF32(src, w, h, n) {
  const k = gaussianKernel(n), r = n >> 1, tmp = new Float32Array(w * h), out = new Float32Array(w * h);
  const fma = (a, b, c) => f(a * b + c);
  // GaussianBlur drops the kernel along a dimension of size 1.
  if (w === 1) tmp.set(src);
  else for (let y = 0; y < h; y++) {
    const row = y * w;
    for (let x = 0; x < w; x++) {
      const S = j => src[row + replicate(x + j, w)];
      let s;
      if (n <= 5) { s = f(S(0) * k[r]); for (let j = 1; j <= r; j++) s = fma(f(S(-j) + S(j)), k[r + j], s); }
      else { s = f(S(-r) * k[0]); for (let j = 1; j < n; j++) s = fma(S(j - r), k[j], s); }
      tmp[row + x] = s;
    }
  }
  if (h === 1) return tmp;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const S = j => tmp[replicate(y + j, h) * w + x];
      let s = f(S(0) * k[r]);
      for (let j = 1; j <= r; j++) s = fma(f(S(j) + S(-j)), k[r + j], s);
      out[y * w + x] = s;
    }
  }
  return out;
}

// cv2.adaptiveThreshold(img, 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, blockSize, C).
export function adaptiveThreshold(im, blockSize = 11, c = 2) {
  if (blockSize % 2 === 0) blockSize += 1;
  const { w, h, data } = im;
  const mean = gaussianBlurF32(Float32Array.from(data), w, h, blockSize);
  const idelta = Math.ceil(c), out = gray(w, h);
  for (let i = 0; i < data.length; i++) {
    const m = sat8(roundEven(mean[i]));
    out.data[i] = data[i] - m > -idelta ? 255 : 0;
  }
  return out;
}
