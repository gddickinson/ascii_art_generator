// Output panel of the converter: the ASCII art, its size and engine, the JS/Python cross-check on the local app,
// and copy / download as text, HTML (the GUI's page template) or PNG.
import { esc, download } from './core.js';
import { toHtml, toPngBlob, copyText } from './ascii_export.js';

const THEMES = { dark: { fg: '#d8ffe0', bg: '#000000' }, light: { fg: '#000000', bg: '#ffffff' } };

export function renderOutput(host, state) {
  host.innerHTML = `<div class="panel outp">
      <div class="row out-head"><p class="small mute" id="o-info" aria-live="polite">Loading the demo image…</p>
        <img id="o-thumb" alt="The image being converted" hidden></div>
      <pre id="o-art" class="art" tabindex="0" aria-label="ASCII art result"></pre>
      <p class="small" id="o-check"></p>
      <div><button type="button" id="o-copy">Copy</button><button type="button" class="alt" id="o-txt">Download .txt</button><button
        type="button" class="alt" id="o-html">Download .html</button><button type="button" class="alt" id="o-png">Download .png</button></div>
      <p class="small mute">The PNG uses the colours and font size chosen under Display; the HTML page is the desktop app's template (10 px monospace).</p>
    </div>`;
  const base = () => (state.image ? state.image.name.replace(/\.[^.]+$/, '') : 'ascii') + '_ascii';
  const text = () => (state.last && state.last.text) || '';
  const say = msg => { document.getElementById('o-check').textContent = msg; };
  host.querySelector('#o-copy').onclick = async () => say((await copyText(text())) ? 'Copied to the clipboard.' : 'Copy failed: select the text and copy it by hand.');
  host.querySelector('#o-txt').onclick = () => download(base() + '.txt', text(), 'text/plain;charset=utf-8');
  host.querySelector('#o-html').onclick = () => download(base() + '.html', toHtml(text()), 'text/html;charset=utf-8');
  host.querySelector('#o-png').onclick = async () => {
    try { download(base() + '.png', await toPngBlob(text(), { fontSize: Math.max(8, state.view.fontSize), ...THEMES[state.view.theme] })); }
    catch (e) { say(e.message); }
  };
}

export function showText(state, res) {
  const art = document.getElementById('o-art');
  if (!art) return;
  const info = document.getElementById('o-info'), check = document.getElementById('o-check'), thumb = document.getElementById('o-thumb');
  if (res.error) { info.innerHTML = `<span class="err">${esc(res.error)}</span>`; return; }
  const t = THEMES[state.view.theme];
  art.textContent = res.text;
  art.style.fontSize = state.view.fontSize + 'px';
  art.style.color = t.fg; art.style.background = t.bg;
  const im = state.image;
  info.innerHTML = `<b>${res.cols} × ${res.rows}</b> characters from ${esc(im ? im.name : '')} (${im ? `${im.w} × ${im.h}` : ''} px)
    · ${res.engine === 'python' ? 'Python pipeline (server)' : 'browser engine (JS port)'} · ${res.ms.toFixed(0)} ms`;
  if (im && thumb.src !== im.url) { thumb.src = im.url; }
  thumb.hidden = !im;
  check.innerHTML = !res.check ? ''
    : res.check.same ? '<span class="ok">Cross-check:</span> the browser\'s JS port gives exactly the same text as Python here.'
      : `<span class="err">Cross-check:</span> the JS port differs from Python in ${res.check.differ} of ${res.check.total} characters
         (Python shown). ${/\.jpe?g$/i.test(im.name) ? 'JPEG decoders differ slightly between browsers and Pillow, which is the likely cause.' : ''}`;
}
