// Settings panel for the converter: every option of ascii_pipeline (the GUI's ASCII Settings, Image Processing and
// Advanced tabs) plus display options. Labels, ranges and defaults come from /api/info.
import { esc } from './core.js';

const fmtNum = (v, step) => (step < 1 ? (+v).toFixed(step < 0.1 ? 2 : 1) : String(v));

export function buildControls(host, info, s, view, onChange) {
  const L = k => info.labels[k] || { label: k, help: '' };
  const R = info.ranges;
  const slider = (k, extra = '') => {
    const [lo, hi, step] = R[k];
    const v = s[k] ?? (k === 'height' ? 50 : lo);
    return `<div class="ctl" title="${esc(L(k).help)}"><label for="c-${k}">${esc(L(k).label)} <b id="v-${k}">${fmtNum(v, step)}</b>${extra}</label>
      <input type="range" id="c-${k}" data-k="${k}" min="${lo}" max="${hi}" step="${step}" value="${v}"></div>`;
  };
  const check = k => `<label class="chk" title="${esc(L(k).help)}"><input type="checkbox" data-k="${k}" ${s[k] ? 'checked' : ''}> ${esc(L(k).label)}</label>`;
  const sets = Object.keys(info.char_sets);
  host.innerHTML = `
    <h3>Size</h3>
    ${slider('width')}
    <label class="chk"><input type="checkbox" id="c-auto" ${s.height == null ? 'checked' : ''}> Auto height (keep aspect ratio)</label>
    ${slider('height')}
    <label class="chk" title="The GUI's Generate Preview: width at most ${info.preview_max.width}, height at most ${info.preview_max.height}">
      <input type="checkbox" id="c-preview" ${view.preview ? 'checked' : ''}> Quick preview size (as the GUI's Generate Preview)</label>
    <h3>Characters</h3>
    <label for="c-char_set">${esc(L('char_set').label)}</label>
    <select id="c-char_set" data-k="char_set">${sets.map(n => `<option ${n === s.char_set ? 'selected' : ''}>${esc(n)}</option>`).join('')}</select>
    <label for="c-custom_chars">${esc(L('custom_chars').label)} <span class="mute">(darkest → brightest pixel; editing selects "custom")</span></label>
    <input id="c-custom_chars" type="text" spellcheck="false" autocomplete="off">
    ${check('invert')}${check('dither')}
    <h3>Image processing</h3>
    ${slider('contrast')}${slider('brightness')}${slider('sharpness')}
    ${check('hist_equal')}
    ${check('enhance_edges')}
    <div class="seg" role="group" aria-label="Edge mode" id="c-edge">${info.edge_modes.map(m =>
      `<button type="button" data-mode="${m}" class="${m === s.edge_mode ? 'on' : ''}">${m}</button>`).join('')}</div>
    ${check('unsharp_mask')}
    <div class="sub" id="g-unsharp">${slider('unsharp_radius')}${slider('unsharp_amount')}</div>
    ${check('adaptive_thresh')}
    <div class="sub" id="g-thresh">${slider('thresh_block')}${slider('thresh_c')}</div>
    <h3>Display</h3>
    <div class="ctl"><label for="c-font">Preview font <b id="v-font">${view.fontSize}px</b></label>
      <input type="range" id="c-font" min="${info.font_size.min}" max="${info.font_size.max}" value="${view.fontSize}"></div>
    <label for="c-theme">Colours</label>
    <select id="c-theme"><option value="dark" ${view.theme === 'dark' ? 'selected' : ''}>light characters on black</option>
      <option value="light" ${view.theme === 'light' ? 'selected' : ''}>black characters on white (as the GUI)</option></select>
    <button type="button" class="alt" id="c-reset">Reset to defaults</button>`;

  const $ = sel => host.querySelector(sel);
  const custom = $('#c-custom_chars');
  const sync = () => {
    $('#c-height').disabled = s.height == null;
    if (s.height == null) $('#v-height').textContent = 'auto';
    custom.value = s.char_set === 'custom' ? s.custom_chars : info.char_sets[s.char_set];
    $('#c-char_set').value = s.char_set;
    $$('#c-edge button').forEach(b => { b.classList.toggle('on', b.dataset.mode === s.edge_mode); b.disabled = !s.enhance_edges; });
    $$('#g-unsharp input').forEach(i => { i.disabled = !s.unsharp_mask; });
    $$('#g-thresh input').forEach(i => { i.disabled = !s.adaptive_thresh; });
  };
  const $$ = sel => [...host.querySelectorAll(sel)];

  $$('input[type=range][data-k]').forEach(inp => inp.addEventListener('input', () => {
    const k = inp.dataset.k, step = +inp.step;
    s[k] = step < 1 ? +inp.value : Math.round(+inp.value);
    $('#v-' + k).textContent = fmtNum(s[k], step);
    onChange();
  }));
  $$('input[type=checkbox][data-k]').forEach(inp => inp.addEventListener('change', () => { s[inp.dataset.k] = inp.checked; sync(); onChange(); }));
  $('#c-auto').addEventListener('change', e => {
    s.height = e.target.checked ? null : +$('#c-height').value;
    if (!e.target.checked) $('#v-height').textContent = s.height;
    sync(); onChange();
  });
  $('#c-preview').addEventListener('change', e => { view.preview = e.target.checked; onChange(); });
  $('#c-char_set').addEventListener('change', e => { s.char_set = e.target.value; sync(); onChange(); });
  custom.addEventListener('input', () => { s.char_set = 'custom'; s.custom_chars = custom.value; $('#c-char_set').value = 'custom'; onChange(); });
  $('#c-edge').addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    s.edge_mode = b.dataset.mode; sync(); onChange();
  });
  $('#c-font').addEventListener('input', e => { view.fontSize = +e.target.value; $('#v-font').textContent = view.fontSize + 'px'; onChange({ displayOnly: true }); });
  $('#c-theme').addEventListener('change', e => { view.theme = e.target.value; onChange({ displayOnly: true }); });
  $('#c-reset').addEventListener('click', () => {
    Object.assign(s, structuredClone(info.defaults));
    buildControls(host, info, s, view, onChange); onChange();
  });
  sync();
}

// Settings from a route query such as #/convert?char_set=blocks&enhance_edges=1 (typed like the defaults).
export function settingsFromQuery(defaults, query) {
  const s = structuredClone(defaults);
  for (const [k, v] of Object.entries(query)) {
    if (!(k in defaults)) continue;
    const d = defaults[k];
    if (typeof d === 'boolean') s[k] = v === '1' || v === 'true';
    else if (typeof d === 'number' || k === 'height') s[k] = v === 'auto' || v === '' ? null : +v;
    else s[k] = v;
  }
  return s;
}
