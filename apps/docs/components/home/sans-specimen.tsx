'use client';

import { useEffect, useRef, useState } from 'react';
import NumberFlow, { NumberFlowGroup } from '@number-flow/react';
import { Switch } from '@/components/ui/controls';

const TICKER: [string, string, number][] = [
  ['BTC', 'Bitcoin', 67421.08], ['ETH', 'Ethereum', 3512.44], ['SOL', 'Solana', 148.21], ['HYPE', 'Hyperliquid', 38.17],
  ['XAU', 'Gold', 2634.1], ['NVDA', 'NVIDIA', 131.26], ['AAPL', 'Apple', 227.52],
];
const DRIFT = [-0.0194, 0.0062, -0.0418, -0.124, -0.0031, 0.0112, -0.0078];
/** Fixed-decimal en-US format for NumberFlow (the same output toLocaleString gave). */
const fixed = (digits = 2) => ({ minimumFractionDigits: digits, maximumFractionDigits: digits });
const sign = (v: number) => (v >= 0 ? '+' : '−');

interface Row { sym: string; name: string; open: number; px: number; flash: 0 | 1 | -1; tick: number }

/** Bloxwap Sans in a trading UI: a live watchlist (tabular figures toggle), an order ticket and a big price. */
export function SansSpecimen() {
  const [tabular, setTabular] = useState(true);
  const [rows, setRows] = useState<Row[]>(() => TICKER.map(([sym, name, px], i) => ({ sym, name, px, open: px * (1 + DRIFT[i]!), flash: 0, tick: 0 })));
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let visible = false;
    const io = new IntersectionObserver(([entry]) => { visible = entry!.isIntersecting; });
    io.observe(ref.current!);
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const timer = window.setInterval(() => {
      if (!visible || document.hidden) return;
      setRows((current) => {
        const next: Row[] = current.map((r) => ({ ...r, flash: 0 }));
        const n = 1 + Math.floor(Math.random() * 3);
        for (let k = 0; k < n; k++) {
          const i = Math.floor(Math.random() * next.length);
          const r = next[i]!;
          const step = (Math.random() - 0.48) * r.px * 0.0016;
          next[i] = { ...r, px: Math.max(0.01, r.px + step), flash: step >= 0 ? 1 : -1, tick: r.tick + 1 };
        }
        return next;
      });
    }, reduce ? 2600 : 1100);
    return () => { window.clearInterval(timer); io.disconnect(); };
  }, []);

  const btc = rows[0]!;
  const delta = btc.px - btc.open;
  const pct = (delta / btc.open) * 100;
  return <div ref={ref} className={`bento ${tabular ? 'tabular' : 'proportional'}`}>
    <article className="card card-editorial span-7">
      <p className="kicker mono-label">Markets · Sunday edition</p>
      <h3 className="ed-head">Good type is quiet until the market isn’t.</h3>
      <p className="ed-body">When volatility spikes, interfaces get loud: flashing quotes, stacked alerts, numbers that won’t sit still. Bloxwap Sans keeps its voice even. Smooth round bowls and simple, tail-free shapes stay clear in dense screens, tall x-heights hold up at 11&nbsp;px, and nine weights give hierarchy without shouting.</p>
      <div className="ed-weights" aria-hidden="true">
        {[[100, 'Thin'], [300, 'Light'], [400, 'Regular'], [600, 'SemiBold'], [800, 'ExtraBold'], [900, 'Black']].map(([w, n]) => <span key={n} style={{ fontWeight: w }}>{n}</span>)}
      </div>
    </article>

    <article className="card card-ticker span-5" aria-labelledby="ticker-title">
      <div className="card-bar">
        <h3 id="ticker-title" className="card-title">Watchlist</h3>
        <Switch label={<><code>tnum</code> tabular</>} checked={tabular} onChange={setTabular} />
      </div>
      <table className="ticker">
        <thead><tr><th scope="col">Asset</th><th scope="col" className="num">Price</th><th scope="col" className="num">24h</th></tr></thead>
        <tbody>{rows.map((r) => {
          const ch = ((r.px - r.open) / r.open) * 100;
          return <tr key={r.sym}>
            <td className="sym">{r.sym}<small>{r.name}</small></td>
            <td className={`num px${r.flash > 0 ? ' flash-up' : r.flash < 0 ? ' flash-dn' : ''}`}><NumberFlow value={r.px} locales="en-US" format={fixed(r.px >= 10 ? 2 : 4)} /></td>
            <td className={`num chg ${ch >= 0 ? 'up' : 'dn'}`}><NumberFlow value={Math.abs(ch)} locales="en-US" format={fixed()} prefix={sign(ch)} suffix="%" /></td>
          </tr>;
        })}</tbody>
      </table>
      <p className="card-foot">Toggle <code>tnum</code> off to watch proportional figures shift as prices tick.</p>
    </article>

    <article className="card card-order span-5" aria-label="Order ticket sample">
      <div className="ot-tabs" aria-hidden="true"><span className="on">Buy</span><span>Sell</span></div>
      <div className="ot-pair"><span className="ot-sym">BTC-USD</span><span className="ot-px"><NumberFlow value={btc.px} locales="en-US" format={fixed()} /></span></div>
      <div className="ot-field"><span>Amount</span><strong>0.2500 <small>BTC</small></strong></div>
      <div className="ot-field"><span>Limit price</span><strong>$67,400.00</strong></div>
      <div className="ot-meter" aria-hidden="true"><i style={{ width: '62%' }} /></div>
      <div className="ot-field ot-total"><span>Total</span><strong>$16,850.00</strong></div>
      <span className="ot-btn" aria-hidden="true">Place buy order</span>
    </article>

    <article className="card card-price span-7" aria-label="Figures specimen">
      <p className="mono-label">BTC · Bitcoin</p>
      <p className="big-price" role="region" tabIndex={0} aria-label="Bitcoin price specimen, horizontally scrollable"><NumberFlow value={btc.px} locales="en-US" format={fixed()} prefix="$" /></p>
      <NumberFlowGroup>
        <p className={`price-change ${delta >= 0 ? 'up' : 'dn'}`}>
          <NumberFlow value={Math.abs(delta)} locales="en-US" format={fixed()} prefix={sign(delta)} />{' ('}
          <NumberFlow value={Math.abs(pct)} locales="en-US" format={fixed()} prefix={sign(pct)} suffix="%" />{') today'}
        </p>
      </NumberFlowGroup>
      <div className="fig-row" aria-hidden="true"><span>0123456789</span><span className="fig-it">0123456789</span></div>
      <div className="fig-row fig-sym" aria-hidden="true"><span>$ € £ ¥ ₿ % ‰ + − × ÷ = ≈ ≠ ≤ ≥ ← ↑ → ↓</span></div>
    </article>
  </div>;
}
