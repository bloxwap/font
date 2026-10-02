import Link from 'next/link';
import { ArrowRight, Download } from 'lucide-react';
import { CopyTextButton } from '@/components/ui/copy-text-button';
import { fontStack, shortName } from '@/lib/families';
import { fmtBytes, fmtNum } from '@/lib/format';
import { downloadUrl, fileUrl, publicUrl } from '@/lib/site';
import type { FamilyMeta, ZipFile } from '@/lib/types';

const LABEL: Record<string, string> = { otf: 'OpenType (OTF)', ttf: 'TrueType (TTF)', woff2: 'WOFF2', woff: 'WOFF', variable: 'Variable' };

function DownloadCard({ meta }: { meta: FamilyMeta }) {
  const formats = meta.files.formats;
  const zip = meta.files.zip;
  const axes = meta.axes.map((a) => `${a.tag} ${a.min}–${a.max}`).join(' · ');
  const stack = fontStack(meta.name, meta.style);
  return <article className="card dl-card">
    <div className="dl-head">
      <div><h3 style={{ fontFamily: stack }}>{meta.name}</h3><p>{meta.blurb}</p></div>
      <span className="dl-aa" style={{ fontFamily: stack }} aria-hidden="true">Ag</span>
    </div>
    <p className="mono-label">{axes}{` · ${fmtNum(meta.counts.glyphs)} glyphs`}{meta.hasItalic ? ' · italics' : ''}</p>
    <ul className="dl-formats">{Object.keys(LABEL).map((fmt) => {
      const group = formats[fmt as keyof typeof formats];
      return group
        ? <li key={fmt}><span>{LABEL[fmt]}</span><span>{group.count} file{group.count === 1 ? '' : 's'} · {fmtBytes(group.bytes)}</span></li>
        : <li key={fmt} className="na"><span>{LABEL[fmt]}</span><span>—</span></li>;
    })}</ul>
    {meta.files.web.length > 0 && <details>
      <summary>Web fonts ({meta.files.web.length} WOFF2)</summary>
      <ul>{meta.files.web.map((w) => <li key={w.path}><a href={fileUrl(w.path)}>{w.name}</a> <span className="l-iso">{fmtBytes(w.bytes)}</span></li>)}</ul>
    </details>}
    {zip
      ? <a className="btn btn--secondary" href={downloadUrl(zip.path)} download><Download aria-hidden="true" /> Download {shortName(meta.name)} <span className="btn-meta">{fmtBytes(zip.bytes)}</span></a>
      : <span className="btn btn--secondary" aria-disabled="true">Zip available after release build</span>}
  </article>;
}

const FONT_FACE = `@font-face {
  font-family: "Bloxwap Sans";
  src: url("BloxwapSans[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Bloxwap Sans";
  src: url("BloxwapSans-Italic[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: italic;
  font-display: swap;
}`;
const USE = `body {
  font-family: "Bloxwap Sans", system-ui, sans-serif;
  font-weight: 450; /* any value 100–900 */
}
.price {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1, "ss01" 1;
}
code, pre {
  font-family: "Bloxwap Mono", ui-monospace, monospace;
  font-feature-settings: "calt" 1; /* code ligatures */
}
.scoreboard {
  font-family: "Bloxwap Pixel", monospace;
  font-weight: 700;
  font-variation-settings: "ROND" 60;
}`;

function Snippet({ title, code, className }: { title: string; code: string; className?: string }) {
  return <div className={`snippet ${className ?? ''}`}>
    <div className="snippet-bar"><span className="mono-label">{title}</span><CopyTextButton text={code} ariaLabel={`Copy: ${title}`} /></div>
    <pre className="css-code">{code}</pre>
  </div>;
}

/** Download cards for every built family and the web usage snippets. Server-rendered from the data. */
export function Downloads({ families, zip }: { families: FamilyMeta[]; zip: ZipFile | null }) {
  const primary = families.filter((f) => !f.companion);
  const companions = families.filter((f) => f.companion);
  const sansVf = families.find((f) => f.id === 'sans')?.files.web.find((w) => w.variable && !/Italic/.test(w.name));
  const preloadPath = sansVf?.path ?? 'fonts/BloxwapSans/variable/BloxwapSans[wght].woff2';
  const cdn = `<link rel="preload" href="${publicUrl(preloadPath)}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="${publicUrl('bloxwap-font.css')}">
<style>
  body { font-family: "Bloxwap Sans", system-ui, sans-serif; }
  code { font-family: "Bloxwap Mono", ui-monospace, monospace; }
</style>`;
  return <>
    <div className="dl-all card">
      <div>
        <h3>All families</h3>
        <p>{primary.map((f) => shortName(f.name)).join(', ')}{companions.length ? ` and ${companions.length} companion famil${companions.length === 1 ? 'y' : 'ies'}` : ''} — static and variable, desktop and web formats, plus <code>OFL.txt</code>.</p>
      </div>
      {zip
        ? <a className="btn" href={downloadUrl(zip.path)} download><Download aria-hidden="true" /> Download all <span className="btn-meta">{fmtBytes(zip.bytes)}</span></a>
        : <span className="btn" aria-disabled="true">Download all <span className="btn-meta">soon</span></span>}
    </div>
    <div className="dl-grid">{primary.map((meta) => <DownloadCard key={meta.id} meta={meta} />)}</div>
    {companions.length > 0 && <div className="dl-grid dl-grid--companions">{companions.map((meta) => <DownloadCard key={meta.id} meta={meta} />)}</div>}

    <div className="usage">
      <h3 className="usage-title">Use on the web</h3>
      <div className="usage-grid">
        <Snippet title="1 · Self-host with @font-face" code={FONT_FACE} />
        <Snippet title="2 · Use it" code={USE} />
        <Snippet title="3 · Or link the hosted stylesheet (every family, every script)" code={cdn} className="span-2" />
      </div>
      <div className="usage-links">
        <Link className="btn btn--secondary btn--sm" href="/docs/installation">Installation guide <ArrowRight aria-hidden="true" /></Link>
        <Link className="btn btn--ghost btn--sm" href="/docs/multi-script">One family for every script <ArrowRight aria-hidden="true" /></Link>
        <Link className="btn btn--ghost btn--sm" href="/docs/opentype-features">OpenType features <ArrowRight aria-hidden="true" /></Link>
      </div>
    </div>
  </>;
}
