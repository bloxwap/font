# @bloxwap/font

Bloxwap Sans, Mono and Pixel as variable web fonts, with Arabic, Hebrew, Armenian, Georgian, Japanese, Korean
and Simplified Chinese companions. Specimens, the type tester and docs: **[bloxwap.github.io/font](https://bloxwap.github.io/font/)**.

```sh
npm install @bloxwap/font
```

## Next.js

The `next/font` exports need Next.js 15 or later.

```tsx title="app/layout.tsx"
import { BloxwapSans } from '@bloxwap/font/sans';
import { BloxwapMono } from '@bloxwap/font/mono';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${BloxwapSans.variable} ${BloxwapMono.variable}`}>
      <body className={BloxwapSans.className}>{children}</body>
    </html>
  );
}
```

`BloxwapSans`, `BloxwapMono` and `BloxwapPixel` come from `next/font/local`, so Next.js self-hosts them and preloads
the complete normal face. `next/font/local` accepts only path, weight and style per source;
it cannot assign a different `unicode-range` to each source. Use the CSS entries below for core subsetting. The italic is in the same family but isn't preloaded: a page downloads it only when it renders italic text.
`.variable` defines `--font-bloxwap-sans`, `--font-bloxwap-mono` and `--font-bloxwap-pixel`:

```css
code, pre { font-family: var(--font-bloxwap-mono); }
```

Sans and Mono carry their script companions as a fallback family with `unicode-range`, so a page downloads a companion
font only when its text uses that script. Set Pixel's roundness with `font-variation-settings: "ROND" 0–100`.

## CSS (any framework)

```js
import '@bloxwap/font/css';
```

```css
body { font-family: "Bloxwap Sans", system-ui, sans-serif; }
code { font-family: "Bloxwap Mono", ui-monospace, monospace; }
.score { font-family: "Bloxwap Pixel", monospace; font-variation-settings: "ROND" 60; }
```

Core CSS uses `latin`, `greek`, `cyrillic` and `other` variable WOFF2s.
Greek and Cyrillic include the documented shared combining marks, numbers and punctuation;
Latin is declared last and supplies independently matched common characters.
Latin includes all Latin Extended, IPA, Vietnamese, Latin combining marks, punctuation and currency.
Latin-only Sans upright loads 184,980 bytes instead of 310,848 bytes.
One family name per style covers every script. Each companion is also available under its own name (for example
`"Bloxwap Sans Arabic"`). The WOFF2 files are at `@bloxwap/font/fonts/<Family>/<Family>-Variable.woff2` (and `-Italic-Variable.woff2`).

Subset files use `<Family>-Variable.<subset>.woff2` and `-Italic-Variable.<subset>.woff2`.
The complete variable files remain available at the original paths for self-hosting and Next.js.

Shaping across mixed-script boundaries, such as Latin next to Greek inside one word, is outside the subset guarantee.
The `css/{sans,mono,pixel}-full` entries load complete core fonts for applications that need them.

Weights 100–900 on one variable axis, with italics for Sans, Mono, Pixel, Armenian and Georgian. Desktop formats
(OTF, TTF) are in the [GitHub release](https://github.com/bloxwap/font/releases/latest).

## License

[SIL Open Font License 1.1](https://github.com/bloxwap/font/blob/main/LICENSE). © 2026 Bloxwap, Inc.

## HIG / selective web and native assets (0.1.3 candidate)

The new distribution is a candidate, not yet published. Build a pinned checkout using
Python with `fonttools[woff,unicode]==4.66.1` and `brotli==1.2.0`; set `FONT_PYTHON`
to that interpreter before `npm pack`. No glyph sources are changed by packaging.

- `@bloxwap/font/manifest`: every built face's path, weight, style, ISO 15924 scripts,
  internal font version, package version, bytes and SHA-256. Static faces include
  their package, package-qualified asset import path, unique registration name and variable source hash.
- `@bloxwap/font/css/{sans,mono,pixel}`: one role with its companions.
- `@bloxwap/font/css/{sans,mono}-core` and `pixel-core`: core only.
- `@bloxwap/font/css/{sans,mono}-{arabic,hebrew,armenian,georgian,jp,kr,sc}`:
  script only, retaining unicode-range and swap behavior.
- `@bloxwap/font-native/assets/BloxwapSans/BloxwapSans-SemiBold.ttf`: direct
  Metro `require()` entry for a chosen face, without bundling other weights.
- `@bloxwap/font-native/BloxwapSans` (or another published family): typed Metro
  asset map, e.g. `faces['BloxwapSans-SemiBold']`. Maps bundle every face in that family; prefer direct entries for strict budgets.
  Register only selected TTFs;
  use their exact keys as fontFamily with no fontWeight/fontStyle override.
  Native TTFs decode hash-pinned static WOFF2s without changing glyphs or hinting;
  OS/2 registration weights normalize to named tiers, with sourceWeight retained.
  Static Pixel uses ROND 50. All nine weights and available italics are included.

Native assets ship separately from the web package. Install only the packages you need:

```sh
npm install @bloxwap/font-native
# Optional script companions, for example:
npm install @bloxwap/font-native-jp
```

`@bloxwap/font-native` contains Sans, Mono and Pixel. Packages suffixed `-arabic`,
`-hebrew`, `-armenian`, `-georgian`, `-jp`, `-kr` and `-sc` each contain that
script's Sans and Mono families. Use `@bloxwap/font-native-jp/BloxwapSansJP` or
`@bloxwap/font-native-jp/assets/BloxwapSansJP/BloxwapSansJP-Regular.ttf` for Japanese.
All packages have matching versions and include LICENSE with `OFL-1.1` licensing.
This pre-1.0 move replaces the unpublished candidate native exports under the web
package, with unchanged registration names and TTF bytes and no compatibility shim.
The web package retains the complete manifest and enforces a 20 MB unpacked budget.

Static sources are pinned in `static-sources.json` to a release tag, family zip SHA-256,
and every inner WOFF2 SHA-256. The build verifies `packages/font/fonts/<Family>/woff2/`
first, then downloads only missing families from public release zips. An existing input
with a mismatched hash fails the build. The default zip cache is
`~/.cache/bloxwap-font/static-sources/<tag>/`; set `BLOXWAP_STATIC_SOURCES_CACHE`
to override its root. CI uses job-local storage without GitHub cache saves. The manifest's
`source` records `<asset>.zip:<family>/woff2/<file>.woff2@<tag>` and `sourceSha256`
records the original WOFF2 bytes. Release zips and all packages retain the OFL license.

After rebuilding fonts, run `packages/font/.venv/bin/python packages/npm/scripts/static_sources.py lock --tag v<upcoming-version>`
from the repository root and commit the lock alongside the rebuilt variable fonts and site data.
`lock` reads local zips in `apps/docs/public/downloads/`; `fetch` verifies dist inputs and
fetches missing families (optionally `--family BloxwapSans`). The release script refreshes
the lock before uploading; the pinned release assets must be available before npm CI builds.

The shared build generates all packages in parallel using one process per CPU.
Source and output hashes validate cached native TTFs, so unchanged builds and packs
skip decoding and rewriting them. Run `FONT_PYTHON=../font/.venv/bin/python npm test`
after building from `packages/npm`. For timings and pack sizes, see the repository's
[benchmark harness](../../bench/README.md).

Read [Cross-platform typography](https://bloxwap.github.io/font/docs/cross-platform/)
for Next.js and Expo recipes, locale selection, scaling, licensing and limitations.
`npm test` checks the manifest against the actual built files and binary metadata.
Physical native rendering still requires host/device validation.
