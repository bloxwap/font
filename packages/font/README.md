# @bloxwap/font-source

The type design and build for Bloxwap Sans, Mono and Pixel and their Arabic,
Armenian, Georgian, Hebrew, Japanese (JP), Korean (KR) and Simplified Chinese (SC) companions.

## Commands

From the repository root (or `bun run <script>` in this directory):

| Command | What it does |
|---|---|
| `bun run fonts:setup` | Create `.venv` (Python 3.12 via [uv](https://docs.astral.sh/uv/)) from `requirements.txt` |
| `bun run fonts:build` | Build every family; `bun run fonts:build sans mono` for selected ones |
| `bun run fonts:web` | Re-package existing builds for the website (`apps/docs/public`) |
| `bun run fonts:check` | Master compatibility + folded-stroke checks |
| `bun run fonts:qa` | OpenType Sanitizer on every file, language coverage, script shaping and mark/italic checks |
| `bun run fonts:release` | Upload the download zips to the GitHub Release for the current version |

`JOBS` limits one shared pool for source generation, variable builds, instance
generation and static compiles across all requested families. It defaults to
`nproc` on Linux or `sysctl -n hw.ncpu` on macOS. For example,
`JOBS=4 bun run fonts:build pixel` uses at most four compile processes. The pool
starts SC, JP and KR first, then other companions, then Sans, Mono and Pixel,
and reports `max concurrency: N (JOBS=J)` when it finishes. Lower `JOBS` to fit
available memory, especially for CJK and Pixel builds.

Post-processing regenerates site data only for the requested families and keeps
the other families' summaries. `tools/site_data.py` uses a process pool (CPU count
by default, overridden with `SITE_DATA_JOBS`) and caches successful Hyperglot
language results in `.hyperglot-cache/`, keyed by font SHA-256 and Hyperglot
version. Deleting that ignored directory forces fresh language analysis.

Run the pipeline regression checks with
`.venv/bin/python -m unittest discover -s tools -p 'test_*.py'` from this directory.

## Layout

```text
tools/bwfont/           the design
  skeleton.py           glyph drawing DSL (centre-line skeletons)
  geometry.py           stroker: elliptical pen, round caps, structural plans
  glyphs/               glyph modules (Latin, Greek, Cyrillic, symbols, Arabic, Hangul, Han …)
  han/                  CJK ideograph engine, components and IDS decompositions
  hangul/  arabic/      Hangul jamo engine, Arabic rasm × joining-form kit
  pixel/                Bloxwap Pixel bitmaps and generator
  families.py           the family catalog: packs, axes, metrics
tools/generate.py       skeletons → UFO masters + designspaces (sources/)
tools/build_all.sh      shared build pool → postprocess
tools/build_pool.py     bounded generation + variable/instance/static compilation
tools/postprocess.py    hinting, WOFF/WOFF2, fonts/ distribution, website copies and zips
fonts/                  the distribution: <Family>/{variable,otf,ttf,woff2,woff} (generated, ignored)
```

`build/`, `sources/` and `fonts/` are generated (and ignored); the zips ship as GitHub Release assets.

## Design

Every glyph is a skeleton drawn in Python and expanded with an elliptical pen
into round-capped outlines, so all masters (Thin/Regular/Black × upright/italic)
come from the same code and stay point-compatible. Accented letters, script
look-alikes, small caps and numerals are derived automatically.

- [DESIGN.md](DESIGN.md): drawing API, metrics and style rules
- [HAN.md](HAN.md): how Chinese characters are composed from stroke-drawn components
  following our own IDS decompositions (verified against Unihan stroke counts)

Design tools (run here):

```sh
.venv/bin/python tools/check_glyphs.py [module]
.venv/bin/python tools/check_cusps.py [module]
.venv/bin/python tools/check_scripts.py  # compiled companions: coverage, shaping, spacing, web faces
.venv/bin/python tools/dev_preview.py out.png "Hamburg" --stems 22,84,180
.venv/bin/python tools/han_check.py --sheet out.png --chars 明想林河
.venv/bin/python tools/render.py "fonts/BloxwapSans/variable/BloxwapSans[wght].ttf" out.png "Text" --wghts 100,400,900
```

Unihan data in `tools/bwfont/han/*.tsv` is © Unicode, Inc. (Unicode License v3).
