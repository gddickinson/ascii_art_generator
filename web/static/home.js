// Home page: hero with the demo image as live ASCII art, real counts, and links to the pages.
import { route, app, api, esc, isStatic, onLeave } from './core.js';
import { makeConverter } from './ascii_engine.js';
import { loadUrl } from './image_load.js';

route('home', async () => {
  const info = await api('/info');
  const sets = Object.keys(info.char_sets);
  app().innerHTML = `<section class="hero"><p class="kicker">Pictures made of characters</p>
    <h1 class="glow">ASCII Art Generator</h1>
    <p class="lead">${esc(info.description)} This site runs the same conversion in your browser: pick a photo,
      choose a character set, tune contrast, sharpness, edges or dithering, and copy or download the result.
      ${isStatic() ? 'Your image never leaves your device.' : ''}</p>
    <a class="btn" href="#/convert">Convert an image</a><a class="btn alt" href="#/gallery">See the styles</a></section>
    <div class="panel hero-art"><pre class="art" id="h-art" aria-label="The demo image as ASCII art"></pre>
      <p class="small mute" id="h-cap"></p></div>
    <div class="tiles">
      <div class="tile"><b>${sets.length}</b><span>character sets (+ your own)</span></div>
      <div class="tile"><b>${Object.keys(info.defaults).length}</b><span>conversion options</span></div>
      <div class="tile"><b>${info.edge_modes.length}</b><span>edge detectors</span></div>
      <div class="tile"><b>${info.js_test_cases}</b><span>test conversions where the JS port matches Python exactly</span></div></div>
    <div class="grid">
      <a class="card" href="#/convert"><b>Converter</b><span>Your image or the demo, every option of the desktop app, live preview, copy and download as text, HTML or PNG.</span></a>
      <a class="card" href="#/gallery"><b>Gallery</b><span>The demo picture in each character set, edge mode and effect.</span></a>
      <a class="card" href="#/about"><b>About</b><span>How the conversion works, the command line and desktop app, and this web version.</span></a>
    </div>`;
  const img = await loadUrl('static/demo.png', 'demo.png');
  const convert = makeConverter(img.rgba, img.w, img.h);
  const art = document.getElementById('h-art'), cap = document.getElementById('h-cap');
  let i = 0;
  const show = () => {
    if (!document.body.contains(art)) return;
    const set = sets[i % sets.length];
    art.textContent = convert({ ...structuredClone(info.defaults), width: 84, char_set: set }).text;
    cap.textContent = `The demo image (drawn by scripts/make_demo_image.py), character set "${set}", converted in your browser.`;
    i++;
  };
  show();
  if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const id = setInterval(show, 3000);
    onLeave(() => clearInterval(id));
  }
});
