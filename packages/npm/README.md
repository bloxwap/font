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
the normal face. The italic is in the same family but isn't preloaded: a page downloads it only when it renders italic text.
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

One family name per style covers every script. Each companion is also available under its own name (for example
`"Bloxwap Sans Arabic"`). The WOFF2 files are at `@bloxwap/font/fonts/<Family>/<Family>-Variable.woff2` (and `-Italic-Variable.woff2`).

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
  their unique registration name and variable source hash.
- `@bloxwap/font/css/{sans,mono,pixel}`: one role with its companions.
- `@bloxwap/font/css/{sans,mono}-core` and `pixel-core`: core only.
- `@bloxwap/font/css/{sans,mono}-{arabic,hebrew,armenian,georgian,jp,kr,sc}`:
  script only, retaining unicode-range and swap behavior.
- `@bloxwap/font/native/BloxwapSans` (or another published family): typed Metro
  asset map, e.g. `faces['BloxwapSans-SemiBold']`. Register only selected TTFs;
  use their exact keys as fontFamily with no fontWeight/fontStyle override.
  Static Pixel pins ROND to 50. All nine weights and available italics are included.

Read [Cross-platform typography](https://bloxwap.github.io/font/docs/cross-platform/)
for Next.js and Expo recipes, locale selection, scaling, licensing and limitations.
`npm test` checks the manifest against the actual built files and binary metadata.
Physical native rendering still requires host/device validation.
