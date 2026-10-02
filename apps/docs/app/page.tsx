import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { HomeLayout } from 'fumadocs-ui/layouts/home';
import { baseOptions } from '@/lib/layout.shared';
import { getIndex, getMetas, getTotals } from '@/lib/font-data';
import { fmtBytes, fmtNum } from '@/lib/format';
import { downloadUrl } from '@/lib/site';
import { Hero } from '@/components/home/hero';
import { FamilyCards } from '@/components/home/family-cards';
import { SansSpecimen } from '@/components/home/sans-specimen';
import { MonoSpecimen } from '@/components/home/mono-specimen';
import { PixelSpecimen } from '@/components/home/pixel-specimen';
import { TypeTester } from '@/components/home/type-tester';
import { GlyphBrowser } from '@/components/home/glyph-browser';
import { LanguageList } from '@/components/home/language-list';
import { Downloads } from '@/components/home/downloads';
import { SiteFooter } from '@/components/site-footer';
import { Toaster } from '@/components/ui/toast';

function Missing({ name }: { name: string }) {
  return <p className="fam-note">{name} is still being drawn — specimens below use a fallback font for now.</p>;
}

export default function Home() {
  const index = getIndex();
  const metas = getMetas();
  const totals = getTotals();
  const byId = new Map(metas.map((m) => [m.id, m]));
  const pixel = byId.get('pixel');
  const stats = [
    { label: 'Families', value: fmtNum(totals.families || 3) },
    { label: 'Scripts', value: totals.scripts.length ? fmtNum(totals.scripts.length) : '—' },
    { label: 'Characters', value: totals.characters ? fmtNum(totals.characters) : '—' },
    { label: 'Languages', value: totals.languages ? fmtNum(totals.languages) : '—' },
  ];

  return <HomeLayout {...baseOptions()}>
    <main className="home" id="main">
      <Hero version={totals.version} stats={stats}
        zip={index.zip ? { href: downloadUrl(index.zip.path), size: fmtBytes(index.zip.bytes) } : null} />

      <FamilyCards families={metas} catalog={index.catalog} />

      <section className="section" id="sans" aria-labelledby="sans-title">
        <header className="sec-head">
          <p className="eyebrow">01 — Bloxwap Sans</p>
          <h2 id="sans-title">Built for numbers that move.</h2>
          <p className="lede">A rounded neo-grotesk with smooth, nearly circular curves, open apertures and friendly round figures — tabular by default, so prices, balances and charts stay perfectly aligned while they update.</p>
          {!byId.has('sans') && <Missing name="Bloxwap Sans" />}
        </header>
        <SansSpecimen />
      </section>

      <section className="section" id="mono" aria-labelledby="mono-title">
        <header className="sec-head">
          <p className="eyebrow">02 — Bloxwap Mono</p>
          <h2 id="mono-title">Same voice, fixed width.</h2>
          <p className="lede">Every glyph sits on a 600-unit cell with rounded slabs on narrow letters, unmistakable <code>0O 1lI</code>, and optional code ligatures that never break the grid.</p>
          {!byId.has('mono') && <Missing name="Bloxwap Mono" />}
        </header>
        <MonoSpecimen />
      </section>

      <section className="section" id="pixel" aria-labelledby="pixel-title">
        <header className="sec-head">
          <p className="eyebrow">03 — Bloxwap Pixel</p>
          <h2 id="pixel-title">Pixels, with a soft side.</h2>
          <p className="lede">A bitmap-grid display face with two axes: weight fattens every pixel, roundness morphs them from crisp squares to dots. Made for scoreboards, tickers and game-like moments.</p>
          {!pixel && <Missing name="Bloxwap Pixel" />}
        </header>
        <PixelSpecimen axes={pixel?.axes ?? []} hasItalic={pixel?.hasItalic ?? true} />
      </section>

      <section className="section" id="tester" aria-labelledby="tester-title">
        <header className="sec-head">
          <p className="eyebrow">04 — Type tester</p>
          <h2 id="tester-title">Try every axis and feature.</h2>
        </header>
        <TypeTester families={metas} />
      </section>

      <section className="section" id="glyphs" aria-labelledby="glyphs-title">
        <GlyphBrowser families={metas} />
      </section>

      <section className="section" id="languages" aria-labelledby="lang-title">
        <LanguageList families={metas} />
      </section>

      <section className="section" id="download" aria-labelledby="dl-title">
        <header className="sec-head">
          <p className="eyebrow">07 — Download</p>
          <h2 id="dl-title">Free for any project.</h2>
          <p className="lede">Every family ships as OTF, TTF, WOFF2, WOFF and variable fonts under the SIL Open Font License 1.1 — use them in apps, sites, print and products, commercial or not.</p>
        </header>
        <Downloads families={metas} zip={index.zip} />
      </section>

      <section className="start-grid" aria-labelledby="docs-title">
        <div>
          <p className="eyebrow">Documentation</p>
          <h2 id="docs-title">From one stylesheet<br />to a whole type system.</h2>
          <p>Install the fonts, pick features and axes in CSS, and see exactly what each family covers.</p>
        </div>
        <div className="guide-links">{[
          ['/docs/installation', '01', 'Installation', 'Download, self-host with @font-face, Next.js and Tailwind.'],
          ['/docs/usage', '02', 'Usage', 'Weights, italics, variation and feature settings.'],
          ['/docs/opentype-features', '03', 'OpenType features', 'Every feature with a live before and after.'],
          ['/docs/multi-script', '04', 'Every script, one family', 'Companion scripts merged with unicode-range.'],
        ].map(([href, number, title, description]) => <Link href={href!} key={href}><span>{number}</span><div><h3>{title}</h3><p>{description}</p></div><ArrowRight aria-hidden="true" /></Link>)}</div>
      </section>
    </main>
    <SiteFooter />
    <Toaster />
  </HomeLayout>;
}
