/** Shapes of the JSON written by tools/site_data.py into public/data/. */

export interface Axis { tag: string; name: string; min: number; default: number; max: number }
export interface Instance { name: string; coords: Record<string, number>; psName?: string | null }
export interface Metrics {
  upm: number; ascender: number; descender: number; lineGap: number;
  xHeight: number | null; capHeight: number | null; italicAngle: number;
}
export interface Feature {
  tag: string; tables: string[]; name: string; label: string | null; toggle: boolean;
  /** Single characters the feature changes (first 64). */
  chars: string;
  /** Multi-character inputs (ligatures), first 48. */
  sequences: string[];
}
export interface Locl { otTag: string; lang: string; script: string }
export interface Language {
  iso: string; name: string; autonym: string; speakers: number; alphabet: string; sample?: string;
  /** languages.json only: the family it's shown in, and every family that supports it. */
  family?: string; families?: string[];
}
export interface LanguageScript { script: string; count: number; languages: Language[] }
export interface Languages { count: number; scripts: LanguageScript[]; skipped?: boolean; error?: string }
export interface ScriptCount { script: string; count: number }
export interface Block { name: string; start: number; end: number; count: number; assigned: number }
export interface Coverage { codepoints: number; scripts: ScriptCount[]; blocks: Block[] }
export interface FileGroup { count: number; bytes: number; files: { name: string; bytes: number }[] }
export interface WebFile { path: string; name: string; bytes: number; variable: boolean }
export interface ZipFile { path: string; bytes: number }
export interface Files { formats: Partial<Record<'otf' | 'ttf' | 'woff2' | 'woff' | 'variable', FileGroup>>; web: WebFile[]; zip: ZipFile | null }
export interface Counts { glyphs: number; encoded: number; features: number; languages: number; scripts: number; instances: number }

/** public/data/<id>.json */
export interface FamilyData {
  id: string; style: 'sans' | 'mono' | 'pixel'; family: string; cssFamily: string; fileStem: string; blurb: string;
  version: string; hasItalic: boolean; web: boolean; generated: string;
  metrics: Metrics; axes: Axis[]; instances: Instance[]; features: Feature[]; locl: Locl[];
  categories: { name: string; count: number }[]; glyphScripts: string[];
  languages: Languages; coverage: Coverage; files: Files; counts: Counts;
}

/** One glyph in public/data/<id>.glyphs.json (keys are short to keep CJK lists small). */
export interface Glyph {
  /** glyph name */ n: string;
  /** code point, or null when only reachable through a feature */ u: number | null;
  /** Readable Unicode names of the source character(s). */ d?: string;
  /** category */ c: string;
  /** script */ s: string;
  /** advance width (font units) */ a: number;
  /** further code points mapped to the same glyph */ alt?: number[];
  /** Source-specific metadata for further code points sharing this glyph. */
  v?: { u: number; d: string; c: string; s: string }[];
  /** text that produces an unencoded glyph */ t?: string;
  /** the feature that produces it */ f?: string;
}

export interface CatalogEntry {
  id: string; name: string; ps: string; style: 'sans' | 'mono' | 'pixel'; italic: boolean; packs: string[];
  /** site_data found fonts for it (dist or an in-progress build). */
  built: boolean;
  /** Its variable WOFF2 is published in public/fonts, so the website can render it. */
  web: boolean;
}
export interface FamilySummary {
  id: string; family: string; cssFamily: string; fileStem: string; style: string; version: string; web: boolean;
  counts: Counts; axes: Axis[]; hasItalic: boolean; scripts: ScriptCount[]; blocks: Block[]; zip: ZipFile | null;
}
/** public/data/index.json */
/** Collection-wide numbers, de-duplicated across families (tools/site_data.py totals_of). */
export interface Totals {
  families: number; characters: number; languages: number; languagesNote: string;
  scripts: string[]; staticFonts: number; variableFonts: number;
}
export interface FontIndex {
  generated: string; catalog: CatalogEntry[]; families: FamilySummary[]; zip: ZipFile | null; totals?: Totals;
}

/** What the home page's client components get at build time (no glyphs or languages). */
export interface FamilyMeta {
  id: string; name: string; ps: string; style: 'sans' | 'mono' | 'pixel'; companion: boolean; blurb: string;
  version: string; hasItalic: boolean; metrics: Metrics; axes: Axis[]; instances: Instance[];
  features: Feature[]; locl: Locl[]; counts: Counts; coverage: Coverage; files: Files;
}
