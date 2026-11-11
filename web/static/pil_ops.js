// Pillow image operations ported to JS, following Pillow 13's C code (libImaging) so results match the Python
// pipeline pixel for pixel: Lanczos resize (Resample.c), RGB -> L (Convert.c), ImageEnhance blends (Blend.c),
// 3x3 kernel filters (Filter.c), unsharp mask with its box-blur Gaussian (BoxBlur.c, UnsharpMask.c) and
// Floyd-Steinberg dithering to 1-bit (Convert.c tobilevel). Images are { w, h, data: Uint8Array } (one band).
// Float32 arithmetic is emulated with Math.fround; FMA selects fused multiply-add (clang's default contraction
// on arm64, which the macOS Pillow wheels use); tests/fixtures/ascii_fixture.json checks the choice.

const f = Math.fround;
export const FMA = { filter: true, blend: true };

export const gray = (w, h, data = new Uint8Array(w * h)) => ({ w, h, data });
const clamp8 = v => (v < 0 ? 0 : v > 255 ? 255 : v);

// ---- resize (Lanczos, Resample.c) ----------------------------------------------------------------------------
const PRECISION_BITS = 22;
function sinc(x) { if (x === 0) return 1; x *= Math.PI; return Math.sin(x) / x; }
const lanczos = x => (x >= -3 && x < 3 ? sinc(x) * sinc(x / 3) : 0);

function precomputeCoeffs(inSize, outSize) {
  const scale = inSize / outSize;
  const filterscale = scale < 1 ? 1 : scale;
  const support = 3 * filterscale;
  const ksize = Math.ceil(support) * 2 + 1;
  const kk = new Int32Array(outSize * ksize), bounds = new Int32Array(outSize * 2);
  const inv = 1 / filterscale, pre = new Float64Array(ksize);
  for (let xx = 0; xx < outSize; xx++) {
    const center = (xx + 0.5) * scale;
    let ww = 0;
    let xmin = Math.trunc(center - support + 0.5); if (xmin < 0) xmin = 0;
    let xmax = Math.trunc(center + support + 0.5); if (xmax > inSize) xmax = inSize;
    xmax -= xmin;
    for (let x = 0; x < xmax; x++) { const w = lanczos((x + xmin - center + 0.5) * inv); pre[x] = w; ww += w; }
    for (let x = 0; x < xmax; x++) {
      const k = ww !== 0 ? pre[x] / ww : pre[x];
      kk[xx * ksize + x] = k < 0 ? Math.trunc(-0.5 + k * (1 << PRECISION_BITS)) : Math.trunc(0.5 + k * (1 << PRECISION_BITS));
    }
    bounds[xx * 2] = xmin; bounds[xx * 2 + 1] = xmax;
  }
  return { ksize, kk, bounds };
}
const clipSS = ss => clamp8(ss >> PRECISION_BITS);

function resampleH(src, sw, rows, row0, outW, c) {
  const out = new Uint8Array(outW * rows);
  for (let y = 0; y < rows; y++) {
    const base = (y + row0) * sw;
    for (let xx = 0; xx < outW; xx++) {
      const xmin = c.bounds[xx * 2], xmax = c.bounds[xx * 2 + 1], k0 = xx * c.ksize;
      let ss = 1 << (PRECISION_BITS - 1);
      for (let x = 0; x < xmax; x++) ss += src[base + x + xmin] * c.kk[k0 + x];
      out[y * outW + xx] = clipSS(ss);
    }
  }
  return out;
}

function resampleV(src, w, outH, c, shift = 0) {
  const out = new Uint8Array(w * outH);
  for (let yy = 0; yy < outH; yy++) {
    const ymin = c.bounds[yy * 2] - shift, ymax = c.bounds[yy * 2 + 1], k0 = yy * c.ksize;
    for (let xx = 0; xx < w; xx++) {
      let ss = 1 << (PRECISION_BITS - 1);
      for (let y = 0; y < ymax; y++) ss += src[(y + ymin) * w + xx] * c.kk[k0 + y];
      out[yy * w + xx] = clipSS(ss);
    }
  }
  return out;
}

// Resize one band (Image.resize(size, Image.LANCZOS) applies this to every band independently).
export function resizeBand(src, inW, inH, outW, outH) {
  const needH = outW !== inW, needV = outH !== inH;
  if (!needH && !needV) return Uint8Array.from(src);
  const horizontalFirst = !((inH - outH) > 0 && (inH - outH) > (inW - outW) * 2);
  const cv = (needH && horizontalFirst) || needV ? precomputeCoeffs(inH, outH) : null;
  const ch = needH ? precomputeCoeffs(inW, outW) : null;
  if (horizontalFirst) {
    let first = 0, last = inH;
    if (needH) { first = cv.bounds[0]; last = cv.bounds[outH * 2 - 2] + cv.bounds[outH * 2 - 1]; }
    let img = src, w = inW;
    if (needH) { img = resampleH(src, inW, last - first, first, outW, ch); w = outW; }
    return needV ? resampleV(img, w, outH, cv, needH ? first : 0) : img;
  }
  let img = src;
  if (needV) img = resampleV(src, inW, outH, cv);
  return needH ? resampleH(img, inW, outH, 0, outW, ch) : img;
}

// RGBA (canvas ImageData layout) -> L, resized first per band like Pillow (resize the RGB image, then convert).
export function resizeRGBAtoL(rgba, inW, inH, outW, outH) {
  const n = inW * inH, bands = [new Uint8Array(n), new Uint8Array(n), new Uint8Array(n)];
  for (let i = 0; i < n; i++) { bands[0][i] = rgba[i * 4]; bands[1][i] = rgba[i * 4 + 1]; bands[2][i] = rgba[i * 4 + 2]; }
  const [r, g, b] = bands.map(band => resizeBand(band, inW, inH, outW, outH));
  const out = gray(outW, outH);
  for (let i = 0; i < outW * outH; i++) out.data[i] = (r[i] * 19595 + g[i] * 38470 + b[i] * 7471 + 0x8000) >>> 16;
  return out;
}

// ---- ImageEnhance (Blend.c) -------------------------------------------------------------------------------------
export function blend(im1, im2, factor) {
  const alpha = f(factor);
  if (alpha === 0) return gray(im1.w, im1.h, Uint8Array.from(im1.data));
  if (alpha === 1) return gray(im2.w, im2.h, Uint8Array.from(im2.data));
  const out = gray(im1.w, im1.h), a = im1.data, b = im2.data, o = out.data;
  const interp = alpha >= 0 && alpha <= 1;
  for (let i = 0; i < o.length; i++) {
    const d = b[i] - a[i];
    const t = FMA.blend ? f(alpha * d + a[i]) : f(a[i] + f(alpha * d));
    o[i] = interp ? Math.trunc(t) : (t <= 0 ? 0 : t >= 255 ? 255 : Math.trunc(t));
  }
  return out;
}

export function contrast(im, factor) {
  const hist = new Float64Array(256);
  for (const v of im.data) hist[v]++;
  let sum = 0; for (let j = 0; j < 256; j++) sum += j * hist[j];
  const mean = Math.trunc(sum / im.data.length + 0.5);
  return blend(gray(im.w, im.h, new Uint8Array(im.data.length).fill(mean)), im, factor);
}
export const brightness = (im, factor) => blend(gray(im.w, im.h), im, factor);
export const sharpness = (im, factor) => blend(filter3x3(im, [1, 1, 1, 1, 5, 1, 1, 1, 1], 13), im, factor);

// ---- 3x3 kernel filters (Filter.c ImagingFilter3x3) -------------------------------------------------------------
export function filter3x3(im, kernel, scale = 1, offset = 0) {
  const { w, h, data } = im;
  if (w < 3 || h < 3) return gray(w, h, Uint8Array.from(data));
  const k = kernel.map(v => f(f(v) / f(scale))), off = f(f(offset) + 0.5);
  const out = gray(w, h, Uint8Array.from(data)), o = out.data;
  const row = (r, x, k0, k1, k2) => {
    const a = data[r + x - 1], b = data[r + x], c = data[r + x + 1];
    if (FMA.filter) return f(c * k2 + f(b * k1 + f(a * k0)));
    return f(f(f(a * k0) + f(b * k1)) + f(c * k2));
  };
  for (let y = 1; y < h - 1; y++) {
    const rm = (y - 1) * w, r0 = y * w, rp = (y + 1) * w;
    for (let x = 1; x < w - 1; x++) {
      let ss = off;
      ss = f(ss + row(rp, x, k[0], k[1], k[2]));
      ss = f(ss + row(r0, x, k[3], k[4], k[5]));
      ss = f(ss + row(rm, x, k[6], k[7], k[8]));
      o[r0 + x] = Math.trunc(ss < 0 ? 0 : ss > 255 ? 255 : ss);
    }
  }
  return out;
}
export const findEdges = im => filter3x3(im, [-1, -1, -1, -1, 8, -1, -1, -1, -1], 1);

// ---- Gaussian blur as three box blurs (BoxBlur.c) and unsharp mask (UnsharpMask.c) ----------------------------
export function gaussianBlurRadius(radius, passes = 3) {
  const r = f(radius);
  const sigma2 = f(f(r * r) / passes);
  const L = f(Math.sqrt(12.0 * sigma2 + 1.0));
  const l = f(Math.floor((L - 1.0) / 2.0));
  let a = f(f(2 * l + 1) * f(f(l * f(l + 1)) - f(3 * sigma2)));
  a = f(a / f(6 * f(sigma2 - f(f(l + 1) * f(l + 1)))));
  return f(l + a);
}

function boxBlurLine(out, inp, lastx, radius, edgeA, edgeB, ww, fw) {
  let acc = inp[0] * (radius + 1), x;
  for (x = 0; x < edgeA - 1; x++) acc += inp[x];
  acc += inp[lastx] * (radius - edgeA + 1);
  const save = (x, l, r) => { const bulk = acc * ww + (inp[l] + inp[r]) * fw; out[x] = Math.floor((bulk + 8388608) / 16777216) & 255; };
  if (edgeA <= edgeB) {
    for (x = 0; x < edgeA; x++) { acc += inp[x + radius] - inp[0]; save(x, 0, x + radius + 1); }
    for (x = edgeA; x < edgeB; x++) { acc += inp[x + radius] - inp[x - radius - 1]; save(x, x - radius - 1, x + radius + 1); }
    for (x = edgeB; x <= lastx; x++) { acc += inp[lastx] - inp[x - radius - 1]; save(x, x - radius - 1, lastx); }
  } else {
    for (x = 0; x < edgeB; x++) { acc += inp[x + radius] - inp[0]; save(x, 0, x + radius + 1); }
    for (x = edgeB; x < edgeA; x++) { acc += inp[lastx] - inp[0]; save(x, 0, lastx); }
    for (x = edgeA; x <= lastx; x++) { acc += inp[lastx] - inp[x - radius - 1]; save(x, x - radius - 1, lastx); }
  }
}

function horizontalBoxBlur(data, w, h, floatRadius) {
  const radius = Math.trunc(floatRadius);
  const ww = Math.trunc(f(16777216 / f(floatRadius * 2 + 1)));
  const fw = Math.floor((16777216 - (radius * 2 + 1) * ww) / 2);
  const edgeA = Math.min(radius + 1, w), edgeB = Math.max(w - radius - 1, 0);
  const line = new Uint8Array(w);
  for (let y = 0; y < h; y++) {
    const row = data.subarray(y * w, y * w + w);
    boxBlurLine(line, row, w - 1, radius, edgeA, edgeB, ww, fw);
    row.set(line);
  }
}

function transpose(data, w, h) {
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) out[x * h + y] = data[y * w + x];
  return out;
}

export function gaussianBlur(im, radius, passes = 3) {
  const r = gaussianBlurRadius(radius, passes);
  let d = Uint8Array.from(im.data);
  if (im.w === 0 || im.h === 0 || r === 0) return gray(im.w, im.h, d);
  for (let i = 0; i < passes; i++) horizontalBoxBlur(d, im.w, im.h, r);
  const t = transpose(d, im.w, im.h);
  for (let i = 0; i < passes; i++) horizontalBoxBlur(t, im.h, im.w, r);
  return gray(im.w, im.h, transpose(t, im.h, im.w));
}

export function unsharpMask(im, radius, percent, threshold = 3) {
  const blurred = gaussianBlur(im, radius), o = blurred.data, a = im.data;
  for (let i = 0; i < a.length; i++) {
    const diff = a[i] - o[i];
    o[i] = Math.abs(diff) > threshold ? clamp8(a[i] + Math.trunc(diff * percent / 100)) : a[i];
  }
  return blurred;
}

// ---- invert and Floyd-Steinberg dithering ---------------------------------------------------------------------
export const invert = im => gray(im.w, im.h, im.data.map(v => 255 - v));

export function dither(im) {
  const { w, h, data } = im, out = gray(w, h), errors = new Int32Array(w + 1);
  for (let y = 0; y < h; y++) {
    let l = 0, l0 = 0, l1 = 0, x;
    for (x = 0; x < w; x++) {
      l = clamp8(data[y * w + x] + Math.trunc((l + errors[x + 1]) / 16));
      const o = l > 128 ? 255 : 0;
      out.data[y * w + x] = o;
      l -= o;
      const l2 = l, d2 = l + l;
      l += d2; errors[x] = l + l0;
      l += d2; l0 = l + l1;
      l1 = l2; l += d2;
    }
    errors[x] = l0;
  }
  return out;
}
