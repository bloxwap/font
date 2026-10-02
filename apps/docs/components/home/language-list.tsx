'use client';

import { useEffect, useMemo, useState } from 'react';
import NumberFlow from '@number-flow/react';
import { Search } from 'lucide-react';
import { FamilyPicker } from '@/components/ui/controls';
import { toast } from '@/components/ui/toast';
import { fontStack } from '@/lib/families';
import { fmtNum } from '@/lib/format';
import { loadFamily, loadLanguages, sendToTester, useAsync } from '@/lib/client-data';
import type { FamilyMeta, Language } from '@/lib/types';
import { coverageHighlights } from '@/lib/coverage';

const LIMIT = 48;

/**
 * Hyperglot language coverage for the whole collection (each language shown in the family that
 * covers it) or for one family: search, filter by script, click to try in the tester.
 */
export function LanguageList({ families }: { families: FamilyMeta[] }) {
  const [familyId, setFamilyId] = useState('all');
  const all = familyId === 'all';
  const meta = families.find((f) => f.id === familyId);
  const langs = useAsync(() => (all ? loadLanguages() : loadFamily(familyId).then((d) => d?.languages ?? null)), familyId);
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [script, setScript] = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [pressed, setPressed] = useState<string | null>(null);
  useEffect(() => { const t = window.setTimeout(() => setDebounced(query.trim().toLowerCase()), 120); return () => window.clearTimeout(t); }, [query]);
  useEffect(() => { setScript(''); setExpanded(new Set()); }, [familyId]);

  const byId = useMemo(() => new Map(families.map((f) => [f.id, f])), [families]);
  const familyOf = (l: Language) => byId.get(all ? l.family ?? 'sans' : familyId);
  const shortName = (f?: FamilyMeta) => f?.name.replace(/^Bloxwap /, '') ?? '';
  const highlights = meta ? coverageHighlights(meta) : [];
  const groups = useMemo(() => (langs?.scripts ?? []).filter((s) => !script || s.script === script).map((s) => ({
    script: s.script,
    rows: s.languages.filter((l) => !debounced || l.name.toLowerCase().includes(debounced) || (l.autonym || '').toLowerCase().includes(debounced) || l.iso.includes(debounced)),
  })).filter((g) => g.rows.length), [langs, script, debounced]);

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
          : !groups.length ? <div className="empty-state"><strong>No matches</strong>Try another name or ISO 639-3 code.</div>
            : groups.map((g) => {
              const show = debounced || expanded.has(g.script) ? g.rows : g.rows.slice(0, LIMIT);
              return <section className="l-script" key={g.script} aria-label={g.script}>
                <h3>{g.script} <small>{fmtNum(g.rows.length)}</small></h3>
                <div className="l-grid">{show.map((l) => {
                  const key = `${g.script}:${l.iso}`;
                  const fam = familyOf(l);
                  const also = all && l.families && l.families.length > 1 ? ` · Supported by ${l.families.map((id) => shortName(byId.get(id))).join(', ')}` : '';
                  return <button key={l.iso} type="button" className="l-card" aria-pressed={pressed === key} title={`Try ${l.name} in ${fam?.name ?? 'the tester'}${also}`}
                    onClick={() => { setPressed(key); sendToTester({ family: fam?.id ?? familyId, text: l.sample || l.alphabet || l.name, lang: l.iso }); toast(`${l.name} loaded into the tester`); }}>
                    <span className="l-top"><span className="l-name">{l.name}</span><span className="l-iso">{l.iso}</span></span>
                    {l.autonym && l.autonym !== l.name && <span className="l-auto">{l.autonym}</span>}
                    <span className="l-sample" lang={l.iso} style={{ fontFamily: fontStack(fam?.name ?? 'Bloxwap Sans', fam?.style ?? 'sans') }}>{l.sample || l.alphabet}</span>
                    {all && fam && fam.id !== 'sans' && <span className="l-fam">{shortName(fam)}</span>}
                  </button>;
                })}</div>
                {g.rows.length > show.length && <button type="button" className="btn btn--secondary btn--sm l-more"
                  onClick={() => setExpanded((e) => new Set(e).add(g.script))}>Show all {fmtNum(g.rows.length)} {g.script} languages</button>}
              </section>;
            })}
    </div>
  </>;
}
