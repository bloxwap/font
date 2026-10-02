<h1 align="center">Bloxwap Font</h1>

<p align="center">
  <strong>Rounded, open-source typefaces for interfaces, code and screens.<br>Drawn from scratch, in the spirit of Inter and Geist.
  <a href="https://bloxwap.github.io/font/">Try the type tester</a>.</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@bloxwap/font"><img alt="npm version" src="https://img.shields.io/npm/v/@bloxwap/font?color=blue&style=flat-square"></a>
  <a href="https://github.com/bloxwap/font/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/bloxwap/font?color=blue&style=flat-square"></a>
  <a href="https://github.com/bloxwap/font/releases"><img alt="Release downloads" src="https://img.shields.io/github/downloads/bloxwap/font/total?style=flat-square"></a>
  <a href="https://github.com/bloxwap/font/actions/workflows/docs.yml"><img alt="Docs build" src="https://img.shields.io/github/actions/workflow/status/bloxwap/font/docs.yml?branch=main&amp;label=docs&amp;style=flat-square"></a>
  <a href="LICENSE"><img alt="License: OFL-1.1" src="https://img.shields.io/badge/license-OFL--1.1-blue?style=flat-square"></a>
</p>

| Family | For | Axes |
|---|---|---|
| **Bloxwap Sans** | Interfaces and text | `wght` 100–900 · italics |
| **Bloxwap Mono** | Code and terminals, with code ligatures | `wght` 100–900 · italics |
| **Bloxwap Pixel** | Displays, tickers, game-like moments | `wght` 100–900 · `ROND` 0–100 · italics |
| **Sans / Mono Arabic** | Arabic, Persian, Urdu, Pashto, Kurdish, Sindhi, Uyghur, Jawi… | `wght` 100–900 |
| **Sans / Mono Armenian** | Armenian, proportioned for multilingual text | `wght` 100–900 · italics |
| **Sans / Mono Georgian** | Mkhedruli and Mtavruli uppercase | `wght` 100–900 · italics |
| **Sans / Mono Hebrew** | Hebrew and full Niqqud | `wght` 100–900 |
| **Sans / Mono JP** | Japanese kana and Jōyō kanji | `wght` 100–900 |
| **Sans / Mono KR** | Korean (all 11,172 Hangul syllables) | `wght` 100–900 |
| **Sans / Mono SC** | Simplified Chinese (3,500 standard characters) | `wght` 100–900 |

17 families · 11 scripts · 19,311 characters · 656 languages · 216 static + 24 variable fonts
(OTF, TTF, WOFF2, WOFF) · OFL-1.1.

## Use

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

One family name covers every script: the stylesheet loads companions with
`unicode-range` only when a page uses them. Armenian and Georgian have italics;
Arabic and Hebrew include mark positioning for joined and pointed text.
Downloads: [latest release](https://github.com/bloxwap/font/releases/latest). Self-hosting: [Installation](https://bloxwap.github.io/font/docs/installation/).

## Develop

```sh
bun install
bun run docs:dev        # website on http://localhost:3904
bun run fonts:setup     # Python 3.12 toolchain (uv) for the font build
bun run fonts:build     # build every family into packages/font/fonts and the website
```

| Path | |
|---|---|
| [`apps/docs`](apps/docs) | The website (Fumadocs + Next.js, static export) |
| [`packages/font`](packages/font) | The type design: skeleton glyph source and build tools |
| [`packages/npm`](packages/npm) | The `@bloxwap/font` npm package (web fonts, `next/font` exports, CSS) |

## License

[SIL Open Font License 1.1](LICENSE). © 2026 Bloxwap, Inc. Clean-room: no
outlines were copied, traced or derived from any other font.
