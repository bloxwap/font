/**
 * Build-time access to the data tools/site_data.py writes into public/data/. Server-only
 * (reads the file system during `next build`), so every number on the site is the number
 * in the fonts that ship with it.
 */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { CatalogEntry, FamilyData, FamilyMeta, FontIndex } from './types';

const DATA = join(process.cwd(), 'public', 'data');
const cache = new Map<string, unknown>();

function readJson<T>(name: string): T | null {
  if (cache.has(name)) return cache.get(name) as T | null;
  const path = join(DATA, name);
  const value = existsSync(path) ? (JSON.parse(readFileSync(path, 'utf8')) as T) : null;
  cache.set(name, value);
  return value;
}

const EMPTY_INDEX: FontIndex = { generated: '', catalog: [], families: [], zip: null };

export function getIndex(): FontIndex {
  return readJson<FontIndex>('index.json') ?? EMPTY_INDEX;
}

export function getCatalog(): CatalogEntry[] { return getIndex().catalog; }

export function getCatalogEntry(id: string): CatalogEntry | undefined {
  return getCatalog().find((entry) => entry.id === id);
}

/** Full data for a family the website can render (data JSON and web fonts present), else null. */
export function getFamily(id: string): FamilyData | null {
  const entry = getCatalogEntry(id);
  if (entry && !entry.web) return null;
  const data = readJson<FamilyData>(`${id}.json`);
  return data && data.web !== false ? data : null;
}

const ORDER = ['sans', 'mono', 'pixel'];
const rank = (id: string) => (ORDER.includes(id) ? ORDER.indexOf(id) : ORDER.length);

/** Families the website can render: Sans, Mono, Pixel, then companions in catalog order. */
export function getReadyFamilies(): FamilyData[] {
  return getCatalog()
    .map((entry) => getFamily(entry.id))
    .filter((f): f is FamilyData => f !== null)
    .sort((a, b) => rank(a.id) - rank(b.id));
}

/** The trimmed shape the home page's client components receive. */
export function toMeta(data: FamilyData): FamilyMeta {
  return {
    id: data.id, name: data.cssFamily, ps: data.fileStem, style: data.style,
    companion: !['sans', 'mono', 'pixel'].includes(data.id), blurb: data.blurb, version: data.version,
    hasItalic: data.hasItalic, metrics: data.metrics, axes: data.axes, instances: data.instances,
    features: data.features.filter((f) => f.toggle), locl: data.locl, counts: data.counts,
    coverage: { ...data.coverage, blocks: data.coverage.blocks.filter((b) => b.count >= 16) },
    files: data.files,
  };
}

export function getMetas(): FamilyMeta[] { return getReadyFamilies().map(toMeta); }

/** Read a file from public/ (OFL.txt, bloxwap-font.css) at build time. */
export function readPublic(name: string): string | null {
  const path = join(process.cwd(), 'public', name);
  return existsSync(path) ? readFileSync(path, 'utf8') : null;
}

/** Headline numbers for the whole collection (de-duplicated across families by site_data.py). */
export function getTotals() {
  const t = getIndex().totals;
  return {
    families: t?.families ?? getReadyFamilies().length,
    scripts: t?.scripts ?? [],
    characters: t?.characters ?? 0,
    languages: t?.languages ?? 0,
    languagesNote: t?.languagesNote ?? '',
    staticFonts: t?.staticFonts ?? 0,
    variableFonts: t?.variableFonts ?? 0,
    version: getFamily('sans')?.version ?? '',
  };
}
