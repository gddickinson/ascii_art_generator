// Node test: the JS engine reproduces the Python pipeline (ascii_pipeline.py) exactly on the cases in
// tests/fixtures/ascii_fixture.json (made by scripts/make_ascii_fixture.py). Run: node web/static/ascii_engine.test.mjs
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { CHAR_SETS, makeConverter } from './ascii_engine.js';
import { toHtml } from './ascii_export.js';

const fixture = JSON.parse(readFileSync(fileURLToPath(new URL('../../tests/fixtures/ascii_fixture.json', import.meta.url)), 'utf8'));
let failed = 0, chars = 0, wrong = 0;
const fail = msg => { failed++; console.log('FAIL ' + msg); };

if (JSON.stringify(CHAR_SETS) !== JSON.stringify(fixture.char_sets)) fail('CHAR_SETS differ from ASCIIArtGenerator.CHAR_SETS');

const hs = fixture.html_sample;
if (toHtml(hs.text, hs.font_px) !== hs.html) fail('toHtml differs from ascii_export.to_html');

const converters = fixture.images.map(im => makeConverter(new Uint8Array(Buffer.from(im.rgba, 'base64')), im.w, im.h));
for (const c of fixture.cases) {
  const got = converters[c.image](c.settings, { preview: c.preview }).text;
  chars += c.text.length;
  if (got !== c.text) {
    const a = Array.from(got), b = Array.from(c.text);
    const diff = a.length === b.length ? a.filter((ch, i) => ch !== b[i]).length : Math.max(a.length, b.length);
    wrong += diff;
    fail(`image ${c.image} ${JSON.stringify(c.case)}: ${diff} of ${b.length} characters differ`);
  }
}
console.log(`${fixture.cases.length - failed} of ${fixture.cases.length} cases identical to Python (${chars - wrong} of ${chars} characters)`);
process.exit(failed ? 1 : 0);
