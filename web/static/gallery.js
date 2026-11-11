// Gallery: the demo image through each character set, edge mode and effect, converted live by the JS engine.
import { route, app, api, esc } from './core.js';
import { makeConverter } from './ascii_engine.js';
import { loadUrl } from './image_load.js';
import { PRESETS, presetQuery } from './presets.js';

route('gallery', async () => {
  const info = await api('/info');
  app().innerHTML = `<p class="kicker">Gallery</p><h1>Character sets and effects</h1>
    <p class="lead">The code-generated demo image converted with each of the generator's character sets and processing
      options, 64 characters wide. Open any of them in the converter to try it on your own picture.</p>
    <div class="grid wide" id="gal">${PRESETS.map((p, i) => `<a class="card gal" href="#/convert?${presetQuery(p)}">
      <b>${esc(p.name)}</b><small>${esc(p.note)}</small><pre class="art mini" id="g-${i}" aria-label="${esc(p.name)} example"></pre></a>`).join('')}</div>`;
  const img = await loadUrl('static/demo.png', 'demo.png');
  const convert = makeConverter(img.rgba, img.w, img.h);
  PRESETS.forEach((p, i) => {
    const el = document.getElementById('g-' + i);
    if (el) el.textContent = convert({ ...structuredClone(info.defaults), width: 64, ...p.s }).text;
  });
});
