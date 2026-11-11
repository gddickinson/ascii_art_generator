// Static-site data layer: answers api() calls without the Python server. GET paths come from the JSON exported by
// scripts/build_static.py. Conversion on the static site runs in the browser (ascii_engine.js), not through api().
import { needsServer } from './core.js';

const files = new Map();
function file(rel) {
  if (!files.has(rel)) files.set(rel, fetch('api/' + rel + '.json').then(r => { if (!r.ok) throw new Error(`${r.status} ${rel}`); return r.json(); }));
  return files.get(rel);
}

export async function staticApi(path, body) {
  const clean = path.split('?')[0].replace(/^\/+/, '');
  if (body) throw new Error(needsServer('The Python conversion').replace(/<[^>]+>/g, ''));
  return file(clean);
}
