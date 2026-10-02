# Design review: `apps/docs` against the Bloxwap design system

Reviewed on 2026-10-01 with the zandesign catalog. The references are the other Bloxwap sites, compared in source and in the browser:

- **sfx docs** (`sfx/apps/docs`, <https://bloxwap.github.io/sfx/>) and **chart docs** (`chart-ts/apps/docs`,
  <https://bloxwap.github.io/chart/>). They share one Fumadocs shell and plain-UI's `.btn` family. Cards are zero-stroke
  fills; controls are pills at `--control-h-sm`; the code palette is pink keywords, green strings and blue types; copy
  buttons are Lucide icon ghosts; the theme is dark only (`forcedTheme: 'dark'`).
- **bloxwap.com** and **bloxwap.github.io**: dark only, `#171717` borderless cards on Bloxwap black, a green pill CTA.

## Verdict

The docs shell (sidebar, prose, search pill, footer, `.btn`, scale layer, hero entrance) was already ported from sfx.
The landing page and its controls were not. Every surface was a 1 px-bordered card with ruled dividers inside it,
controls were stroked 40 px boxes, and the site had a light mode that no other Bloxwap site has. The biggest lever was
one systemic pass on `styles/tokens.css` and `app/global.css`: dark only, zero-stroke fill cards, pill controls, and
values on the token scale. After that pass the site reads as part of the same family as sfx and chart.

## Findings

All findings below are applied.

| ID | Sev | Check | Where | Finding | Fix |
|---|---|---|---|---|---|
| F1 | P0 | BTN-1 | `components/home/downloads.tsx` `DownloadCard` | The Download section had 18 brand-green primary buttons: "All families", the 3 primary families and 14 companion families. | "All families" stays primary. Per-family downloads are `.btn--secondary`, which is muted on a card. |
| F2 | P0 | TYPE-3 | `styles/tokens.css` `--faint` | `#6f6f6f` text was 3.6:1 on cards and 3.9:1 on the page. It is used for glyph counts, ISO codes, tester hints, feature-preview labels, glyph names and code comments. | `--faint: #858585`, which is 4.9:1 on `--card` and 5.4:1 on black. |
| F3 | P1 | COL-2 (brand parity) | `components/provider.tsx`, `app/layout.tsx`, `lib/layout.shared.tsx`, `styles/tokens.css`, `components/site-footer.tsx` | The site followed the system theme and had a light/dark toggle. sfx, chart, bloxwap.com and bloxwap.github.io are all dark only. | `forcedTheme: 'dark'`, `className="dark"` on `<html>`, the theme switch removed, one dark palette, `themeColor` and `colorScheme` set to dark, and one footer lockup. |
| F4 | P1 | LAY-2 / LAY-1 | `app/global.css` (about 30 rule sets) | Cards, panels, snippets, the glyph grid, language cards, facts, specimens, callouts and the marquee all had a `1px solid var(--border)`. Inside them, dividers separated tester groups, snippet bars, pixel controls, the glyph stage, waterfall rows, download rows and the hero stats. | Zero-stroke fill cards (`--card`, `--radius-xl`). Hover shifts the fill to `--muted`, nested surfaces use `--muted`, and spacing replaces the dividers. Only data-table rules and glyph guides keep lines. |
| F5 | P1 | HIER-1 / LAY-5 | `components/home/family-cards.tsx`, `.fam-status` | On companion cards the absolutely positioned glyph count overlapped the family name ("Sans Armenian" sat under "2,715 GLYPHS"). | Companion counts now sit in the meta column under the description, next to the thing they measure. |
| F6 | P1 | HIER-4 | `lib/layout.shared.tsx` `links` | The nav had Docs, Tester, Glyphs and Download; the sfx nav has only Docs. The hero CTA, "Try it" and the section anchors already reach the rest. | `links: [Docs]`, as in sfx. |
| F7 | P2 | BTN-5 / HIER-6 | `app/global.css` `.seg`, `.chip`, `select`, `.search-field`, `.switch`, `.copy-btn`; `components/ui/copy-text-button.tsx` | Controls used strokes, 10 px radii, 40 px heights and an inset selection ring. Copy was a stroked text pill. | The segmented control uses sfx's install-tab spec: card track, muted thumb, 32 px. Selects, search and chips are fill pills at `--control-h-sm`. The switch uses sfx's board switch (muted, green when on). Copy is a Lucide `Copy`/`Check` ghost icon button with an sr-only status. On a card, every control's fill steps up to `--muted`. |
| F8 | P2 | TYPE-4 | `app/global.css` | 37 raw-pixel `font:` declarations, and 12 px caps eyebrows. | Down to 5; the rest are specimen display sizes. Chrome text uses `--text-*`. Eyebrows and meta labels are 11 px mono with 0.09em tracking, matching sfx/chart. |
| F9 | P2 | LAY-3 | `app/global.css` | Off-grid spacing: 3, 5, 6, 7, 9, 10, 14, 18 and 22 px. | `--space-*`. |
| F10 | P2 | MOT-4 | `app/global.css` | Ad hoc `.1s`, `.12s`, `.15s`, `.18s` and `.2s` transitions, some with linear defaults. | `--duration-fast`/`--duration-base` with `--ease-spring`, which reduced motion zeroes. Pressed scale added to feature toggles. |
| F11 | P2 | COL-1 | `styles/tokens.css`, `.tk-k` | The Mono specimen used green keywords and amber strings. sfx and chart use pink keywords, green strings and blue types. | `--code-keyword`, `--code-string` and `--code-type` now carry the sfx/chart values. |
| F12 | P2 | BTN-4 | `components/home/downloads.tsx`, `.dl-all` | At 390 px, "Download Sans, Mono & Pixel 38.1 MB" overflowed its card. | The label is now "Download all"; the heading already says "All families". The hero and "All families" primaries go full width under 600 px, as sfx's mobile hero does. |
| F13 | P2 | COL-1 | `app/global.css` `--color-fd-*` | The Fumadocs mapping sent muted, secondary and accent to an extra `--card-2` step that sfx and chart don't have. | Mapped exactly as in sfx/chart. `--card-2` and `--shadow` are removed. |

**Verified clean:** TYPE-1, TYPE-2 (caps only on labels of 11 px or less), COL-4, COL-6, FORM-2, MODAL-1 (no modals),
MOT-1, MOT-2 (the hero entrance was already staggered like sfx's), IMG-1 (Lucide only), IMG-3, HIER-3 (family and
language cards lead with a glyph).

## P0 detail

### F1: One primary per view (BTN-1)

**Evidence:** In the Download section, every one of the 17 download cards ended in a full brand-green pill, under a green
"All families" pill. Nothing marked the recommended action.

**Why:** with every action primary, users have to hunt for *the* action.
<https://x.com/zander_supafast/status/1802684455670136954>

```diff
-      ? <a className="btn" href={…} download>… Download {shortName(meta.name)} …
+      ? <a className="btn btn--secondary" href={…} download>… Download {shortName(meta.name)} …
```

### F2: Faint text contrast (TYPE-3)

**Evidence:** `#6f6f6f` on `#171717` is 3.6:1, below the 4.5:1 needed for the 9–12 px text that uses it.

**Why:** text that fails contrast is decoration, not content.
<https://x.com/zander_supafast/status/1968252670604685678>

```diff
-  --faint: #6f6f6f;
+  --faint: #858585; /* 4.9:1 on --card, 5.4:1 on black */
```

## P1 detail

- **F3 (dark only):** this was a user decision, confirmed during review. All four reference sites force dark, and
  specimens now render on the same black as the rest of the brand.
- **F4 (cards, not rules):** this follows the chart review's team preference ("Bloxwap cards are fill-only").
  <https://x.com/zander_supafast/status/2080000671781110136>
- **F5:** a layout bug, fixed by moving the metric into proximity with its subject (LAY-5).
  <https://x.com/zander_supafast/status/1802939950645584131>
- **F6:** <https://x.com/zander_supafast/status/1968252670604685678>

## Systemic recommendations

1. **Token and shared-component pass (applied).** F2–F4 and F7–F13 were fixed almost entirely in `styles/tokens.css`
   and `app/global.css`. One `:where(.card, .t-panel, .t-view, .bw-specimen, …)` rule raises control fills one level
   on any card, so new components inherit it.
2. **Publish the docs theme once (not done).** sfx, chart, hyperliquid and font now copy the same Fumadocs overrides,
   `.btn` family, scale layer, search pill, footer and page-end styles. A `@workspace/docs-theme` stylesheet next to
   `plain-ui`, as the chart review suggested, would stop this drift at the source. The font site's palette now
   matches `tokens.generated.css` closely enough to switch to it.

## Outside catalog (reviewer judgment)

- **React key warning (fixed):** Fumadocs puts the sidebar `footer` in a list, so the dev overlay reported a missing
  `key` on `docs-sidebar-footer`. Adding `key="sidebar-footer"` fixes it. sfx and chart have the same code and the
  same warning.
- **Hash anchors landed low (fixed, 2026-10-02):** `/#tester`, `/#glyphs` and the other section anchors stopped with the
  eyebrow about 285 px down, so most of the previous section was still showing. Three offsets stacked: html
  `scroll-padding-top: 5rem`, `.section { scroll-margin-top: 4.5rem }`, and the section's own `clamp(64px, 9vw, 120px)`
  top padding. `.section` now sets `scroll-margin-top: calc(-1 * var(--section-pad))`, so the eyebrow stops at the
  5rem scroll padding, as docs headings do (measured with headless Playwright: section top −40 px, eyebrow just under
  the header). An earlier "lands in the wrong section" reading was a screenshot taken mid smooth scroll.
- **Live numbers use NumberFlow (2026-10-02):** `@number-flow/react` 0.6.2 now renders every number that changes on
  its own: the watchlist prices and 24h changes, the order-ticket price, the big BTC price and its change (as a
  `NumberFlowGroup`), the hero `wght`/`ROND` readout, and the glyph and language headline counts. Proportional figures
  still shift when `tnum` is off, because NumberFlow inherits the cell's `font-variant-numeric`. The hero samples
  every 160 ms with a 320 ms roll, so its 60 fps loop never re-renders the wordmark. Reduced motion turns the roll off.
  Every slider readout rolls too: the shared `Range` renders its value with NumberFlow (`format`/`suffix` props, plus
  a plain-text `note` for instance names such as "Regular"). That covers the tester, the Pixel specimen, the glyph
  inspector and the docs specimens, all on the same 320 ms `QUICK_ROLL` (`lib/number-flow.ts`) so the digits keep up
  with a drag.
- **Order-ticket specimen (left as is):** the Sans specimen's mock order form keeps a green "Buy" tab and a "Place buy
  order" button. It is specimen content showing the type in a trading UI, not a site action.

## Verification

- `bun run check` (fumadocs-mdx, next typegen, `tsc --noEmit`) passes.
- Checked in Chrome against the running dev server (`:3904`) at 1440 px: home (all sections), `/docs/families/sans`,
  `/docs/opentype-features` and `/docs/language-support`. Checked at 390 px in iframes, because the window would not
  resize narrower: home, downloads and a docs table. There is no horizontal overflow.
- **Not run:** `bun run build` (the dev server was running) and the Playwright smoke test (it needs `DOCS_URL` pointing
  at a served build). Neither touches anything this pass changed: no test asserts copy text, theme or nav links.
