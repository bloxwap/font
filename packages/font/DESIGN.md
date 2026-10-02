# Bloxwap type system — design & contribution guide

Clean-room: every outline is generated from our own skeleton code. Never
open, trace, measure or copy outlines from any existing font (Inter, Geist,
SF, Nunito, Maple, …). Those are cited only as *spirit* references.

## Families

| Family         | What                                                     | Source                     |
|----------------|----------------------------------------------------------|----------------------------|
| Bloxwap Sans   | Rounded neo-grotesk, proportional, 9 weights + italics   | `tools/bwfont/glyphs/*.py` |
| Bloxwap Mono   | Same skeletons, 600-unit cell, slabbed narrow letters    | same files (`g.mono`)      |
| Bloxwap Pixel  | Bitmap-grid display face, rounded "pixels"               | `tools/bwfont/pixel/`      |

## Pipeline

```
glyph skeleton functions ──► stroker (elliptical pen, round caps) ──► outlines
   ──► auto spacing ──► composites (accents, aliases) ──► UFO masters
   ──► designspace (wght 100–900 + ital) ──► fontmake ──► OTF/TTF/WOFF2/VF
```

Masters: Thin (stem 22), Regular (84), Black (180), upright + italic (9° shear
applied to skeletons, so italic strokes keep their weight).

## Metrics (UPM 1000)

| name | value | | name | value |
|---|---|---|---|---|
| x-height `g.xh` | 540 | | cap `g.cap` | 720 |
| ascender `g.asc` | 760 | | descender `g.desc` | −210 |
| overshoot `g.ov` | 10 | | Mono advance | 600 |

Stem `g.W` = 22…180 (Regular 84). Horizontal thickness `g.H ≈ 0.8·W + 3`
(contrast comes automatically from the elliptical pen: vertical strokes are W
thick, horizontal strokes H thick). `g.hw = W/2`, `g.hh = H/2`.
`g.grow = W − 84` (negative for Thin): use it to widen shapes with weight.

## Drawing API (`tools/bwfont/skeleton.py`)

```python
from ..skeleton import glyph, derive, G, mirror_x, mirror_y, shift, scale_about

@glyph("n", 0x6E, zone="lc")          # name, unicodes…, zone: lc|uc|fig|auto
def n(g: G):
    bw = g.wd(436, 456)               # body (ink) width: sans value, mono value; grows with weight
    g.stem(0, 0, g.xh)                # stem with LEFT ink edge at x, ink spanning y0..y1
    (g.pen(g.hw, 300, 0.52)           # start a smooth stroke at skeleton point, width factor 0.52
        .v(240, g.xh - g.hh, w=1.0)   # quarter curve: leave vertically, arrive horizontally
        .h(bw - g.hw, 250)            # quarter curve: leave horizontally, arrive vertically
        .l(bw - g.hw, g.hh)           # straight line
        .end())                       # round caps (or .end("butt"))
```

Pen path methods (all return the path; coordinates are *skeleton* =
centre-line positions):

* `.l(x, y, w=None)` line · `.c(c1, c2, p, w=None)` raw cubic
* `.h(x, y, k=None, w=None)` / `.v(…)` quarter curves (k = tension, default 0.58; 0.55 ≈ circle, 0.62 squarer)
* `.to(x, y, d0, d1, k=None, w=None)` curve with explicit unit tangents
  (`"r" "l" "u" "d"` or a vector) at start/end
* `.end(caps=("round","round"))` open stroke · `.close()` closed loop
* `w` = width factor at that node (1.0 = full pen). Width interpolates smoothly along the segment.

Builder helpers (outer = *ink* coordinates, inset automatically):

* `g.stem(x_left_ink, y0, y1, w=1)`, `g.vstem(cx, y0, y1)` vertical stems
* `g.bar(x0, x1, cy, w=1)` horizontal bar (ink x0..x1, centred on cy)
* `g.line(x0, y0, x1, y1, w0=1, w1=None, caps=…)` skeleton line
* `g.oval(x0, y0, x1, y1, k=None, w=1)` closed oval from its ink box
* `g.dot(cx, cy, d=None)` round dot (default diameter ≈ 1.16·W + 10)
* `g.include("name", fn=None)` draw another glyph's skeleton (optionally transformed)
* `g.transform(fn)` … draw … `g.transform(None)` — transform subsequent strokes (e.g. `mirror_x(bw/2)`)
* `derive(name, *unicodes, src=, sx=, sy=, dx=, dy=, wscale=)` — new glyph from a *skeleton transform*
  of another (weight re-applied, so small caps / superiors keep good colour)
* Spacing: automatic (HT-letterspacer-like). Override with `g.lsb`, `g.rsb`,
  `g.sb = {"l": +10, "r": -5, "scale": 1.1}`, or fixed `g.advance` (ink is centred).
* `g.anchor(name, x, y)` — defaults are computed from the ink box; set explicitly
  when needed. Names: `top bottom ogonek horn center caron dotright`.

## Style rules

1. **Rounded**: every terminal is a round cap. No flat cuts, no spurs, no ink traps.
2. **Corners are separate strokes**. One `pen()` path must be tangent-continuous;
   where two strokes meet at an angle (A apex, k junction, v vertex) draw two
   strokes — their round caps form the rounded join.
3. **Bowls and arches ride the stem** (no tapered joins): never start or end a bowl
   or arch *on* a stem with a thin taper — that leaves lobes beside the stem and dents in
   the counter. A **bowl** is a complete closed round (`bowl_left()` / `loop()` in
   `latin_lower.py`, or `g.oval`) whose side lies on the stem's centre-line (`EPS`
   inside it): the stem overlaps it, the counter is one smooth round, and clean notches
   form where the bowl leaves the stem (see `d_six()` in `figures.py`). An **arch,
   shoulder or hook** springing from a stem first rides up the stem's centre-line for a
   short straight run (width `LEAD`), then peels away tangentially (`arch()`, `r`), so
   the counter has no lump or square corner. Where a loop turns into a stem keep the
   corner radius above the pen radius at every weight (scale it with `g.hw`); straight
   runs must be > 0 in every master (or 0 in all). `JOIN` (0.52) is legacy.
4. Diagonals use width factor ~0.92 so they don't look heavier than stems.
5. Curves are smooth and round, Nunito-like. Write tensions on the usual scale
   (k 0.58–0.62); `soften()` in `skeleton.py` pulls everything above a circular
   quarter (0.552) toward it, keeping `SQUARENESS` (0.15) of the difference. Tensions
   ≤ 0.552 pass through unchanged. Apertures open (terminals of c/e/s/a around
   0.2–0.25·h from the extremes).
6. Overshoot: round tops/bottoms go `g.ov` beyond baseline / x-height / cap height.
7. **Weight-independent topology**: never branch on `g.W` / `g.grow`; the same code
   must yield the same strokes for every master. Positions may depend on W linearly.
   Branching on `g.mono` is fine.
8. Widths grow with weight: `g.wd(sans, mono, grow=0.5)` adds `grow·(W−84)`.
9. **Mono**: everything sits in a 600-unit cell; regular ink width ≲ 470.
   Narrow letters get rounded slabs (see `i l r j` in `latin_lower.py`);
   wide letters (M W m w) are condensed and may use `w=0.84–0.9` strokes.
10. Reference proportions (Regular, ink widths): n 436, o 478, H ≈ 540, O ≈ 640,
    E ≈ 440, M ≈ 660, W ≈ 860, figures ≈ 470 (tabular default).
11. **Minimal flourish**: no decorative tails where a straight stroke reads (the y
    descender is a straight diagonal; its old curled tail lives in ss04). Keep forms
    simple so they hold up at small sizes.

## Naming & encoding

* Glyph names: AGL-style for Latin (`A`, `Aogonek`, `eth`, `germandbls`), otherwise `uniXXXX`.
  Greek uses AGL names (`Gamma`, `alpha` …); Cyrillic uses `uni04XX`.
* Accented letters are **not drawn**: `composites.py` builds them from NFD
  decompositions + marks. Script look-alikes (Greek Α, Cyrillic А, …) are aliases —
  see `ALIASES` in `composites.py`; don't redraw them.
* Variants by suffix (features are generated automatically): `.ss01…ss20`, `.cv01…`,
  `.pnum`, `.zero`, `.sups .subs .numr .dnom`, `.case`, `.sc`, `.loclSRB/.loclBGR`,
  ligatures `a_b` (Sans `liga`), `a_b.code` (Mono `calt` code ligatures).

## Verify your work

```bash
.venv/bin/python tools/check_glyphs.py <module>          # must report 0 problems
.venv/bin/python tools/dev_preview.py out.png "HOHOH nonon" --stems 22,84,180
.venv/bin/python tools/dev_preview.py out.png "text" --family mono --stems 84
.venv/bin/python tools/dev_preview.py out.png "text" --slant 9
.venv/bin/python tools/dev_preview.py out.png --outline A --stems 84   # big view with points
```

Look at every preview (they are PNGs) and iterate until the shapes are right.

## Readability and text integrity

Sans capital I uses rounded horizontal bars by default to distinguish it from
lowercase l. Its wider advance also affects accented I and script aliases that
reuse its skeleton; rebuild every Sans companion after changing this glyph.
Keep optional disambiguation (`ss08`) and slashed zero (`zero`) available for
identifiers. Mono retains its slabbed I and hooked l.

After compiling, render the shipped fonts at actual UI sizes and every named
weight, upright and italic:

```bash
.venv/bin/python tools/readability_preview.py --out /tmp/bloxwap-readability
.venv/bin/python tools/readability_preview.py --out /tmp/bloxwap-readability --italic
.venv/bin/python tools/readability_preview.py --out /tmp/bloxwap-readability/variable --variable-only
.venv/bin/python tools/readability_preview.py --out /tmp/bloxwap-readability/scripts --scripts-only
.venv/bin/python tools/check_unicode.py
```

Review `Il1`, `0O`, `rn/m`, `cl/d`, counters in `aceos`, punctuation, and accents
at 12, 16, 20 and 24 px. Check that details remain visible and neighboring
letters remain separate. Thin and Black are stress cases, not recommended body
weights. Pixel is a display face: start at 20 px and verify the actual weight
and roundness. FreeType previews are a review aid; also check target browsers
and screens. They do not establish accessibility conformance or replace reader
testing. Review the variable sheets too: the website uses variable fonts, whose
rasterization can differ from the hinted static faces. Pixel's variable review
includes roundness 0, 50 and 100 at weights 400 and 900.
The script sheets sample all 17 families at 16 and 24 px with
Thin, Regular and Black, including Arabic joining, Hebrew niqqud and CJK
forms. Verify the relevant languages with native readers; sample coverage and
successful shaping do not establish readability across the full repertoire.

Preserve each character's Unicode identity even when script look-alikes share
an outline. Keep stylistic glyphs unencoded and reach them through OpenType
features. Ligatures must retain their original source sequences in the website
tester and clipboard. Labels should describe Unicode names and code points,
not guess a character from its appearance.
