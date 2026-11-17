import { FONT_VERSION } from './font-version';
/** Reject malformed generated artifacts before they enter component state. */
export function validateData(path: string, value: unknown): unknown {
  const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
  const scalar = (v: unknown) => Number.isInteger(v) && Number(v) >= 0 && Number(v) <= 0x10ffff && !(Number(v) >= 0xd800 && Number(v) <= 0xdfff);
  if (!object(value) || value.assetVersion !== FONT_VERSION) throw new Error(`Invalid data: ${path}`);
  if (path.endsWith('.glyphs.json')) {
    if (value.id !== path.split('/').pop()?.replace('.glyphs.json', '') || !Array.isArray(value.glyphs) || !value.glyphs.every(g => object(g) && typeof g.n === 'string' && typeof g.c === 'string' && typeof g.s === 'string' && Number.isFinite(g.a) && (g.u === null || scalar(g.u)) && (g.alt === undefined || Array.isArray(g.alt) && g.alt.every(scalar)) && (g.v === undefined || Array.isArray(g.v) && g.v.every(v => object(v) && scalar(v.u))))) throw new Error(`Invalid glyph data: ${path}`);
  } else if (path.endsWith('languages.json')) {
    if (!Array.isArray(value.scripts) || !value.scripts.every(s => object(s) && typeof s.script === 'string' && Array.isArray(s.languages) && s.languages.every(l => object(l) && typeof l.iso === 'string' && typeof l.name === 'string'))) throw new Error(`Invalid languages: ${path}`);
  } else if (!path.endsWith('index.json')) {
    if (value.id !== path.split('/').pop()?.replace('.json', '') || !Array.isArray(value.axes) || !Array.isArray(value.features) || !object(value.files) || !Array.isArray(value.files.web) || !object(value.metrics) || !(Number(value.metrics.upm) > 0) || !object(value.languages)) throw new Error(`Invalid family: ${path}`);
    if (!(value.axes as unknown[]).every(a => object(a) && typeof a.tag === 'string' && Number.isFinite(a.min) && Number.isFinite(a.max) && Number.isFinite(a.default) && Number(a.min) <= Number(a.default) && Number(a.default) <= Number(a.max)) ||
        !(value.features as unknown[]).every(f => object(f) && typeof f.tag === 'string' && typeof f.name === 'string' && typeof f.chars === 'string' && Array.isArray(f.sequences) && f.sequences.every(t => typeof t === 'string')) ||
        !Array.isArray(value.instances) || !value.instances.every(i => object(i) && typeof i.name === 'string' && object(i.coords) && Object.values(i.coords).every(Number.isFinite)) ||
        !object(value.counts) || !Object.values(value.counts).every(n => Number.isFinite(n) && Number(n) >= 0) ||
        !object(value.coverage) || !Array.isArray(value.coverage.blocks) || !Array.isArray(value.coverage.scripts) ||
        !(value.files.web as unknown[]).every(w => object(w) && typeof w.path === 'string' && !w.path.startsWith('/') && !w.path.split('/').includes('..') && typeof w.name === 'string' && Number.isFinite(w.bytes))) throw new Error(`Invalid family fields: ${path}`);
    validateData('languages.json', {...value.languages, assetVersion: FONT_VERSION});
  } else if (!Array.isArray(value.catalog) || !Array.isArray(value.families)) throw new Error('Invalid index');
  return value;
}
