'use client';

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { AlignCenter, AlignLeft, AlignRight } from 'lucide-react';
import { FamilyPicker, Range, Segmented, Switch } from '@/components/ui/controls';
import { CopyTextButton } from '@/components/ui/copy-text-button';
import { toast } from '@/components/ui/toast';
import { fontStack, instanceName, weightLadder } from '@/lib/families';
import { DEFAULT_ON, featureRank } from '@/lib/features';
import { loadGlyphs, TESTER_EVENT, type TesterRequest } from '@/lib/client-data';
import type { FamilyMeta, Feature } from '@/lib/types';
import { plainPaste } from './pixel-specimen';

const SAMPLES: Record<string, string> = {
  pangram: 'Fast fox, quiet charts: 0.25 BTC at $67,421.',
  paragraph: 'Bloxwap Sans is a rounded neo-grotesk drawn for screens that never stop moving. Smooth, round curves, open apertures and a tall x-height keep small text crisp, while nine weights and true italics give interfaces a clear hierarchy — from a 10 px timestamp to a 200 px headline.',
  numbers: '$67,421.08  +1.94%\nETH 3,512.44  −0.62%\n1/2 · 3/4 · x² · H₂O · 1st 2nd · 0O',
  code: 'const ok = a !== b && c >= 0 || d <= 1;\nlist.map((x) => x ?? 0) // -> [] :: |> <=>',
};
/** Samples for companion scripts, chosen by the family's coverage. */
const SCRIPT_SAMPLES: Record<string, string> = {
  Hangul: '다람쥐 헌 쳇바퀴에 타고파. 비트코인 67,421달러.',
  Han: '我能吞下玻璃而不伤身体。比特币 67,421 美元。',
  Arabic: 'صِف خَلقَ خَودِ كَمِثلِ الشَمسِ إِذ بَزَغَت — ٦٧٬٤٢١',
  Hebrew: 'שָׁלוֹם עוֹלָם — בְּלוֹקְסְוַאפ 2026',
  Armenian: 'Հայաստան, Երևան — Bloxwap 2026',
  Georgian: 'ქართული ენა — ᲥᲐᲠᲗᲣᲚᲘ — Bloxwap 2026',
};
const FALLBACK_FEATURES = ['liga', 'calt', 'dlig', 'tnum', 'pnum', 'zero', 'case', 'frac', 'sups', 'subs', 'ordn', 'smcp', 'c2sc', 'ss01', 'ss02'];
const WATERFALL = [12, 14, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128];
type View = 'text' | 'waterfall' | 'weights';
type Align = 'left' | 'center' | 'right';

function scriptSample(meta: FamilyMeta | undefined): string | null {
  if (!meta?.companion) return null;
  const script = meta.coverage.scripts.find((s) => SCRIPT_SAMPLES[s.script]);
  return script ? SCRIPT_SAMPLES[script.script]! : null;
}

function initialFeatures(list: Feature[]): Record<string, boolean> {
  return Object.fromEntries(list.map((f) => [f.tag, DEFAULT_ON.has(f.tag)]));
}

/** Every axis and OpenType feature of every built family, with live CSS output. */
export function TypeTester({ families }: { families: FamilyMeta[] }) {
  const byId = useMemo(() => new Map(families.map((f) => [f.id, f])), [families]);
  const [familyId, setFamilyId] = useState(families[0]?.id ?? 'sans');
  const meta = byId.get(familyId);
  const [size, setSize] = useState(72);
  const [wght, setWght] = useState(400);
  const [rond, setRond] = useState(0);
  const [italic, setItalic] = useState(false);
  const [lh, setLh] = useState(1.15);
  const [ls, setLs] = useState(0);
  const [align, setAlign] = useState<Align>('left');
  const [sample, setSample] = useState('pangram');
  const [lang, setLang] = useState('');
  const [extraLang, setExtraLang] = useState<string | null>(null);
  const [view, setView] = useState<View>('text');
  const [text, setText] = useState(SAMPLES.pangram!);
  const [pressedWeight, setPressedWeight] = useState<number | null>(null);
  const textRef = useRef<HTMLDivElement>(null);

  const featureList = useMemo(() => {
    const list = meta?.features.length ? meta.features : FALLBACK_FEATURES.map((tag) => ({ tag, name: tag, label: null, chars: '', sequences: [], tables: [], toggle: true }));
    return list.slice().sort((a, b) => featureRank(a.tag) - featureRank(b.tag) || a.tag.localeCompare(b.tag));
  }, [meta]);
  const [features, setFeatures] = useState<Record<string, boolean>>(() => initialFeatures(featureList));
  useEffect(() => { setFeatures(initialFeatures(featureList)); }, [featureList]);

  const wa = meta?.axes.find((a) => a.tag === 'wght');
  const ra = meta?.axes.find((a) => a.tag === 'ROND');

  // Write text into the editable box only when it changes programmatically (typing stays uncontrolled).
  const replaceText = useCallback((next: string) => {
    setText(next);
    if (textRef.current) textRef.current.innerText = next;
  }, []);

  useEffect(() => { if (window.innerWidth < 600) setSize(44); }, []);

  // Clamp axes and disable italic only for families without an italic face.
  useEffect(() => {
    if (!meta) return;
    if (wa) setWght((w) => Math.min(wa.max, Math.max(wa.min, w)));
    if (ra) setRond((r) => (r < ra.min || r > ra.max ? ra.default : r));
    if (!meta.hasItalic) setItalic(false);
  }, [meta, wa, ra]);

  const applySample = useCallback(async (kind: string, id: string) => {
    setSample(kind);
    const target = byId.get(id);
    if (kind === 'charset') {
      const glyphs = await loadGlyphs(id);
      if (!glyphs) { replaceText('ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz\n0123456789 !?&@#$%'); return; }
      const groups = new Map<string, string[]>();
      for (const g of glyphs) {
        if (g.u == null || g.c === 'Marks' || g.c === 'Spaces & controls') continue;
        const list = groups.get(g.c) ?? [];
        if (list.length < 400) list.push(String.fromCodePoint(g.u));
        groups.set(g.c, list);
      }
      replaceText([...groups.values()].map((chars) => chars.join('')).join('\n'));
      return;
    }
    if (kind === 'script') { replaceText(scriptSample(target) ?? SAMPLES.pangram!); return; }
    replaceText(SAMPLES[kind] ?? SAMPLES.pangram!);
  }, [byId, replaceText]);

  const chooseFamily = useCallback((id: string) => {
    setFamilyId(id);
    const target = byId.get(id);
    if (sample === 'charset') void applySample('charset', id);
    else if (target?.companion && scriptSample(target)) void applySample('script', id);
    else if (sample === 'script') void applySample('pangram', id);
  }, [byId, sample, applySample]);

  // Requests from the glyph browser and language list (same page), or ?family=&text=&lang= links.
  const handleRequest = useCallback((request: TesterRequest, scroll: boolean) => {
    if (request.family && byId.has(request.family)) setFamilyId(request.family);
    if (request.lang !== undefined) { setLang(request.lang); setExtraLang(request.lang || null); }
    if (request.text) { setSample('custom'); replaceText(request.text); }
    setView('text');
    if (request.feature) {
      const tag = request.feature;
      window.setTimeout(() => setFeatures((f) => (tag in f ? { ...f, [tag]: true } : f)), 60);
    }
    if (scroll) document.getElementById('tester')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  }, [byId, replaceText]);

  useEffect(() => {
    const onRequest = (event: Event) => handleRequest((event as CustomEvent<TesterRequest>).detail, true);
    window.addEventListener(TESTER_EVENT, onRequest);
    const params = new URLSearchParams(window.location.search);
    if (params.get('text') || params.get('family')) {
      handleRequest({ family: params.get('family') ?? undefined, text: params.get('text') ?? undefined, lang: params.get('lang') ?? undefined, feature: params.get('feature') ?? undefined }, false);
    }
    return () => window.removeEventListener(TESTER_EVENT, onRequest);
  }, [handleRequest]);

  function toggleFeature(tag: string) {
    setFeatures((current) => {
      const next = { ...current, [tag]: !current[tag] };
      // tnum and pnum are mutually exclusive
      if (next[tag] && (tag === 'tnum' || tag === 'pnum')) {
        const other = tag === 'tnum' ? 'pnum' : 'tnum';
        if (other in next) next[other] = false;
      }
      return next;
    });
  }

  function reset() {
    setSize(window.innerWidth < 600 ? 44 : 72); setWght(400); setRond(ra?.default ?? 0); setItalic(false);
    setLh(1.15); setLs(0); setAlign('left'); setLang(''); setExtraLang(null); setFeatures(initialFeatures(featureList));
  }

  const featureCss = Object.entries(features).filter(([tag, on]) => on !== DEFAULT_ON.has(tag)).map(([tag, on]) => `"${tag}" ${on ? 1 : 0}`).join(', ');
  const name = meta?.name ?? 'Bloxwap Sans';
  const style = meta?.style ?? 'sans';
  const base: CSSProperties = {
    fontFamily: fontStack(name, style), fontStyle: italic ? 'italic' : 'normal',
    fontVariationSettings: ra ? `"ROND" ${rond}` : 'normal', fontFeatureSettings: featureCss || 'normal',
    letterSpacing: `${ls}em`, textAlign: align,
  };
  const textStyle: CSSProperties = { ...base, fontWeight: wght, fontSize: size, lineHeight: lh };
  const firstLine = (text.split('\n')[0] || SAMPLES.pangram)!;
  const dir = 'auto';

  const displayNames = useMemo(() => { try { return new Intl.DisplayNames(['en'], { type: 'language' }); } catch { return null; } }, []);
  const langOptions = useMemo(() => {
    const seen = new Set<string>();
    const out: { value: string; label: string }[] = [];
    for (const l of [...(meta?.locl ?? []), ...(extraLang ? [{ lang: extraLang }] : [])]) {
      if (seen.has(l.lang)) continue;
      seen.add(l.lang);
      let label = l.lang;
      try { label = displayNames?.of(l.lang) ?? l.lang; } catch { /* not a BCP 47 code */ }
      out.push({ value: l.lang, label: `${label} (${l.lang})` });
    }
    return out;
  }, [meta, extraLang, displayNames]);

  const cssLines: [string, string][] = [
    ['font-family', `"${name}"`], ['font-size', `${size}px`], ['font-weight', String(wght)],
    ...(italic ? [['font-style', 'italic'] as [string, string]] : []),
    ...(ra ? [['font-variation-settings', `"ROND" ${rond}`] as [string, string]] : []),
    ['line-height', lh.toFixed(2)],
    ...(ls !== 0 ? [['letter-spacing', `${ls}em`] as [string, string]] : []),
    ...(featureCss ? [['font-feature-settings', featureCss] as [string, string]] : []),
  ];
  const cssText = cssLines.map(([k, v]) => `${k}: ${v};`).join('\n');
  const ladder = weightLadder(meta?.instances).filter((i) => !/Italic/.test(i.name));
  const hasData = !!meta?.features.length;

  return <div className="tester">
    <aside className="t-panel" aria-label="Tester controls">
      <div className="t-group">
        <FamilyPicker label="Tester typeface" families={families} value={familyId} onChange={chooseFamily} />
      </div>
      <div className="t-group">
        <Range label="Size" min={10} max={220} value={size} onChange={setSize} suffix="px" />
        <Range label="Weight" min={wa?.min ?? 100} max={wa?.max ?? 900} value={wght} onChange={setWght}
          note={instanceName(meta?.instances, wght)} />
        {ra && <Range label={<>Roundness <code>ROND</code></>} min={ra.min} max={ra.max} value={rond} onChange={setRond} />}
        <Range label="Line height" min={0.8} max={2} step={0.01} value={lh} onChange={setLh} format={{ minimumFractionDigits: 2, maximumFractionDigits: 2 }} />
        <Range label="Tracking" min={-0.1} max={0.25} step={0.005} value={ls} onChange={setLs}
          format={{ maximumFractionDigits: 3 }} suffix="em" />
      </div>
      <div className="t-group t-inline">
        <Switch label="Italic" checked={italic} onChange={setItalic} disabled={!meta?.hasItalic} title={meta?.hasItalic ? undefined : `${name} has no italics`} />
        <Segmented label="Alignment" small value={align} onChange={setAlign} options={[
          { value: 'left', label: <AlignLeft aria-hidden="true" />, ariaLabel: 'Align left' },
          { value: 'center', label: <AlignCenter aria-hidden="true" />, ariaLabel: 'Align center' },
          { value: 'right', label: <AlignRight aria-hidden="true" />, ariaLabel: 'Align right' },
        ]} />
      </div>
      <div className="t-group">
        <label className="ctl"><span className="ctl-row"><span>Sample</span></span>
          <select value={sample} onChange={(e) => void applySample(e.target.value, familyId)}>
            <option value="pangram">Pangram</option>
            <option value="paragraph">Paragraph</option>
            <option value="numbers">Numbers &amp; prices</option>
            <option value="code">Code</option>
            {scriptSample(meta) && <option value="script">Native script</option>}
            <option value="charset">Character set</option>
            {sample === 'custom' && <option value="custom">Custom</option>}
          </select>
        </label>
        <label className="ctl"><span className="ctl-row"><span>Language <code>locl</code></span></span>
          <select value={lang} onChange={(e) => setLang(e.target.value)} disabled={!langOptions.length && !lang}
            title={langOptions.length ? undefined : 'No localized forms in this family'}>
            <option value="">Default (en)</option>
            {langOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </label>
      </div>
      <div className="t-group">
        <div className="ctl-row"><span>OpenType features</span><button type="button" className="link-btn" onClick={reset}>Reset</button></div>
        <div className="features" role="group" aria-label="OpenType features">
          {featureList.map((f) => {
            const label = f.label || (f.name !== f.tag ? f.name : '');
            const affects = [f.chars, ...f.sequences].filter(Boolean).join(' ');
            return <button key={f.tag} type="button" className="feat" aria-pressed={!!features[f.tag]}
              title={`${f.tag} — ${label || f.name}${affects ? `\nAffects: ${affects}` : ''}`} onClick={() => toggleFeature(f.tag)}>
              <code>{f.tag}</code><span>{label}</span>
            </button>;
          })}
        </div>
        <p className="t-hint">{hasData ? 'Generated from the font’s GSUB/GPOS tables. Hover a feature to see the characters it affects.' : 'Font data not available — showing standard features.'}</p>
      </div>
    </aside>

    <div className="t-main">
      <Segmented label="Tester view" role="tab" small className="t-views" value={view} onChange={setView}
        controls={(v) => `t-view-${v}`}
        options={[{ value: 'text', label: 'Text' }, { value: 'waterfall', label: 'Waterfall' }, { value: 'weights', label: 'Weights' }]} />
      <div className="t-view" id="t-view-text" role="tabpanel" hidden={view !== 'text'}>
        <div ref={textRef} className="t-text" style={textStyle} lang={lang || undefined} dir={dir} contentEditable suppressContentEditableWarning
          spellCheck={false} role="textbox" aria-multiline="true" aria-label="Type tester text, editable"
          onInput={(e) => setText((e.target as HTMLDivElement).innerText.replace(/\n+$/, ''))} onPaste={plainPaste}>{SAMPLES.pangram}</div>
      </div>
      <div className="t-view" id="t-view-waterfall" role="tabpanel" hidden={view !== 'waterfall'}>
        <div className="waterfall">{view === 'waterfall' && WATERFALL.map((s) => <div className="wf-row" key={s}>
          <span className="mono-label">{s}px</span>
          <div className="wf-text" lang={lang || undefined} dir={dir} style={{ ...base, fontWeight: wght, fontSize: s }}>{firstLine}</div>
        </div>)}</div>
      </div>
      <div className="t-view" id="t-view-weights" role="tabpanel" hidden={view !== 'weights'}>
        <div className="ladder">{view === 'weights' && ladder.map((i) => <button type="button" className="ld-row" key={i.weight}
          aria-pressed={pressedWeight === i.weight} title={`Set weight to ${i.weight}`}
          onClick={() => { setWght(i.weight); setPressedWeight(i.weight); toast(`Weight set to ${i.weight}`); }}>
          <span className="mono-label">{i.weight} {i.name}</span>
          <span className="ld-text" lang={lang || undefined} dir={dir} style={{ ...base, fontWeight: i.weight }}>{firstLine}</span>
        </button>)}</div>
      </div>
      <div className="css-out">
        <pre className="css-code" aria-label="CSS for this setting">{cssLines.map(([k, v], i) => <span key={k}>{i ? '\n' : ''}<span className="k">{k}</span>: {v};</span>)}</pre>
        <CopyTextButton text={cssText} label="Copy CSS" />
      </div>
    </div>
  </div>;
}
