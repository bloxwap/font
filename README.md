# Bloxwap Font

Rounded, clean, open-source typefaces from Bloxwap, Inc. — in the spirit of
Inter and Geist, drawn from scratch.

**[bloxwap.github.io/font](https://bloxwap.github.io/font/)** — specimen, type tester, glyph browser and docs.

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

```css
@import url("https://bloxwap.github.io/font/bloxwap-font.css");

body { font-family: "Bloxwap Sans", system-ui, sans-serif; }
code { font-family: "Bloxwap Mono", ui-monospace, monospace; }
```

One family name covers every script: the stylesheet loads companions with
`unicode-range` only when a page uses them. Armenian and Georgian have italics;
Arabic and Hebrew include mark positioning for joined and pointed text.
Downloads and self-hosting: [Installation](https://bloxwap.github.io/font/docs/installation/).

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

## License

[SIL Open Font License 1.1](LICENSE). © 2026 Bloxwap, Inc. Clean-room: no
outlines were copied, traced or derived from any other font.
