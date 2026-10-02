"""Combining marks (pixel versions).

Top marks are drawn for lowercase: x-height top is row 4, row 5 stays empty
(one-row gap) and the mark occupies rows 6–8.  `_top` sits at (300, 500).
`.case` variants (over capitals and ascenders) are the same bitmaps two rows
higher (rows 8–10, `_top` at (300, 700)); a few get a compact two-row design.
Two rows = exactly one italic step, so marks stay aligned in italics.

Bottom marks hang from (300, 0): row -1 is the gap, marks live in rows -2/-3
(cedilla & ogonek attach directly in row -1).
"""
from __future__ import annotations

import unicodedata

from . import art
from .art import PixelDef, add, parse, CELL

LC_TOP = 500
UC_TOP = 700

TOP_LC = """
:  acutecomb=U+0301 gravecomb=U+0300 circumflexcomb=U+0302 caroncomb=U+030C brevecomb=U+0306 invertedbrevecomb=U+0311 tildecomb=U+0303
8  .....            .....            .....                 .....             .....            .....                    .....
7  ...#.            .#...            ..#..                 .#.#.             #...#            .###.                    .##.#
6  ..#..            ..#..            .#.#.                 ..#..             .###.            #...#                    #.##.

:  macroncomb=U+0304 dotaccentcomb=U+0307 dieresiscomb=U+0308 ringcomb=U+030A hungarumlautcomb=U+030B dblgravecomb=U+030F hookabovecomb=U+0309
8  .....             .....                .....               ..#..           .....                   .....               .##..
7  .....             .....                .....               .#.#.           ..#.#                   #.#..               ...#.
6  .###.             ..#..                .#.#.               ..#..           .#.#.                   .#.#.               ..#..

:  verticallineabovecomb=U+030D commaturnedabovecomb=U+0312 commaabovecomb=U+0313 reversedcommaabovecomb=U+0314 perispomenicomb=U+0342 tonoscomb
8  .....                        ...#.                       ..##.                 .##..                         .....              .....
7  ..#..                        ..#..                       ...#.                 .#...                         .##.#              ...#.
6  ..#..                        ..##.                       ..#..                 ..#..                         #.##.              ..#..
"""

TOP_LC2 = """
:  overlinecomb=U+0305 dblverticallineabovecomb=U+030E candrabinducomb=U+0310 commaaboverightcomb=U+0315 leftangleabovecomb=U+031A xabovecomb=U+033D dbloverlinecomb=U+033F bridgeabovecomb=U+0346 dotaboverightcomb=U+0358 verticaltildecomb=U+033E zigzagabovecomb=U+035B
8 ..... ..... ..#.. ..... ..... .#.#. ##### ..... ..... ..#.. .....
7 ..... .#.#. #...# ....# ##... ..#.. ..... ##### ..... .#... .#.#.
6 ##### .#.#. .###. ...#. .#... .#.#. ##### #...# ....# ..#.. #.#.#
5 ..... ..... ..... ..... ..... ..... ..... ..... ..... ..... .....
"""

# compact two-row designs used over capitals (rows 8-9; ring hugs the cap)
TOP_CASE_OVERRIDES = """
:  ringcomb.case hookabovecomb.case commaturnedabovecomb.case commaabovecomb.case reversedcommaabovecomb.case
9  ..#..         .##..              ...#.                     ..##.               .##..
8  .#.#.         ...#.              ..##.                     ..#..               ..#..
7  ..#..         .....              .....                     .....               .....
"""

BOTTOM2 = """
:  gravebelowcomb=U+0316 acutebelowcomb=U+0317 lefttackbelowcomb=U+0318 righttackbelowcomb=U+0319 ringhalfleftbelowcomb=U+031C uptackbelowcomb=U+031D downtackbelowcomb=U+031E plusbelowcomb=U+031F minusbelowcomb=U+0320 bridgebelowcomb=U+032A caronbelowcomb=U+032C invertedbrevebelowcomb=U+032F dbllowlinecomb=U+0333 ringhalfrightbelowcomb=U+0339 invertedbridgebelowcomb=U+033A squarebelowcomb=U+033B seagullbelowcomb=U+033C equalbelowcomb=U+0347 dblverticallinebelowcomb=U+0348 xbelowcomb=U+0353 asteriskbelowcomb=U+0359 palatalhookbelowcomb=U+0321 retroflexhookbelowcomb=U+0322
-1 .....             .....             .....                .....                 .....                    .....                .....                  .....             .....              .....              .....             .....                     .....            .....                     .....                     .....            .....               .....             .....                    .....          .#.#.                ....#                      ..#..
-2 .#...             ...#.             .#...                ...#.                 .##..                    ..#..                .###.                  ..#..             .###.              #####              .#.#.             #...#                     #####            .##..                     #...#                     #####            #.#.#               #####             .#.#.                    .#.#.          ..#..                ...#.                      ..#..
-3 ..#..             ..#..             .##..                ..##.                 ..#..                    .###.                ..#..                  .###.             .....              #...#              ..#..             .###.                     .....            ..#..                     #####                     #...#            .#.#.               .....             .#.#.                    ..#..          .#.#.                ..##.                      ...##
-4 .....             .....             .....                .....                 .....                    .....                .....                  ..#..             .....              .....              .....             .....                     #####            .....                     .....                     #####            .....               #####             .....                    .#.#.          .....                .....                      .....
"""

CENTER2 = """
:  tildeoverlaycomb=U+0334 shortsolidusoverlaycomb=U+0337
4  .....                   ...#.
3  .##.#                   ..#..
2  #.##.                   .#...
"""

BOTTOM = """
:  dotbelowcomb=U+0323 dieresisbelowcomb=U+0324 ringbelowcomb=U+0325 commaaccentcomb=U+0326 cedillacomb=U+0327 circumflexbelowcomb=U+032D brevebelowcomb=U+032E
-1 .....               .....                    ..#..               .....                  ..#..              .....                  .....
-2 ..#..               .#.#.                    .#.#.               ..#..                  .##..              ..#..                  #...#
-3 .....               .....                    ..#..               .#...                  .....              .#.#.                  .###.

:  tildebelowcomb=U+0330 macronbelowcomb=U+0331 lowlinecomb=U+0332 verticallinebelowcomb=U+0329 ypogegrammenicomb=U+0345 ogonekcomb=U+0328
-1 .....                 .....                  .....              .....                       .....                   .#...
-2 .##.#                 .###.                  #####              ..#..                       ..#..                   ..##.
-3 #.##.                 .....                  .....              ..#..                       ...#.                   .....
"""

CENTER = """
:  strokeshortcomb=U+0335 strokelongcomb=U+0336 slashlongcomb=U+0338
6  .....                  .....                 ....#
5  .....                  .....                 ...#.
4  .....                  .....                 ...#.
3  .###.                  #####                 ..#..
2  .....                  .....                 .#...
1  .....                  .....                 .#...
0  .....                  .....                 #....
"""

OTHER = """
:  horncomb=U+031B caroncomb.alt
7 ..... .....
6 ...#. ..#..
5 ..#.. ..#..
4 ..... .#...
"""

# hand-made pairs (lowercase rows 6-8; .case = +2 rows)
COMBOS = """
:  circumflexcomb_acutecomb circumflexcomb_gravecomb circumflexcomb_hookabovecomb
8  ....#                    ...#.                    ...##
7  .#.#.                    .#..#                    .#..#
6  #.#..                    #.#..                    #.#..

:  commaabovecomb_tonoscomb commaabovecomb_gravecomb reversedcommaabovecomb_tonoscomb reversedcommaabovecomb_gravecomb
8  ##..#                    ##.#.                    ##..#                            ##.#.
7  .#.#.                    .#..#                    #..#.                            #...#
6  #....                    #....                    .#...                            .#...

:  commaabovecomb_perispomenicomb reversedcommaabovecomb_perispomenicomb dieresiscomb_tonoscomb dieresiscomb_gravecomb dieresiscomb_perispomenicomb
9  .##.#                          .##.#                                  .....                  .....                  .....
8  #.##.                          #.##.                                  ...#.                  .#...                  .##.#
7  ..##.                          .##..                                  ..#..                  ..#..                  #.##.
6  ..#..                          ..#..                                  .#.#.                  .#.#.                  .#.#.
"""


def _set_top_anchors(d: PixelDef, base_y):
    top = max(r for _, r in d.pix)
    d.anchors = {"_top": (300, base_y), "top": (300, (top + 1) * CELL)}


def _case_name(n):
    return n + ".case"


def stack(lower: str, upper: str):
    """Pixels of `upper` sitting directly on top of `lower` (no gap)."""
    lo = art.REG[lower].pix
    up = art.REG[upper].pix
    lo_top = max(r for _, r in lo)
    up_bot = min(r for _, r in up)
    d = lo_top + 1 - up_bot
    return set(lo) | {(x, r + d) for x, r in up}


def register():
    parse(TOP_LC, kind="mark")
    parse(TOP_LC2, kind="mark")
    lc_top = [n for n in art.ORDER if art.REG[n].kind == "mark"]
    for n in lc_top:
        _set_top_anchors(art.REG[n], LC_TOP)
    parse(TOP_CASE_OVERRIDES, kind="mark")
    for n in ("ringcomb.case", "hookabovecomb.case", "commaturnedabovecomb.case",
              "commaabovecomb.case", "reversedcommaabovecomb.case"):
        _set_top_anchors(art.REG[n], UC_TOP)
    for n in lc_top:
        cn = _case_name(n)
        if cn in art.REG:
            continue
        d = art.REG[n]
        add(PixelDef(cn, [], {(x, r + 2) for x, r in d.pix}, kind="mark"))
        _set_top_anchors(art.REG[cn], UC_TOP)

    before = set(art.REG)
    parse(BOTTOM, kind="mark")
    parse(BOTTOM2, kind="mark")
    for n in set(art.REG) - before:
        d = art.REG[n]
        low = min(r for _, r in d.pix)
        if n == "ogonekcomb":
            d.anchors = {"_ogonek": (300, 0)}
        else:
            d.anchors = {"_bottom": (300, 0), "bottom": (300, low * CELL)}

    before = set(art.REG)
    parse(CENTER, kind="mark")
    parse(CENTER2, kind="mark")
    for n in set(art.REG) - before:
        art.REG[n].anchors = {"_center": (300, 350)}

    parse(OTHER, kind="mark")
    art.REG["horncomb"].anchors = {"_horn": (300, 500)}
    art.REG["caroncomb.alt"].anchors = {"_caron": (300, 700)}

    # combination marks
    before = set(art.REG)
    parse(COMBOS, kind="mark")
    for n in sorted(set(art.REG) - before):
        _set_top_anchors(art.REG[n], LC_TOP)
        d = art.REG[n]
        cn = _case_name(n)
        add(PixelDef(cn, [], {(x, r + 2) for x, r in d.pix}, kind="mark"))
        _set_top_anchors(art.REG[cn], UC_TOP)
    _auto_combos()
    # canonical-equivalent / look-alike marks as components
    for cp, src in ((0x340, "gravecomb"), (0x341, "acutecomb"), (0x343, "commaabovecomb"),
                    (0x344, "dieresiscomb_tonoscomb")):
        d = art.REG[src]
        add(PixelDef(art.name_for(cp), [cp], set(d.pix), kind="mark", anchors=dict(d.anchors)))
    add(PixelDef(art.name_for(0x34F), [0x34F], set(), kind="mark", advance=0))


def _auto_combos():
    """Stacked top-mark pairs that occur in target decompositions."""
    from .. import composites as comp
    pairs = set()
    for cp in comp.target_codepoints():
        nfd = unicodedata.normalize("NFD", chr(cp))
        if len(nfd) < 3:
            continue
        greek = 0x370 <= ord(nfd[0]) <= 0x3FF or 0x1F00 <= ord(nfd[0]) <= 0x1FFF
        ms = []
        for c in nfd[1:]:
            m = comp.MARKS.get(ord(c))
            if m is None:
                break
            name, a = m
            if greek and name == "acutecomb":
                name = "tonoscomb"
            ms.append((name, a))
        for (a, aa), (b, bb) in zip(ms, ms[1:]):
            if aa == bb == "top":
                pairs.add((a, b))
    for a, b in sorted(pairs):
        name = comp.VIET.get((a, b)) or f"{a}_{b}"
        if name in art.REG or a not in art.REG or b not in art.REG:
            continue
        add(PixelDef(name, [], stack(a, b), kind="mark"))
        _set_top_anchors(art.REG[name], LC_TOP)
        cn = _case_name(name)
        add(PixelDef(cn, [], {(x, r + 2) for x, r in art.REG[name].pix}, kind="mark"))
        _set_top_anchors(art.REG[cn], UC_TOP)


# spacing modifier letters built from marks: cp -> (mark, dy)
SPACING = {
    0xB4: ("acutecomb", 0), 0xA8: ("dieresiscomb", 0), 0xAF: ("macroncomb", 0),
    0xB8: ("cedillacomb", 0), 0x2C6: ("circumflexcomb", 0), 0x2C7: ("caroncomb", 0),
    0x2C9: ("macroncomb", 0), 0x2CA: ("acutecomb", 0), 0x2CB: ("gravecomb", 0),
    0x2D8: ("brevecomb", 0), 0x2D9: ("dotaccentcomb", 0), 0x2DA: ("ringcomb", 0),
    0x2DB: ("ogonekcomb", 0), 0x2DC: ("tildecomb", 0), 0x2DD: ("hungarumlautcomb", 0),
    0x384: ("tonoscomb", 0), 0x385: ("dieresiscomb_tonoscomb", 0), 0x2CD: ("macronbelowcomb", 0),
    0x2CC: ("verticallinebelowcomb", 0), 0x2C8: None, 0x1FBD: ("commaabovecomb", 0),
    0x1FBF: ("commaabovecomb", 0), 0x1FFE: ("reversedcommaabovecomb", 0),
    0x1FC0: ("perispomenicomb", 0), 0x1FEF: ("gravecomb", 0), 0x1FFD: ("tonoscomb", 0),
    0x1FC1: ("dieresiscomb_perispomenicomb", 0), 0x1FED: ("dieresiscomb_gravecomb", 0),
    0x1FEE: ("dieresiscomb_tonoscomb", 0), 0x1FCD: ("commaabovecomb_gravecomb", 0),
    0x1FCE: ("commaabovecomb_tonoscomb", 0), 0x1FCF: ("commaabovecomb_perispomenicomb", 0),
    0x1FDD: ("reversedcommaabovecomb_gravecomb", 0), 0x1FDE: ("reversedcommaabovecomb_tonoscomb", 0),
    0x1FDF: ("reversedcommaabovecomb_perispomenicomb", 0), 0x2D3: None,
}


def register_spacing():
    for cp, v in SPACING.items():
        if v is None:
            continue
        m, dy = v
        if m not in art.REG or art.name_for(cp) in art.REG:
            continue
        add(PixelDef(art.name_for(cp), [cp], set(), comps=[(m, 0, dy)]))
