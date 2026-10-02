/*
 * Generated documentation blocks. Server components: they read public/data/*.json at build time
 * (lib/font-data.ts), so every number in the docs is the number in the fonts that ship with the site.
 */
import { ServerCodeBlock } from 'fumadocs-ui/components/codeblock.rsc';
import type { CSSProperties } from 'react';
import { getCatalog, getCatalogEntry, getFamily, getIndex, getMetas, getReadyFamilies, readPublic } from '@/lib/font-data';
import { fontStack, shortName } from '@/lib/families';
import { DEFAULT_ON, featureDescription, featureRank, featureSample } from '@/lib/features';
import { fmtBytes, fmtNum, hex, plural } from '@/lib/format';
import { downloadUrl, fileUrl } from '@/lib/site';
import type { FamilyData } from '@/lib/types';
import { GlyphBrowser } from '@/components/home/glyph-browser';
import { FamilySpecimenClient } from './family-specimen';

const PACK_LABEL: Record<string, string> = {
  core: 'Latin, Greek, Cyrillic and symbols', arabic: 'Arabic', hangul: 'Korean Hangul', han: 'Simplified Chinese hanzi', cjk: 'CJK punctuation and symbols',
  kana: 'Japanese kana', 'han-jp': 'Japanese kanji', hebrew: 'Hebrew', armenian: 'Armenian', georgian: 'Georgian',
};

function familyName(id: string): string {
  return getCatalogEntry(id)?.name ?? id;
}

/** The dashed "in development" note for a family whose fonts are not built yet. */
export function InDevelopment({ id }: { id: string }) {
  const data = getFamily(id);
  if (data) return null;
  const entry = getCatalogEntry(id);
  const packs = entry?.packs.map((p) => PACK_LABEL[p] ?? p).join(' + ');
  return <div className="bw-callout-wip not-prose" role="note">
    <span className="wip-badge">In development</span>
    <div>
      <strong>{familyName(id)} is being drawn.</strong>
      <p>Its fonts are not part of this release yet{packs ? ` (planned coverage: ${packs})` : ''}. This page fills in automatically from the font data once it is built.</p>
    </div>
  </div>;
}

/** A one-line placeholder for secondary blocks (the dashed note is shown once, by FamilyFacts or InDevelopment). */
function Pending({ id, what }: { id: string; what: string }) {
  return <p className="bw-pending">{what} for {familyName(id)} will appear here once its fonts are built.</p>;
}

/** Headline facts for a family. */
export function FamilyFacts({ id }: { id: string }) {
  const data = getFamily(id);
  if (!data) return <InDevelopment id={id} />;
  const rows: [string, string][] = [
    ['Version', data.version || '—'],
    ['Glyphs', fmtNum(data.counts.glyphs)],
    ['Characters', fmtNum(data.counts.encoded)],
    ['Axes', data.axes.map((a) => `${a.tag} ${a.min}–${a.max}`).join(' · ') || '—'],
    ['Styles', `${data.counts.instances}${data.hasItalic ? ' + italics' : ''}`],
    ['Features', fmtNum(data.counts.features)],
    ['Languages', data.languages.count ? fmtNum(data.languages.count) : '—'],
    ['Download', data.files.zip ? fmtBytes(data.files.zip.bytes) : '—'],
  ];
  return <dl className="bw-facts not-prose">
    {rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}
  </dl>;
}

/** A live specimen in the family's own font, with its axes as sliders. */
export function FamilySpecimen({ id, text, small }: { id: string; text?: string; small?: string }) {
  const data = getFamily(id);
  if (!data) return null;
  return <FamilySpecimenClient name={data.cssFamily} style={data.style} axes={data.axes} hasItalic={data.hasItalic}
    instances={data.instances} text={text ?? defaultText(data)} small={small} />;
}

function defaultText(data: FamilyData): string {
  const scripts = new Set(data.coverage.scripts.map((s) => s.script));
  if (scripts.has('Hangul')) return '다람쥐 헌 쳇바퀴에 타고파 · Bloxwap 2026';
  if (scripts.has('Han')) return '我能吞下玻璃而不伤身体 · Bloxwap 2026';
  if (scripts.has('Arabic')) return 'صِف خَلقَ خَودِ كَمِثلِ الشَمسِ · Bloxwap';
  if (scripts.has('Hebrew')) return 'שָׁלוֹם עוֹלָם · Bloxwap 2026';
  if (scripts.has('Armenian')) return 'Հայաստան, Երևան · Bloxwap 2026';
  if (scripts.has('Georgian')) return 'ქართული ენა · ᲥᲐᲠᲗᲣᲚᲘ · Bloxwap 2026';
  if (data.style === 'pixel') return 'BUY LOW · SELL HIGH';
  if (data.style === 'mono') return 'const ok = a !== b && c >= 0;';
  return 'Fast fox, quiet charts: 0.25 BTC at $67,421.';
}

/** Axes with their ranges, and the named instances. */
export function AxesTable({ id }: { id: string }) {
  const data = getFamily(id);
  if (!data) return <Pending id={id} what="Axes and instances" />;
  return <>
    <table>
      <thead><tr><th>Axis</th><th>Tag</th><th>Min</th><th>Default</th><th>Max</th><th>CSS</th></tr></thead>
      <tbody>{data.axes.map((a) => <tr key={a.tag}>
        <td>{a.name}</td><td><code>{a.tag}</code></td><td>{a.min}</td><td>{a.default}</td><td>{a.max}</td>
        <td><code>{a.tag === 'wght' ? `font-weight: ${a.min} … ${a.max}` : `font-variation-settings: "${a.tag}" ${a.default}`}</code></td>
      </tr>)}</tbody>
    </table>
    <p>Named instances{data.hasItalic ? ' (each also as italic)' : ''}: {data.instances.filter((i) => !/Italic/.test(i.name)).map((i, n, all) => <span key={i.name}>
      <span style={{ fontFamily: fontStack(data.cssFamily, data.style), fontWeight: i.coords.wght }}>{i.name}</span> <code>{Object.entries(i.coords).map(([k, v]) => `${k} ${v}`).join(', ')}</code>{n < all.length - 1 ? ', ' : '.'}
    </span>)}</p>
  </>;
}

/** Every user-facing OpenType feature in the font, with a before/after preview set in the font itself. */
export function FeatureTable({ id }: { id: string }) {
  const data = getFamily(id);
  if (!data) return <Pending id={id} what="The feature list" />;
  const stack = fontStack(data.cssFamily, data.style);
  const features = data.features.slice().sort((a, b) => Number(b.toggle) - Number(a.toggle) || featureRank(a.tag) - featureRank(b.tag) || a.tag.localeCompare(b.tag));
  return <table className="bw-feature-table">
    <thead><tr><th>Tag</th><th>Feature</th><th style={{ minWidth: '14rem' }}>Off / on</th></tr></thead>
    <tbody>{features.map((f) => {
      const sample = f.toggle ? featureSample(f.tag, f.chars, f.sequences) : '';
      const on = DEFAULT_ON.has(f.tag);
      const style = (enabled: boolean): CSSProperties => ({ fontFamily: stack, fontFeatureSettings: `"${f.tag}" ${enabled ? 1 : 0}`, ...(f.tag === 'pnum' || f.tag === 'tnum' ? { fontVariantNumeric: 'normal' } : {}) });
      return <tr key={f.tag}>
        <td><code>{f.tag}</code></td>
        <td><strong>{f.label ?? f.name}</strong><br /><span style={{ color: 'var(--muted-foreground)', fontSize: 14 }}>{featureDescription(f.tag, f.name, f.chars, f.label)}{on ? ' On by default.' : ''}{!f.toggle ? ' Applied automatically.' : ''}</span></td>
        <td>{sample ? <div className="bw-preview" lang={f.tag === 'locl' ? 'ro' : undefined}>
          <span>off</span><span style={style(false)}>{sample}</span>
          <span>on</span><span className="on" style={style(true)}>{sample}</span>
        </div> : <span style={{ color: 'var(--faint)' }}>—</span>}</td>
      </tr>;
    })}</tbody>
  </table>;
}

/** Encoded characters per Unicode script and block. */
export function ScriptCoverage({ id, minimum = 8 }: { id: string; minimum?: number }) {
  const data = getFamily(id);
  if (!data) return <Pending id={id} what="Coverage" />;
  const blocks = data.coverage.blocks.filter((b) => b.count >= minimum);
  return <>
    <p><strong>{fmtNum(data.coverage.codepoints)}</strong> characters: {data.coverage.scripts.map((s, i) => <span key={s.script}>{i ? ', ' : ''}{fmtNum(s.count)} {s.script === 'Common' ? 'shared (punctuation, figures, symbols)' : s.script === 'Han' ? 'Han (CJK ideographs)' : s.script}</span>)}.</p>
    <div className="bw-coverage not-prose" role="list" aria-label={`${data.cssFamily} coverage by Unicode block`}>
      {blocks.map((b) => {
        const pct = Math.min(100, (b.count / Math.max(1, b.assigned)) * 100);
        return <div className="bw-coverage-row" role="listitem" key={b.name}>
          <span title={`${hex(b.start)}–${hex(b.end)}`}>{b.name}</span>
          <span className="bw-bar" aria-hidden="true"><i style={{ width: `${pct}%` }} /></span>
          <span>{fmtNum(b.count)} / {fmtNum(b.assigned)}</span>
        </div>;
      })}
    </div>
  </>;
}

/** Highlights such as "11,172 Hangul syllables" for a family (empty when it has none). */
export function scriptHighlights(data: FamilyData): string[] {
  const out: string[] = [];
  const block = (name: string) => data.coverage.blocks.find((b) => b.name === name)?.count ?? 0;
  const script = (name: string) => data.coverage.scripts.find((s) => s.script === name)?.count ?? 0;
  if (block('Hangul Syllables')) out.push(`${fmtNum(block('Hangul Syllables'))} Hangul syllables`);
  if (script('Han')) out.push(`${fmtNum(script('Han'))} hanzi`);
  if (script('Arabic')) out.push(`${fmtNum(script('Arabic'))} Arabic characters`);
  return out;
}

/** Language support: a summary across families, or one family's full list grouped by script. */
export function LanguageSupport({ id }: { id?: string }) {
  if (!id) {
    const families = getReadyFamilies();
    return <table>
      <thead><tr><th>Family</th><th>Languages</th><th>By script</th><th>Coverage highlights</th></tr></thead>
      <tbody>{families.map((f) => <tr key={f.id}>
        <td><a href={`#${f.id}`}>{f.cssFamily}</a></td>
        <td>{f.languages.count ? fmtNum(f.languages.count) : '—'}</td>
        <td>{f.languages.scripts.map((s) => `${s.script} ${fmtNum(s.count)}`).join(' · ') || '—'}</td>
        <td>{scriptHighlights(f).join(' · ') || `${fmtNum(f.counts.encoded)} characters`}</td>
      </tr>)}</tbody>
    </table>;
  }
  const data = getFamily(id);
  if (!data) return <Pending id={id} what="Language support" />;
  const highlights = scriptHighlights(data);
  if (!data.languages.scripts.length) {
    return <p>{data.languages.skipped ? 'Language detection was skipped for this build. ' : 'Hyperglot does not list a complete language for this build yet. '}
      {highlights.length ? `Character coverage: ${highlights.join(', ')}.` : ''}</p>;
  }
  return <div className="not-prose">
    {data.languages.scripts.map((s) => <details key={s.script} className="bw-lang-script">
      <summary>{s.script} <span>{plural(s.count, 'language')}</span></summary>
      <ul className="bw-lang-list">
        {s.languages.map((l) => <li key={l.iso}>{l.name} <span>{l.iso}</span></li>)}
      </ul>
    </details>)}
  </div>;
}

/** Glyph counts per category for each family. */
export function CharacterSets() {
  const families = getReadyFamilies();
  const categories = [...new Set(families.flatMap((f) => f.categories.map((c) => c.name)))];
  return <table>
    <thead><tr><th>Category</th>{families.map((f) => <th key={f.id}>{shortName(f.cssFamily)}</th>)}</tr></thead>
    <tbody>
      {categories.map((c) => <tr key={c}><td>{c}</td>{families.map((f) => <td key={f.id}>{fmtNum(f.categories.find((x) => x.name === c)?.count ?? 0)}</td>)}</tr>)}
      <tr><td><strong>Total glyphs</strong></td>{families.map((f) => <td key={f.id}><strong>{fmtNum(f.counts.glyphs)}</strong></td>)}</tr>
      <tr><td>Encoded characters</td>{families.map((f) => <td key={f.id}>{fmtNum(f.counts.encoded)}</td>)}</tr>
    </tbody>
  </table>;
}

/** Every family defined in tools/bwfont/families.py, with its status. */
export function FamilyCatalog() {
  const index = getIndex();
  return <table>
    <thead><tr><th>Family</th><th>Style</th><th>Scripts</th><th>Status</th></tr></thead>
    <tbody>{index.catalog.map((entry) => {
      const data = getFamily(entry.id);
      return <tr key={entry.id}>
        <td style={{ fontFamily: data ? fontStack(entry.name, entry.style) : undefined }}>{entry.name}</td>
        <td>{entry.style === 'pixel' ? 'Pixel display' : entry.style === 'mono' ? 'Monospaced' : 'Proportional'}{entry.italic ? ' + italics' : ''}</td>
        <td>{entry.packs.map((p) => PACK_LABEL[p] ?? p).join(' + ')}</td>
        <td>{data ? `${fmtNum(data.counts.glyphs)} glyphs` : <span className="wip-badge">In development</span>}</td>
      </tr>;
    })}</tbody>
  </table>;
}

/** The generated stylesheet as shipped, with long unicode-range lists shortened for reading. */
export async function CombinedCss({ full }: { full?: boolean }) {
  const css = readPublic('bloxwap-font.css') ?? '/* bloxwap-font.css has not been generated yet */';
  const shown = full ? css : css.replace(/(unicode-range: )([^;]{120,});/g, (_m, k: string, v: string) => {
    const parts = v.split(', ');
    return `${k}${parts.slice(0, 4).join(', ')}, … /* ${parts.length} ranges */;`;
  });
  return <ServerCodeBlock lang="css" code={shown.trimEnd()} codeblock={{ title: 'bloxwap-font.css', className: 'bw-css-file' }} />;
}

/** A code block whose text is generated from the data (paths, versions). */
export async function GeneratedCode({ lang, code, title }: { lang: string; code: string; title?: string }) {
  return <ServerCodeBlock lang={lang} code={code} codeblock={title ? { title } : undefined} />;
}

/** @font-face rules for one family's variable fonts, with real file names. */
export async function FontFaceSnippet({ id, base = '/fonts' }: { id: string; base?: string }) {
  const data = getFamily(id);
  if (!data) return <Pending id={id} what="@font-face rules" />;
  const vf = data.files.web.filter((w) => w.variable);
  const wght = data.axes.find((a) => a.tag === 'wght');
  const rules = vf.map((w) => `@font-face {
  font-family: "${data.cssFamily}";
  src: url("${base}/${w.name}") format("woff2");
  font-weight: ${wght ? `${wght.min} ${wght.max}` : '400'};
  font-style: ${/Italic/.test(w.name) ? 'italic' : 'normal'};
  font-display: swap;
}`).join('\n');
  return <ServerCodeBlock lang="css" code={rules} />;
}

/** The OFL text, read from OFL.txt. */
export function OflText() {
  const text = readPublic('OFL.txt') ?? '';
  return <pre className="bw-ofl not-prose">{text.trim()}</pre>;
}

/** An inline number from the data, e.g. <Stat id="sans" stat="glyphs" />. */
export function Stat({ id, stat }: { id: string; stat: 'glyphs' | 'encoded' | 'languages' | 'features' | 'version' | 'zip' | 'instances' }) {
  const data = getFamily(id);
  if (!data) return <>—</>;
  if (stat === 'version') return <>{data.version}</>;
  if (stat === 'zip') return <>{fmtBytes(data.files.zip?.bytes)}</>;
  return <>{fmtNum(data.counts[stat])}</>;
}

/** Download links with real sizes. */
export function DownloadTable() {
  const index = getIndex();
  const families = getReadyFamilies();
  return <table>
    <thead><tr><th>Download</th><th>Contents</th><th>Size</th></tr></thead>
    <tbody>
      {index.zip && <tr><td><a href={downloadUrl(index.zip.path)} download>Bloxwap-Fonts.zip</a></td><td>Sans, Mono and Pixel, all formats, OFL.txt (script companions download separately)</td><td>{fmtBytes(index.zip.bytes)}</td></tr>}
      {families.map((f) => f.files.zip && <tr key={f.id}>
        <td><a href={downloadUrl(f.files.zip.path)} download>{f.files.zip.path.split('/').pop()}</a></td>
        <td>{f.cssFamily}: {Object.entries(f.files.formats).map(([fmt, g]) => `${g!.count} ${fmt === 'variable' ? 'variable' : fmt.toUpperCase()}`).join(', ')}</td>
        <td>{fmtBytes(f.files.zip.bytes)}</td>
      </tr>)}
    </tbody>
  </table>;
}

/** The web font files for one family, with sizes. */
export function WebFiles({ id }: { id: string }) {
  const data = getFamily(id);
  if (!data) return <Pending id={id} what="The web font files" />;
  return <table>
    <thead><tr><th>File</th><th>Kind</th><th>Size</th></tr></thead>
    <tbody>{data.files.web.map((w) => <tr key={w.path}>
      <td><a href={fileUrl(w.path)}><code>{w.name}</code></a></td><td>{w.variable ? 'Variable' : 'Static'}</td><td>{fmtBytes(w.bytes)}</td>
    </tr>)}</tbody>
  </table>;
}

/** The glyph browser from the home page, embedded in a docs page. */
export function GlyphBrowserEmbed({ initial = 'sans' }: { initial?: string }) {
  const metas = getMetas();
  return <div className="bw-embed not-prose"><GlyphBrowser families={metas} initial={initial} eyebrow={null} /></div>;
}

/** Number of families defined (built or not), for prose. */
export function CatalogCount() {
  return <>{getCatalog().length}</>;
}
