'use client';

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from 'react';
import NumberFlow from '@number-flow/react';
import { Search } from 'lucide-react';
import { FamilyPicker, Range } from '@/components/ui/controls';
import { copyText, toast } from '@/components/ui/toast';
import { fontStack, instanceName } from '@/lib/families';
import { fmtNum, hex } from '@/lib/format';
import { loadGlyphs, sendToTester, useAsync } from '@/lib/client-data';
import type { FamilyMeta, Glyph } from '@/lib/types';

/** Cells rendered per page; CJK fonts have tens of thousands of glyphs, so the grid grows on demand. */
const PAGE = 480;

function preview(g: Glyph): string | null {
  if (g.u != null) {
    if (g.c === 'Spaces & controls') return null;
    const ch = String.fromCodePoint(g.u);
    return g.c === 'Marks' ? ` ${ch}` : ch;
  }
  if (g.t) return g.c === 'Marks' ? ` ${g.t}` : g.t;
  return null;
}

function matches(g: Glyph, q: string): boolean {
  if (!q) return true;
  const ql = q.toLowerCase();
  if ([...q].length === 1) {
    // a single character: that character, its accented forms, and alternates of it
    const ch = g.u != null ? String.fromCodePoint(g.u) : g.t ?? '';
    return ch === q || ch.normalize('NFD')[0] === q || g.n === q || g.n.startsWith(`${q}.`);
  }
  if (g.n.toLowerCase().includes(ql)) return true;
  if (g.u != null) {
    const m = ql.match(/^(?:u\+|0x|\\u)?([0-9a-f]{2,6})$/);
    if (m && parseInt(m[1]!, 16) === g.u) return true;
    if (/^\d+$/.test(q) && parseInt(q, 10) === g.u) return true;
  }
  return !!g.t && g.t === q;
}

/** Search, filter and inspect every glyph in a family, with metric guides drawn from the font's own metrics. */
export function GlyphBrowser({ families, initial = 'sans', eyebrow = '05 — Glyphs' }: { families: FamilyMeta[]; initial?: string; eyebrow?: string | null }) {
  const byId = useMemo(() => new Map(families.map((f) => [f.id, f])), [families]);
  const [familyId, setFamilyId] = useState(byId.has(initial) ? initial : families[0]?.id ?? 'sans');
  const meta = byId.get(familyId);
  const glyphs = useAsync(() => loadGlyphs(familyId), familyId);
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [category, setCategory] = useState('');
  const [script, setScript] = useState('');
  const [wght, setWght] = useState(400);
  const [limit, setLimit] = useState(PAGE);
  const [selName, setSelName] = useState<string | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => { const t = window.setTimeout(() => setDebounced(query.trim()), 120); return () => window.clearTimeout(t); }, [query]);
  useEffect(() => { setLimit(PAGE); }, [familyId, debounced, category, script]);

  const categories = useMemo(() => {
    const counts = new Map<string, number>();
    for (const g of glyphs ?? []) counts.set(g.c, (counts.get(g.c) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [glyphs]);
  const scripts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const g of glyphs ?? []) counts.set(g.s, (counts.get(g.s) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [glyphs]);
  useEffect(() => {
    if (category && !categories.some(([c]) => c === category)) setCategory('');
    if (script && !scripts.some(([s]) => s === script)) setScript('');
  }, [categories, scripts, category, script]);

  const list = useMemo(() => (glyphs ?? []).filter((g) => (!category || g.c === category) && (!script || g.s === script) && matches(g, debounced)), [glyphs, category, script, debounced]);
  const selIndex = useMemo(() => {
    const i = selName ? list.findIndex((g) => g.n === selName) : -1;
    return i >= 0 ? i : Math.max(0, list.findIndex((g) => g.u != null && /Lowercase|Uppercase|Letters|Hangul|Ideographs/.test(g.c)));
  }, [list, selName]);
  const selected = list[selIndex];
  const stack = fontStack(meta?.name ?? 'Bloxwap Sans', meta?.style ?? 'sans');
  const wa = meta?.axes.find((a) => a.tag === 'wght');
  const pixel = meta?.axes.some((a) => a.tag === 'ROND');

  // Grow the grid when its last row scrolls into view.
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const io = new IntersectionObserver(([entry]) => { if (entry!.isIntersecting) setLimit((l) => l + PAGE); }, { root: gridRef.current, rootMargin: '200px' });
    io.observe(sentinel);
    return () => io.disconnect();
  }, [list, limit]);

  const copy = useCallback(async (g: Glyph | undefined) => {
    if (!g) return;
    const text = g.u != null ? String.fromCodePoint(g.u) : g.t;
    if (!text) { toast('This glyph has no character to copy'); return; }
    toast(await copyText(text) ? `Copied “${text}” ${g.u != null ? hex(g.u) : ''}` : 'Copy failed');
  }, []);

  function select(i: number, scroll = true) {
    const g = list[i];
    if (!g) return;
    setSelName(g.n);
    if (i >= limit) setLimit(Math.ceil((i + 1) / PAGE) * PAGE);
    if (scroll) requestAnimationFrame(() => gridRef.current?.querySelector(`[data-i="${i}"]`)?.scrollIntoView({ block: 'nearest' }));
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (!list.length) return;
    const grid = gridRef.current!;
    const first = grid.querySelector<HTMLElement>('.g-cell');
    const cols = Math.max(1, Math.round(grid.clientWidth / (first?.offsetWidth || 64)));
    const step = ({ ArrowRight: 1, ArrowLeft: -1, ArrowDown: cols, ArrowUp: -cols, Home: -1e9, End: 1e9 } as Record<string, number>)[event.key];
    if (step !== undefined) { event.preventDefault(); select(Math.min(list.length - 1, Math.max(0, selIndex + step))); }
    else if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); void copy(selected); }
  }

  const empty = glyphs === undefined ? 'Loading glyphs…'
    : glyphs === null ? `Glyph data for ${meta?.name ?? 'this family'} isn’t available yet. It appears here automatically once the font is built.`
      : !list.length ? 'No glyphs match.' : null;

  return <>
    <header className="sec-head sec-head-row">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2 id={eyebrow ? 'glyphs-title' : undefined}>{meta ? <NumberFlow value={meta.counts.glyphs} locales="en-US" /> : 'All'} glyphs</h2>
      </div>
      <FamilyPicker label="Glyph browser typeface" families={families} value={familyId} onChange={(id) => { setFamilyId(id); setSelName(null); }} />
    </header>
    <div className="g-toolbar">
      <label className="search-field"><span className="sr-only">Search glyphs</span>
        <Search aria-hidden="true" />
        <input type="search" value={query} onChange={(e) => { setQuery(e.target.value); setSelName(null); }} placeholder="Search: a, Aacute, U+00E9, 233" autoComplete="off" />
      </label>
      <label className="sel"><span className="sr-only">Category</span>
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {categories.map(([c, n]) => <option key={c} value={c}>{c} ({fmtNum(n)})</option>)}
        </select>
      </label>
      <label className="sel"><span className="sr-only">Script</span>
        <select value={script} onChange={(e) => setScript(e.target.value)}>
          <option value="">All scripts</option>
          {scripts.map(([s, n]) => <option key={s} value={s}>{s} ({fmtNum(n)})</option>)}
        </select>
      </label>
    </div>
    <div className="glyphs">
      <div ref={gridRef} className="g-grid" role="listbox" aria-label={`${meta?.name ?? ''} glyphs`} tabIndex={0} onKeyDown={onKeyDown}
        aria-activedescendant={selected ? `glyph-${familyId}-${selIndex}` : undefined}
        style={{ fontFamily: stack, fontWeight: wght, fontVariationSettings: pixel ? '"ROND" 50' : undefined }}>
        {empty ? <div className="g-empty">{empty}</div> : list.slice(0, limit).map((g, i) => {
          const p = preview(g);
          const label = `${g.n}${g.u != null ? ` ${hex(g.u)}` : ''}`;
          return <button key={g.n} id={`glyph-${familyId}-${i}`} type="button" className="g-cell" role="option" tabIndex={-1}
            aria-selected={i === selIndex} data-i={i} title={label} aria-label={label}
            style={g.f ? { fontFeatureSettings: `"${g.f}" 1` } : undefined}
            onClick={() => { select(i, false); void copy(g); }}>
            {p != null ? p : <span className="gn">{g.n}</span>}
            {g.f && <i className="feat-dot" aria-hidden="true" />}
          </button>;
        })}
        {!empty && list.length > limit && <div className="g-more" ref={sentinelRef}>
          <button type="button" className="btn btn--secondary btn--sm" onClick={() => setLimit((l) => l + PAGE * 4)}>Show more ({fmtNum(list.length - limit)} left)</button>
        </div>}
      </div>
      <Inspector meta={meta} glyph={empty ? undefined : selected} wght={wght} stack={stack} pixel={!!pixel} onCopy={() => void copy(selected)}
        onTry={() => {
          if (!selected) return;
          const ch = selected.u != null ? String.fromCodePoint(selected.u) : selected.t ?? '';
          const upper = ch.toUpperCase() !== ch ? ` ${ch.toUpperCase()}` : '';
          sendToTester({ family: familyId, text: `${ch}${ch}${ch}${upper}`, feature: selected.f });
        }}
        weightControl={<Range label="Weight" min={wa?.min ?? 100} max={wa?.max ?? 900} value={wght} onChange={setWght}
          note={instanceName(meta?.instances, wght)} />} />
    </div>
  </>;
}

function Inspector({ meta, glyph, wght, stack, pixel, onCopy, onTry, weightControl }: {
  meta: FamilyMeta | undefined; glyph: Glyph | undefined; wght: number; stack: string; pixel: boolean;
  onCopy: () => void; onTry: () => void; weightControl: ReactNode;
}) {
  const glyphRef = useRef<HTMLSpanElement>(null);
  const [size, setSize] = useState(180);
  const p = glyph ? preview(glyph) : null;
  // The guides are positioned from the font's metrics at the rendered size (180px desktop, 130px narrow).
  useLayoutEffect(() => {
    const measure = () => { if (glyphRef.current) setSize(parseFloat(getComputedStyle(glyphRef.current).fontSize) || 180); };
    measure();
    window.addEventListener('resize', measure, { passive: true });
    return () => window.removeEventListener('resize', measure);
  }, [p]);
  const m = meta?.metrics;
  const guides: [string, number][] = [];
  if (m && p != null) {
    if (m.capHeight != null) guides.push(['cap', m.capHeight]);
    if (m.xHeight != null) guides.push(['x-height', m.xHeight]);
    guides.push(['baseline', 0]);
    if (m.descender) guides.push(['descender', Math.max(m.descender, -0.25 * m.upm)]);
  }
  const y = (v: number) => (m ? ((m.ascender - v) / m.upm) * size : 0);
  const lineHeight = m ? (m.ascender - m.descender) / m.upm : 1.2;
  const unicode = glyph ? (glyph.u != null ? `${hex(glyph.u)}${glyph.alt ? ` +${glyph.alt.length}` : ''}` : glyph.f ? `via ${glyph.f}` : '—') : '—';
  return <aside className="g-inspect card" aria-live="polite" aria-label="Glyph details">
    <button type="button" className="gi-stage" title="Click to copy" onClick={onCopy} aria-label={glyph ? `Copy ${glyph.n}` : 'No glyph selected'}>
      <span className="gi-box">
        <span className="gi-lines" aria-hidden="true">{guides.map(([name, v]) => <span key={name} className={`gi-line${name === 'baseline' ? ' base' : ''}`} style={{ top: `${y(v).toFixed(1)}px` }}><span>{name}</span></span>)}</span>
        <span ref={glyphRef} className={`gi-glyph${p == null ? ' no-preview' : ''}`}
          style={{ fontFamily: p == null ? undefined : stack, fontWeight: wght, fontVariationSettings: pixel ? '"ROND" 50' : 'normal', fontFeatureSettings: glyph?.f ? `"${glyph.f}" 1` : 'normal', lineHeight: p == null ? undefined : lineHeight }}>
          {glyph ? (p ?? (glyph.c === 'Spaces & controls' ? `${glyph.n} (invisible)` : `${glyph.n}\nnot directly accessible`)) : ''}
        </span>
      </span>
    </button>
    <div className="gi-meta">
      <h3>{glyph?.n ?? '—'}</h3>
      <dl>
        <div><dt>Unicode</dt><dd>{unicode}</dd></div>
        <div><dt>Category</dt><dd>{glyph?.c ?? '—'}</dd></div>
        <div><dt>Script</dt><dd>{glyph?.s ?? '—'}</dd></div>
        <div><dt>Advance</dt><dd>{glyph ? `${glyph.a} u` : '—'}</dd></div>
      </dl>
      {weightControl}
      <div className="gi-actions">
        <button type="button" className="btn btn--secondary btn--sm" onClick={onCopy} disabled={!glyph}>Copy character</button>
        <button type="button" className="btn btn--secondary btn--sm" onClick={onTry} disabled={!glyph}>Use in tester</button>
      </div>
    </div>
  </aside>;
}
