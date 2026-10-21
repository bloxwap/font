<h1 align="center">Bloxwap Font</h1>

<p align="center">
  <strong>Rounded, open-source typefaces for interfaces, code and screens.<br>Drawn from scratch, in the spirit of Inter and Geist.
  <a href="https://bloxwap.github.io/font/">Try the type tester</a>.</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@bloxwap/font"><img src="https://img.shields.io/npm/v/@bloxwap/font?style=flat-square" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/@bloxwap/font"><img src="https://img.shields.io/npm/dm/@bloxwap/font?style=flat-square" alt="npm downloads"></a>
  <a href="https://github.com/bloxwap/font/releases"><img src="https://img.shields.io/github/v/release/bloxwap/font?style=flat-square" alt="release"></a>
  <a href="https://openfontlicense.org/"><img src="https://img.shields.io/badge/license-OFL--1.1-blue?style=flat-square" alt="license"></a>
</p>

## Features

- **Three type families.** Sans for interfaces and text, Mono for code with ligatures, and Pixel for displays and game-like moments, all with matching proportions and weights.
- **11 scripts, 656 languages.** Multilingual companions for Arabic, Armenian, Georgian, Hebrew, Japanese, Korean, and Simplified Chinese. Armenian and Georgian include italics; Arabic and Hebrew include mark positioning for joined and pointed text.
- **Variable and static fonts.** 24 variable fonts (wght 100-900, italics where applicable, and ROND 0-100 for Pixel) plus 216 static weights. Available as OTF, TTF, WOFF2, and WOFF.
- **Clean-room design.** All 19,311 characters drawn from scratch, in the spirit of Inter and Geist. No outlines copied, traced, or derived from any other font.

| Family | For | Axes |
|---|---|---|
| **Bloxwap Sans** | Interfaces and text | `wght` 100-900 · italics |
| **Bloxwap Mono** | Code and terminals, with code ligatures | `wght` 100-900 · italics |
| **Bloxwap Pixel** | Displays, tickers, game-like moments | `wght` 100-900 · `ROND` 0-100 · italics |
| **Sans / Mono Arabic** | Arabic, Persian, Urdu, Pashto, Kurdish, Sindhi, Uyghur, Jawi… | `wght` 100-900 |
| **Sans / Mono Armenian** | Armenian, proportioned for multilingual text | `wght` 100-900 · italics |
| **Sans / Mono Georgian** | Mkhedruli and Mtavruli uppercase | `wght` 100-900 · italics |
| **Sans / Mono Hebrew** | Hebrew and full Niqqud | `wght` 100-900 |
| **Sans / Mono JP** | Japanese kana and Jōyō kanji | `wght` 100-900 |
| **Sans / Mono KR** | Korean (all 11,172 Hangul syllables) | `wght` 100-900 |
| **Sans / Mono SC** | Simplified Chinese (3,500 standard characters) | `wght` 100-900 |

## Installation

```sh
npm install @bloxwap/font
```

```tsx
import { BloxwapSans } from '@bloxwap/font/sans';   // next/font: .className, .variable (--font-bloxwap-sans)
import '@bloxwap/font/css';                         // or plain CSS: "Bloxwap Sans", "Bloxwap Mono", "Bloxwap Pixel"
```

Or link the hosted stylesheet:

```css
@import url("https://bloxwap.github.io/font/bloxwap-font.css");

body { font-family: "Bloxwap Sans", system-ui, sans-serif; }
code { font-family: "Bloxwap Mono", ui-monospace, monospace; }
```

One family name covers every script: the stylesheet loads companions with `unicode-range` only when a page uses them. Downloads: [latest release](https://github.com/bloxwap/font/releases/latest). Self-hosting: [Installation](https://bloxwap.github.io/font/docs/installation/).

For Expo and React Native, the 0.1.3 candidate uses opt-in packages:

```sh
npm install @bloxwap/font-native
# Add script companions only when needed, for example @bloxwap/font-native-jp.
```

Import selected TTFs from `@bloxwap/font-native/assets/BloxwapSans/BloxwapSans-Regular.ttf`
or a complete family map from `@bloxwap/font-native/BloxwapSans`. See
[Cross-platform typography](https://bloxwap.github.io/font/docs/cross-platform/) for registration.
The web package includes the full manifest; native binaries ship in the opt-in packages.

## Release status

`0.1.2` is an early developer preview; expect breaking changes before `1.0`.

## Documentation

Guides, glyph charts, and the type tester: **https://bloxwap.github.io/font/**

## Development

This repository is a workspace: the type design and build tools live in [`packages/font`](packages/font), the `@bloxwap/font` npm package in [`packages/npm`](packages/npm), opt-in native packages in [`packages/native`](packages/native), and the documentation site in [`apps/docs`](apps/docs).

```sh
bun install
bun run fonts:setup     # Python 3.12 toolchain (uv) for the font build
bun run fonts:build     # build every family into packages/font/fonts and the website
bun run dev             # docs and type tester at http://localhost:3904
```

Static web fonts ship in the per-family release zips; Pages and Git track only variable WOFF2s. Native package builds verify local dist sources or download hash-pinned public release zips using `packages/npm/static-sources.json`. Commit that lock with font rebuilds, as described in [Building from source](apps/docs/content/docs/building.mdx).

Requires Bun. Font build requires Python 3.12 or newer and depends on [fontmake](https://github.com/googlefonts/fontmake), [fonttools](https://github.com/fonttools/fonttools), and [uv](https://docs.astral.sh/uv/).

With the docs running, check glyph copy identity, accessible control names, keyboard access, replacement fonts and text-spacing reflow:

```sh
DOCS_URL=http://localhost:3904/ bun run docs:accessibility
```

The browser suite runs in Chromium and WebKit. Its 320 px viewport and 200% root text size checks complement manual browser zoom and screen-reader testing. For font raster previews and Unicode QA, see [Readability and text integrity](packages/font/DESIGN.md#readability-and-text-integrity).

The [benchmark harness](bench/README.md) measures font builds, docs builds and each npm package.
For a static export, run `bun run docs:build`, `bun run docs:preview`, then `DOCS_URL=http://localhost:3904/ bun run docs:smoke` in another terminal. This also checks the home page's 250 KB HTML budget and lazy feature/file details. See [Building from source](apps/docs/content/docs/building.mdx) for base-path setup and the client data boundaries.

## License

[SIL Open Font License 1.1](https://openfontlicense.org/). © 2026 Bloxwap, Inc. Clean-room: no outlines were copied, traced or derived from any other font.
