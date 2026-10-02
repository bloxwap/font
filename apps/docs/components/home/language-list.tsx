'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import NumberFlow from '@number-flow/react';
import { ArrowRight, Search } from 'lucide-react';
import { FamilyPicker } from '@/components/ui/controls';
import { toast } from '@/components/ui/toast';
import { fontStack } from '@/lib/families';
import { fmtNum } from '@/lib/format';
import { loadFamily, loadLanguages, sendToTester, useAsync } from '@/lib/client-data';
import type { FamilyMeta, Language } from '@/lib/types';
import { coverageHighlights } from '@/lib/coverage';

/** Cards on the home page: two rows on desktop. The full lists live on /docs/language-support. */
const SHOW = 10;

type Row = Language & { script: string };
const bySpeakers = (a: Row, b: Row) => (b.speakers || 0) - (a.speakers || 0) || a.name.localeCompare(b.name);

/**
 * A one-screen sample of the Hyperglot language coverage, for the whole collection (each language
 * shown in the family that covers it) or one family: search, filter by script, click to try in the
 * tester, and a link to every language in the docs.
 */
export function LanguageList({ families }: { families: FamilyMeta[] }) {
  const [familyId, setFamilyId] = useState('all');
  const all = familyId === 'all';
  const meta = families.find((f) => f.id === familyId);
  const langs = useAsync(() => (all ? loadLanguages() : loadFamily(familyId).then((d) => d?.languages ?? null)), familyId);
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [script, setScript] = useState('');
  const [pressed, setPressed] = useState<string | null>(null);
  useEffect(() => { const t = window.setTimeout(() => setDebounced(query.trim().toLowerCase()), 120); return () => window.clearTimeout(t); }, [query]);
  useEffect(() => { setScript(''); }, [familyId]);

  const byId = useMemo(() => new Map(families.map((f) => [f.id, f])), [families]);
  const familyOf = (l: Language) => byId.get(all ? l.family ?? 'sans' : familyId);
  const shortName = (f?: FamilyMeta) => f?.name.replace(/^Bloxwap /, '') ?? '';
  const highlights = meta ? coverageHighlights(meta) : [];
  // Every match, flattened across scripts.
  const rows = useMemo<Row[]>(() => (langs?.scripts ?? []).filter((s) => !script || s.script === script).flatMap((s) =>
    s.languages.filter((l) => !debounced || l.name.toLowerCase().includes(debounced) || (l.autonym || '').toLowerCase().includes(debounced) || l.iso.includes(debounced))
      .map((l) => ({ ...l, script: s.script }))), [langs, script, debounced]);
  // Unique languages (a language written in two scripts appears in both lists but counts once).
  const total = useMemo(() => new Set(rows.map((l) => l.iso)).size, [rows]);
  // The sample: unfiltered, the most-spoken language of every script first (so each script shows),
  // then the rest by speakers; filtered or searching, simply the most-spoken matches.
  const picked = useMemo<Row[]>(() => {
    const sorted = [...rows].sort(bySpeakers);
    if (debounced || script) return sorted.slice(0, SHOW);
    const out: Row[] = [];
    const seen = new Set<string>();
    const add = (l: Row) => { const k = `${l.script}:${l.iso}`; if (!seen.has(k) && out.length < SHOW) { seen.add(k); out.push(l); } };
    for (const s of langs?.scripts ?? []) { const first = rows.find((l) => l.script === s.script); if (first) add(first); }
    for (const l of sorted) add(l);
    return out.sort(bySpeakers);
  }, [rows, langs, debounced, script]);

  const name = meta?.name ?? 'This family';
  const count = langs?.count ?? 0;
  let summary = 'Coverage is computed from the font files with Hyperglot.';
  if (all && langs && count) summary = `Across its ${families.length} families, Bloxwap supports ${fmtNum(count)} languages in ${langs.scripts.length} scripts, computed from the fonts with Hyperglot (Chinese and Japanese from character coverage). Each language is shown in the family that covers it; click one to try it in the tester.`;
  else if (langs && count) summary = `${name} supports ${fmtNum(count)} languages across ${langs.scripts.length} script${langs.scripts.length === 1 ? '' : 's'}, computed from the font with Hyperglot. Click a language to try it in the tester.`;
  else if (meta && highlights.length) summary = `${name} covers ${highlights.slice(0, 3).map((h) => `${h.value} ${h.label}`).join(', ')}. Hyperglot counts a language only when every character of its orthography is present.`;

  return <>
    <header className="sec-head sec-head-row">
      <div>
        <p className="eyebrow">06 — Languages</p>
        <h2 id="lang-title"><span className="big-count">{count ? <NumberFlow value={count} locales="en-US" /> : '—'}</span> languages</h2>
        <p className="lede">{summary}</p>
      </div>
      <FamilyPicker label="Language coverage typeface" families={families} value={familyId} onChange={setFamilyId} all="All fonts" />
    </header>
    {meta?.companion && highlights.length > 0 && <div className="coverage-strip" aria-label="Character coverage">
      {highlights.map((h) => <span className="coverage-pill" key={h.label}><strong>{h.value}</strong><span>{h.label}</span></span>)}
    </div>}
    <div className="g-toolbar">
      <label className="search-field"><span className="sr-only">Search languages</span>
        <Search aria-hidden="true" />
        <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search languages or ISO codes" autoComplete="off" />
      </label>
      {langs && langs.scripts.length > 0 && <div className="chips" role="group" aria-label="Filter by script">
        <button type="button" className="chip" aria-pressed={!script} onClick={() => setScript('')}>All <small>{fmtNum(count)}</small></button>
        {langs.scripts.map((s) => <button key={s.script} type="button" className="chip" aria-pressed={script === s.script} onClick={() => setScript(s.script)}>{s.script} <small>{fmtNum(s.count)}</small></button>)}
      </div>}
    </div>
    <div className="l-list">
      {langs === undefined ? <div className="empty-state">Loading languages…</div>
        : !langs || !langs.scripts.length ? <div className="empty-state"><strong>No languages to show yet</strong>
          {!langs ? `Data for ${all ? 'the collection' : name} isn’t available yet.` : langs?.skipped ? 'Language detection was skipped for this build.' : `Hyperglot doesn’t list a complete language for ${name} yet. This list fills in automatically as coverage grows.`}</div>
          : !picked.length ? <div className="empty-state"><strong>No matches</strong>Try another name or ISO 639-3 code.</div>
            : <>
              <div className="l-grid">{picked.map((l) => {
                const key = `${l.script}:${l.iso}`;
                const fam = familyOf(l);
                const also = all && l.families && l.families.length > 1 ? ` · Supported by ${l.families.map((id) => shortName(byId.get(id))).join(', ')}` : '';
                return <button key={key} type="button" className="l-card" aria-pressed={pressed === key} title={`Try ${l.name} in ${fam?.name ?? 'the tester'}${also}`}
                  onClick={() => { setPressed(key); sendToTester({ family: fam?.id ?? familyId, text: l.sample || l.alphabet || l.name, lang: l.iso }); toast(`${l.name} loaded into the tester`); }}>
                  <span className="l-top"><span className="l-name">{l.name}</span><span className="l-iso">{l.script} · {l.iso}</span></span>
                  {l.autonym && l.autonym !== l.name && <span className="l-auto">{l.autonym}</span>}
                  <span className="l-sample" lang={l.iso} style={{ fontFamily: fontStack(fam?.name ?? 'Bloxwap Sans', fam?.style ?? 'sans') }}>{l.sample || l.alphabet}</span>
                  {all && fam && fam.id !== 'sans' && <span className="l-fam">{shortName(fam)}</span>}
                </button>;
              })}</div>
              <p className="l-foot">
                <span>Showing {fmtNum(picked.length)} of {fmtNum(total)} {debounced ? (total === 1 ? 'match' : 'matches') : 'languages'}{script ? ` in ${script}` : ''}</span>
                <Link href="/docs/language-support" className="l-all">See every language <ArrowRight aria-hidden="true" /></Link>
              </p>
            </>}
    </div>
  </>;
}
