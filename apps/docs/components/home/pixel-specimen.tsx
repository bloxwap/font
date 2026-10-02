'use client';

import { useState, type ClipboardEvent } from 'react';
import { Range, Switch } from '@/components/ui/controls';
import type { Axis } from '@/lib/types';

const ITEMS: [string, string, string][] = [['BTC', '67,421', '+1.9%'], ['ETH', '3,512', '−0.6%'], ['SOL', '148.21', '+4.2%'], ['HYPE', '38.17', '+12.4%'], ['XAU', '2,634', '+0.3%'], ['NVDA', '131.26', '−1.1%']];

export function plainPaste(event: ClipboardEvent<HTMLElement>) {
  event.preventDefault();
  document.execCommand('insertText', false, event.clipboardData.getData('text/plain'));
}

/** Bloxwap Pixel: an editable scoreboard with the wght and ROND axes, plus a ticker marquee. */
export function PixelSpecimen({ axes, hasItalic }: { axes: Axis[]; hasItalic: boolean }) {
  const wa = axes.find((a) => a.tag === 'wght') ?? { min: 100, max: 900, default: 400 };
  const ra = axes.find((a) => a.tag === 'ROND') ?? { min: 0, max: 100, default: 0 };
  const [wght, setWght] = useState(wa.default);
  const [rond, setRond] = useState(ra.default);
  const [italic, setItalic] = useState(false);
  const marquee = ITEMS.map(([s, p, c]) => <span key={s}><b>{s}</b> {p} <b className={c[0] === '+' ? 'up' : 'dn'}>{c[0] === '+' ? '▲' : '▼'} {c}</b></span>);
  return <>
    <div className="card card-pixel">
      <div className="pixel-stage" contentEditable suppressContentEditableWarning spellCheck={false} role="textbox" aria-multiline="true"
        aria-label="Pixel specimen, editable" onPaste={plainPaste}
        style={{ fontWeight: wght, fontVariationSettings: `"ROND" ${rond}`, fontStyle: italic ? 'italic' : 'normal' }}>{'BUY LOW\nSELL HIGH'}</div>
      <div className="pixel-controls">
        <Range label="Weight" min={wa.min} max={wa.max} value={wght} onChange={setWght} />
        <Range label={<>Roundness <code>ROND</code></>} min={ra.min} max={ra.max} value={rond} onChange={setRond} />
        {hasItalic && <Switch label="Italic" checked={italic} onChange={setItalic} />}
      </div>
    </div>
    <div className="marquee" aria-hidden="true"><div className="marquee-track">{marquee}{marquee.map((m, i) => <span key={`b${i}`}>{m.props.children}</span>)}</div></div>
  </>;
}
