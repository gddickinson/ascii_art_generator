// Decode an image in the browser into RGBA pixels. Nothing is uploaded: the file is read locally.
// Like Pillow, the EXIF orientation and colour profile are not applied where the browser allows that, so the pixels
// match what the Python app reads (exactly for PNG; JPEG decoders can differ by a level here and there).
const MAX_PIXELS = 50e6;

async function bitmap(blob) {
  try {
    return await createImageBitmap(blob, { imageOrientation: 'none', colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
  } catch (e) {
    try { return await createImageBitmap(blob, { colorSpaceConversion: 'none' }); } catch (e2) { return createImageBitmap(blob); }
  }
}

export async function loadBlob(blob, name = 'image') {
  let bmp;
  try { bmp = await bitmap(blob); } catch (e) { throw new Error(`${name}: the browser cannot read this file as an image.`); }
  const w = bmp.width, h = bmp.height;
  if (w * h > MAX_PIXELS) throw new Error(`${name}: ${w} × ${h} is more than 50 megapixels; use the desktop app.`);
  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(bmp, 0, 0);
  bmp.close && bmp.close();
  return { rgba: ctx.getImageData(0, 0, w, h).data, w, h, name, blob, url: URL.createObjectURL(blob) };
}

export async function loadUrl(url, name) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return loadBlob(await r.blob(), name || url.split('/').pop());
}
