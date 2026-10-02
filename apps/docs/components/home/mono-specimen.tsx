'use client';

import { useState } from 'react';
import { Switch } from '@/components/ui/controls';

/** Bloxwap Mono: a code sample with the calt ligature toggle, a box-drawing terminal, and legibility pairs. */
export function MonoSpecimen() {
  const [ligatures, setLigatures] = useState(true);
  return <div className="bento">
    <article className="card card-code span-7" aria-labelledby="code-title">
      <div className="card-bar">
        <div className="tabs-faux"><span className="tf-dot" /><span className="tf-dot" /><span className="tf-dot" /><h3 id="code-title" className="tf-name">chart.ts</h3></div>
        <Switch label="Ligatures" checked={ligatures} onChange={setLigatures} />
      </div>
      <pre className={`code${ligatures ? '' : ' no-liga'}`} tabIndex={0}><code>
        <span className="tk-c">{'// Stream candles and paint them — 60 fps, no allocations.'}</span>{'\n'}
        <span className="tk-k">import</span>{' { createChart, '}<span className="tk-t">type</span>{' Candle } '}<span className="tk-k">from</span> <span className="tk-s">{'"@bloxwap/chart"'}</span>{';\n\n'}
        <span className="tk-k">const</span>{' chart = createChart(el, { theme: '}<span className="tk-s">{'"dark"'}</span>{', fps: '}<span className="tk-n">60</span>{' });\n\n'}
        <span className="tk-k">export const</span>{' onTick = (c: Candle) => {\n  '}
        <span className="tk-k">if</span>{' (c.close >= c.open && c.volume !== '}<span className="tk-n">0</span>{') chart.push(c);\n  '}
        <span className="tk-k">else if</span>{' (c.close <= c.low || c.flags == '}<span className="tk-n">0x1F</span>{') chart.mark(c, '}<span className="tk-s">{'"<-- wick"'}</span>{');\n  '}
        <span className="tk-k">return</span>{' chart.series?.at('}<span className="tk-n">-1</span>{') ?? '}<span className="tk-k">null</span>{';\n};'}
      </code></pre>
    </article>

    <article className="card card-term span-5" aria-label="Terminal sample">
      <div className="card-bar"><h3 className="card-title">~/bloxwap</h3><span className="mono-label">zsh</span></div>
      <pre className="term" tabIndex={0}>
        <span className="tk-p">$</span>{' bloxwap book BTC-USD --depth 4\n'}
        {'┌──────────┬─────────┬────────┐\n│ '}<b>PRICE</b>{'    │ '}<b>SIZE</b>{'    │ '}<b>SIDE</b>{'   │\n'}
        {'├──────────┼─────────┼────────┤\n'}
        {'│ 67423.50 │  0.4210 │ '}<span className="dn">ask ▼</span>{'  │\n'}
        {'│ 67422.00 │  1.0750 │ '}<span className="dn">ask ▼</span>{'  │\n'}
        {'├──────────┼─────────┼────────┤\n'}
        {'│ 67420.50 │  2.3000 │ '}<span className="up">bid ▲</span>{'  │\n'}
        {'│ 67419.00 │  0.0950 │ '}<span className="up">bid ▲</span>{'  │\n'}
        {'└──────────┴─────────┴────────┘\n'}
        <span className="tk-p">$</span> <span className="cursor" aria-hidden="true">▍</span>
      </pre>
    </article>

    <article className="card card-legible span-12" aria-label="Legibility pairs">
      <div className="legible">
        {[['0O', 'zero / O'], ['1lI', 'one / ell / I'], ['{[()]}', 'brackets'], ['=> !=', 'operators'], ['rn m', 'rn / m']].map(([g, l]) => <div key={l}><span className="lg-g">{g}</span><span className="mono-label">{l}</span></div>)}
      </div>
    </article>
  </div>;
}
