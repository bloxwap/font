# Bloxwap Sans SC — Han (CJK ideograph) contributor guide

Clean-room rule: never open, trace or measure any existing CJK font or
glyph outline, and don't import decomposition databases (CHISE, cjkvi-ids,
BabelStone IDS, Make Me a Hanzi, KanjiVG…). Decompositions and drawings are
written from our own knowledge. Unicode's Unihan data (stroke counts,
radicals, the 通用规范汉字表 index) is used for verification only.

Target: 通用规范汉字表 level 1 — the 3,500 characters in
`tools/bwfont/han/unihan_tgh.tsv` with index ≤ 3500, in **Simplified Chinese
(PRC GB/通用规范) glyph forms**.

## How characters are built

`tools/bwfont/han/engine.py` resolves each character through its IDS
(Ideographic Description Sequence) down to *atomic components*, lays the
components out in boxes, and strokes their skeletons with the family pen.
Because strokes are re-drawn after scaling, a component squeezed into a
narrow slot keeps its weight. Rounded Hei/圆体 style: monoline, round ends,
round corners — all automatic.

## 1. Decompositions — `tools/bwfont/han/ids_*.txt`

One line per character or intermediate component: `char<TAB>IDS`.

```
明	⿰日月
想	⿱相心
相	⿰木目
```

* Operators: ⿰ left-right, ⿱ top-bottom, ⿲ ⿳ three parts, ⿴ full surround,
  ⿵ open below (冂 门), ⿶ open above (凵), ⿷ open right (匚), ⿸ upper-left
  (广 厂 尸 疒), ⿹ upper-right (勹 戈 气 可's 丁), ⿺ lower-left (辶 廴 走),
  ⿻ overlay (use sparingly).
* Decompose down to components that exist (or will exist) in the
  component library. Intermediate components (相, 尔, 青 …) get their own
  lines. Recursion is resolved automatically.
* Use simplified-form radicals: 讠 饣 纟 钅 门 贝 见 车 马 鱼 鸟 页 风 …
* Use positional forms by name where shapes differ: 亻 氵 扌 忄 艹 宀 冖 灬
  罒 刂 阝 礻 衤 犭 彳 攵 辶 疒 …
* Unencoded parts: write them as `{name}` inside IDS (e.g. `⿱{兑上}口`), declare
  their stroke counts in a comment line: `# {兑上}=4  two dots over 口`.
  Comment lines start with `# `; a component library entry for an unencoded
  part is named the same way: `comp("{兑上}", ...)`.
* Verify stroke counts against Unihan (must match):
  `.venv/bin/python tools/han_check.py --ids-only --range 1-1750`

## 2. Components — `tools/bwfont/han/components_*.py`

```python
from .engine import comp

comp("口", "M0 0 L0 1000", "M0 0 L1000 0 L1000 1000", "M0 1000 L1000 1000",
     solo=(0.7, 0.66))
comp("木.L", "M0 280 L1000 280", "M560 0 L560 1000", "M540 300 Q360 600 0 820",
     "M600 420 L900 600", share={"L": 0.36})
comp("囗", "M0 0 L0 1000", "M0 0 L1000 0 L1000 1000", "M0 1000 L1000 1000",
     inner={"⿴": (190, 190, 810, 810)})
```

* 1000×1000 box, **SVG convention: x right, y DOWN**. Draw the skeleton
  (centre-line) to the box edges where the component's ink should reach
  the edge of its slot; the engine insets for the pen.
* **One string = one calligraphic stroke** (横折钩 is one stroke), as SVG
  path data with absolute `M L Q C`. The number of strings must equal the
  stroke count (it is verified against Unihan).
* Corners (`L` then `L` at an angle) become rounded joins; use `Q`/`C`
  for 撇 (left-falling), 捺 (right-falling), 弯钩 etc. Hooks are short final
  segments. Dots (点) are short diagonal lines (~120–200 units).
* `solo=(sx, sy)`: size when the component is a whole character (口 is
  small, 一 is flat…). `inner={op: (x0, y0, x1, y1)}` (y-down) for
  enclosure components. `share={"L": 0.3}` preferred fraction of the slot.
* Positional variants: name them `X.L` `X.R` `X.T` `X.B` `X.M` `X.O`
  (outer of an enclosure) — e.g. `木.L` (narrow, 捺 becomes a dot),
  `土.L` (bottom stroke becomes 提), `心.B`, `口.L`, `日.L`, `目.L`, `月.L`,
  `火.L`, `米.L`, `禾.L`, `王.L`, `女.L`, `子.L`, `石.L`, `马.L`, `车.L`,
  `足.L`, `贝.L`… The engine picks them automatically by position.
* Ownership: components are partitioned among contributors by the Kangxi
  radical of the component character (`engine.radical_of(ch)`); components
  without a character (or with no radical data) follow the radical they
  look like. Only edit your own `components_*.py` file.

## 3. Check & look

```bash
.venv/bin/python tools/han_check.py                        # coverage + stroke-count check
.venv/bin/python tools/han_check.py --sheet out.png --chars 明想林河 --stems 22,84,180
```

Look at the sheets: characters must be balanced (no collisions, even
spacing, correct proportions of left/right and top/bottom parts) and read
correctly to a Chinese reader.

## Japanese (Bloxwap Sans JP / Mono JP)

Target: the 2,136 Jōyō kanji (`tools/bwfont/han/unihan_joyo.tsv`) in Japanese
shinjitai glyph forms, plus kana (`tools/bwfont/glyphs/kana.py`).

* Characters shared with the SC set use the shared data. Japanese-only code
  points (説 図 円 動 間 東 …) and anything whose Japanese structure differs
  get lines in `tools/bwfont/han/ids_jp*.txt` — the **jp layer**, which
  overrides the shared decompositions for the JP families only.
* Japanese uses full-form radicals where Simplified Chinese simplifies them:
  言 糸 金 食(飠) 門 貝 見 車 馬 魚 鳥 頁 長 韋 東 … Write IDS with those
  characters (e.g. `説	⿰言兑`, `間	⿵門日`); components are drawn under their
  own code points with positional forms (`言.L`, `糸.L`, `金.L`, `飠`, `貝.L`,
  `車.L`, `馬.L`, `魚.L`, `見.R`, `頁.R`, `鳥.R`, `門` with `inner`).
* Where a shared code point should look different in Japanese, draw a
  regional component named `<char>@jp` (e.g. `直@jp`); the jp layer prefers it.
* ⻌ (shinnyō) is the one-dot form (3 strokes) like PRC 辶 — reuse 辶.
* Verify: `.venv/bin/python tools/han_check.py --jp --ids-only` (stroke counts
  vs Unihan), `--jp --radicals a-b` (undrawn leaves), `--jp --sheet out.png --chars 説図円`.
