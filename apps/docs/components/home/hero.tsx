'use client';

import { useEffect, useRef, useState } from 'react';
import NumberFlow from '@number-flow/react';
import { QUICK_ROLL as ROLL } from '@/lib/number-flow';
import { ArrowDown, Download } from 'lucide-react';
import { Segmented } from '@/components/ui/controls';
import { InstallCommand } from './install-command';
import { HeroCode } from './hero-code';

const LINES = ['Bloxwap', 'Font'];
type Fam = 'sans' | 'mono' | 'pixel';
interface Axis { wght: number; rond: number | null }
/** The hero samples its average axes every READOUT_MS; NumberFlow rolls between samples. */
const READOUT_MS = 160;

/** The live axis readout, its own component so the hero's 60 fps loop never re-renders the wordmark. */
function AxisReadout({ bind }: { bind: { current: (axis: Axis) => void } }) {
  const [axis, setAxis] = useState<Axis>({ wght: 400, rond: null });
  useEffect(() => { bind.current = setAxis; }, [bind]);
  return <output>
    <NumberFlow value={axis.wght} transformTiming={ROLL} spinTiming={ROLL} />
    {axis.rond != null && <> · ROND <NumberFlow value={axis.rond} transformTiming={ROLL} spinTiming={ROLL} /></>}
  </output>;
}

/**
 * The hero wordmark: every letter is its own span whose weight (and, in Pixel, roundness) follows the
 * pointer, or breathes on a slow wave when idle. Styles are written straight to the DOM in a rAF loop
 * (no React renders per frame), and the loop sleeps while the hero is off screen or the tab is hidden.
 */
export function Hero({ version, zip, stats }: {
  version: string; zip: { href: string; size: string } | null;
  stats: { label: string; value: string }[];
}) {
  const [family, setFamily] = useState<Fam>('sans');
  const heroRef = useRef<HTMLElement>(null);
  const wordRef = useRef<HTMLHeadingElement>(null);
  const readoutRef = useRef<(axis: Axis) => void>(() => {});
  const hintRef = useRef<HTMLSpanElement>(null);
  const familyRef = useRef<Fam>('sans');
  const kickRef = useRef<() => void>(() => {});

  useEffect(() => {
    const hero = heroRef.current!;
    const word = wordRef.current!;
    let lastReadout = 0;
    let shown = '';
    const hint = hintRef.current!;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (window.matchMedia('(pointer: coarse)').matches) hint.textContent = 'drag across';
    const chars = [...word.querySelectorAll<HTMLSpanElement>('.ch')].map((el) => ({ el, w: 400, tw: 400, r: 0, tr: 0, cx: 0, cy: 0 }));
    let pointer: { x: number; y: number } | null = null;
    let running = false;
    let visible = true;
    let dirty = true;
    const t0 = performance.now();

    const measure = () => {
      for (const c of chars) { const r = c.el.getBoundingClientRect(); c.cx = r.left + r.width / 2; c.cy = r.top + r.height / 2; }
      dirty = false;
    };
    const targets = (now: number) => {
      if (pointer) {
        if (dirty) measure();
        const sigma = Math.max(80, window.innerWidth * 0.12);
        for (const c of chars) {
          const dx = c.cx - pointer.x;
          const dy = (c.cy - pointer.y) * 0.6;
          const k = Math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma));
          c.tw = 100 + 800 * k;
          c.tr = 100 * k;
        }
      } else if (!reduce) {
        const t = (now - t0) / 1000;
        chars.forEach((c, i) => { c.tw = 520 + 360 * Math.sin(t * 0.9 - i * 0.5); c.tr = 50 + 50 * Math.sin(t * 0.7 - i * 0.4); });
      } else {
        for (const c of chars) { c.tw = 600; c.tr = 50; }
      }
    };
    const frame = (now: number) => {
      if (!visible || document.hidden) { running = false; return; }
      targets(now);
      let moving = false;
      let sum = 0;
      let rsum = 0;
      const pixel = familyRef.current === 'pixel';
      for (const c of chars) {
        const dw = c.tw - c.w;
        const dr = c.tr - c.r;
        if (Math.abs(dw) > 0.5 || Math.abs(dr) > 0.2) moving = true;
        c.w += dw * 0.14;
        c.r += dr * 0.14;
        c.el.style.fontWeight = String(Math.round(c.w));
        c.el.style.fontVariationSettings = pixel ? `"ROND" ${c.r.toFixed(1)}` : '';
        sum += c.w;
        rsum += c.r;
      }
      if (now - lastReadout >= READOUT_MS || !moving) {
        const axis = { wght: Math.round(sum / chars.length), rond: pixel ? Math.round(rsum / chars.length) : null };
        const key = `${axis.wght}:${axis.rond}`;
        if (key !== shown) { shown = key; lastReadout = now; readoutRef.current(axis); }
      }
      if (moving) dirty = true;
      if (pointer || !reduce || moving) requestAnimationFrame(frame);
      else running = false;
    };
    const kick = () => { if (!running) { running = true; requestAnimationFrame(frame); } };
    kickRef.current = () => { dirty = true; kick(); };

    const onMove = (e: PointerEvent) => { pointer = { x: e.clientX, y: e.clientY }; hint.hidden = true; kick(); };
    const onLeave = () => { pointer = null; kick(); };
    const onDirty = () => { dirty = true; };
    const onVisibility = () => { if (!document.hidden) kick(); };
    hero.addEventListener('pointermove', onMove);
    hero.addEventListener('pointerleave', onLeave);
    window.addEventListener('resize', onDirty, { passive: true });
    window.addEventListener('scroll', onDirty, { passive: true });
    document.addEventListener('visibilitychange', onVisibility);
    const io = new IntersectionObserver(([entry]) => { visible = entry!.isIntersecting; if (visible) kick(); });
    io.observe(word);
    if (reduce) for (const c of chars) { c.w = c.tw = 600; c.el.style.fontWeight = '600'; }
    kick();
    return () => {
      hero.removeEventListener('pointermove', onMove);
      hero.removeEventListener('pointerleave', onLeave);
      window.removeEventListener('resize', onDirty);
      window.removeEventListener('scroll', onDirty);
      document.removeEventListener('visibilitychange', onVisibility);
      io.disconnect();
      visible = false;
    };
  }, []);

  function choose(next: Fam) {
    familyRef.current = next;
    setFamily(next);
    kickRef.current();
  }

  return <section ref={heroRef} className="hero" aria-labelledby="hero-title">
    <div className="hero-grid">
    <div className="hero-main">
    <p className="eyebrow"><span className="status-dot" aria-hidden="true" /> Open source · SIL OFL 1.1{version ? ` · v${version}` : ''}</p>
    <h1 id="hero-title" ref={wordRef} className="hero-word" data-family={family} aria-label="Bloxwap Font">
      {LINES.map((line, i) => <span key={line} className={`hw-line${i ? ' hw-line-2' : ''}`} aria-hidden="true">
        {[...line].map((ch, j) => <span key={j} className="ch">{ch}</span>)}
      </span>)}
    </h1>
    <div className="hero-bottom">
      <div className="hero-copy">
        <p className="hero-tag">Rounded typefaces for interfaces, code and screens — with Arabic, Armenian, Georgian, Hebrew and CJK companions. Free and open source.</p>
        <div className="hero-cta">
          {zip
            ? <a className="btn" href={zip.href} download><Download aria-hidden="true" /> Download Sans, Mono &amp; Pixel <span className="btn-meta">{zip.size}</span></a>
            : <a className="btn" href="#download"><Download aria-hidden="true" /> Download</a>}
          <a className="btn btn--secondary" href="#tester">Try it <ArrowDown aria-hidden="true" /></a>
        </div>
        <InstallCommand />
      </div>
      <div className="hero-side">
        <Segmented label="Hero typeface" value={family} onChange={choose}
          options={[{ value: 'sans', label: 'Sans' }, { value: 'mono', label: 'Mono' }, { value: 'pixel', label: 'Pixel' }]} />
        <p className="hero-axis mono-label"><span>wght</span> <AxisReadout bind={readoutRef} /> <span className="hint" ref={hintRef}>move your pointer</span></p>
      </div>
    </div>
    </div>
    <HeroCode />
    </div>
    <dl className="stats">
      {stats.map((s) => <div key={s.label}><dt>{s.label}</dt><dd>{s.value}</dd></div>)}
    </dl>
  </section>;
}
