// Converter page: load your own image (read in the browser, never uploaded on the static site) or the demo image,
// set any option, and get the ASCII art live. On the local app the Python pipeline can do the conversion instead,
// with the JS port run alongside as a cross-check.
import { route, app, api, esc, isStatic } from './core.js';
import { makeConverter } from './ascii_engine.js';
import { loadBlob, loadUrl } from './image_load.js';
import { buildControls, settingsFromQuery } from './convert_controls.js';
import { renderOutput, showText } from './convert_output.js';

const DEMO = 'static/demo.png';
const loadDemo = () => loadUrl(DEMO, 'demo.png').then(img => ({ ...img, demo: true }));
const state = { image: null, convert: null, settings: null, view: { preview: false, fontSize: 10, theme: 'dark' }, engine: 'js', last: null };

route('convert', async (args, query) => {
  const info = await api('/info');
  if (!state.settings || Object.keys(query).some(k => k in info.defaults)) state.settings = settingsFromQuery(info.defaults, query);
  const local = !isStatic();
  app().innerHTML = `<p class="kicker">Converter</p><h1>Image → ASCII art</h1>
    <p class="lead">${local ? 'Pick an image or use the demo. The browser engine converts as you move the sliders; switch to the Python engine to run the repo\'s own code on this server.'
      : 'Pick an image from your device or use the demo. Your image is converted right here in the browser and is never uploaded anywhere.'}</p>
    <div class="panel src" id="drop">
      <div class="row">
        <div><label for="f-img">Your image (PNG, JPEG, GIF, WebP, BMP…)</label><input id="f-img" type="file" accept="image/*"></div>
        <div style="flex:0 0 auto"><button type="button" class="alt" id="b-demo">Use the demo image</button></div>
        ${local ? `<div style="flex:0 0 auto"><label>Engine</label><div class="seg" role="group" aria-label="Engine" id="eng">
          <button type="button" data-e="js">Browser (JS)</button><button type="button" data-e="python">Python (server)</button></div></div>` : ''}
      </div>
      <p class="small mute" id="src-note">or drop an image anywhere on this panel.</p>
    </div>
    <div class="side conv"><div class="panel ctls" id="ctls"></div><div id="outp"></div></div>`;

  renderOutput(document.getElementById('outp'), state);
  let timer = 0, seq = 0;
  const schedule = (opts = {}) => {
    if (opts.displayOnly) { if (state.last) showText(state, state.last); return; }
    clearTimeout(timer);
    timer = setTimeout(run, state.engine === 'python' ? 250 : 30);
  };

  async function run() {
    if (!state.convert) return;
    const my = ++seq, s = state.settings, opts = { preview: state.view.preview };
    try {
      const t0 = performance.now();
      const js = state.convert(s, opts);
      const tJs = performance.now() - t0;
      if (state.engine === 'python' && local) {
        const fd = new FormData();
        if (!state.image.demo) fd.append('file', state.image.blob, state.image.name);
        fd.append('settings', JSON.stringify(s)); fd.append('preview', String(opts.preview));
        const t1 = performance.now();
        const py = await api('/convert', { body: fd });
        if (my !== seq) return;
        state.last = { ...py, ms: performance.now() - t1, check: compare(js.text, py.text) };
      } else {
        state.last = { engine: 'js', text: js.text, cols: js.cols, rows: js.rows, ms: tJs };
      }
      showText(state, state.last);
    } catch (e) {
      if (my === seq) showText(state, { error: e.message });
    }
  }

  async function useImage(promise) {
    const note = document.getElementById('src-note');
    note.textContent = 'Reading the image…';
    try {
      const img = await promise;
      if (state.image && state.image.url && state.image !== img) URL.revokeObjectURL(state.image.url);
      state.image = img;
      state.convert = makeConverter(img.rgba, img.w, img.h);
      note.textContent = `${img.name}: ${img.w} × ${img.h} pixels${local ? '' : ', read in this browser only'}.`;
      run();
    } catch (e) { note.innerHTML = `<span class="err">${esc(e.message)}</span>`; }
  }

  document.getElementById('f-img').addEventListener('change', e => { const f = e.target.files[0]; if (f) useImage(loadBlob(f, f.name)); });
  document.getElementById('b-demo').addEventListener('click', () => useImage(loadDemo()));
  const drop = document.getElementById('drop');
  drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('over'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('over'));
  drop.addEventListener('drop', e => {
    e.preventDefault(); drop.classList.remove('over');
    const f = e.dataTransfer.files[0]; if (f) useImage(loadBlob(f, f.name));
  });
  const eng = document.getElementById('eng');
  if (eng) {
    const mark = () => eng.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.e === state.engine));
    eng.addEventListener('click', e => { const b = e.target.closest('button'); if (b) { state.engine = b.dataset.e; mark(); run(); } });
    mark();
  }
  buildControls(document.getElementById('ctls'), info, state.settings, state.view, schedule);

  if (state.image) { document.getElementById('src-note').textContent = `${state.image.name}: ${state.image.w} × ${state.image.h} pixels.`; run(); }
  else useImage(loadDemo());
});

// Character-by-character comparison of the JS port with the Python result.
function compare(a, b) {
  if (a === b) return { same: true };
  const x = Array.from(a), y = Array.from(b);
  const n = Math.max(x.length, y.length);
  let d = 0; for (let i = 0; i < n; i++) if (x[i] !== y[i]) d++;
  return { same: false, differ: d, total: y.length };
}
