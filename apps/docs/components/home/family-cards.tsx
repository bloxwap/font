import { fontStack, shortName } from '@/lib/families';
import { fmtNum } from '@/lib/format';
import type { CatalogEntry, FamilyMeta } from '@/lib/types';
import Link from 'next/link';
import { coverageHighlights } from '@/lib/coverage';

const PRIMARY_COPY: Record<string, string> = {
  sans: 'Rounded neo-grotesk · 100–900 · italics',
  mono: 'Monospaced · code ligatures · italics',
  pixel: 'Display · weight + roundness axes',
};
const PACK_SCRIPT: Record<string, string> = {
  arabic: 'Arabic', hangul: 'Korean Hangul', han: 'Simplified Chinese',
  kana: 'Japanese', hebrew: 'Hebrew', armenian: 'Armenian', georgian: 'Georgian',
};
const PACK_SAMPLE: Record<string, string> = {
  arabic: 'ع', hangul: '한', han: '字', kana: 'あ', hebrew: 'שָׁ', armenian: 'Աա', georgian: 'ქ',
};

/** The three primary families, then every companion family (built ones live, others marked in development). */
export function FamilyCards({ families, catalog }: { families: FamilyMeta[]; catalog: CatalogEntry[] }) {
  const byId = new Map(families.map((f) => [f.id, f]));
  const companions = catalog.filter((c) => !['sans', 'mono', 'pixel'].includes(c.id));
  return <>
    <section className="families" aria-label="Families">
      {(['sans', 'mono', 'pixel'] as const).map((id) => {
        const meta = byId.get(id);
        const name = meta?.name ?? `Bloxwap ${id[0]!.toUpperCase()}${id.slice(1)}`;
        return <a key={id} className="fam-card" href={`#${id}`}>
          <span className="fam-aa" style={{ fontFamily: fontStack(name, id) }}>Aa</span>
          <span className="fam-meta"><strong>{name}</strong><span>{PRIMARY_COPY[id]}</span></span>
          <span className="fam-status">{meta ? `${fmtNum(meta.counts.glyphs)} glyphs` : 'In progress'}</span>
        </a>;
      })}
    </section>
    {companions.length > 0 && <section className="families families--companions" aria-label="Companion families">
      {companions.map((entry) => {
        const meta = byId.get(entry.id);
        const script = entry.packs.map((p) => PACK_SCRIPT[p]).filter(Boolean).join(' + ');
        const sample = entry.packs.map((p) => PACK_SAMPLE[p]).find(Boolean) ?? 'Aa';
        const highlight = meta ? coverageHighlights(meta)[0] : undefined;
        return <Link key={entry.id} className={`fam-card fam-card--small${meta ? '' : ' fam-card--wip'}`} href={`/docs/families/${entry.id.replace(/^mono-/, 'sans-')}`}>
          <span className="fam-aa" style={{ fontFamily: meta ? fontStack(entry.name, entry.style) : undefined }}>{sample}</span>
          <span className="fam-meta">
            <strong>{shortName(entry.name)}</strong>
            <span>{meta && highlight ? `${highlight.value} ${highlight.label}` : script}</span>
            <span className="fam-status">{meta ? `${fmtNum(meta.counts.glyphs)} glyphs` : <span className="wip-badge">In development</span>}</span>
          </span>
        </Link>;
      })}
    </section>}
  </>;
}
