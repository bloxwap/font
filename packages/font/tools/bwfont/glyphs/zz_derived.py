"""Glyphs derived from other glyphs' skeletons (loaded last).

* Small capitals: every capital letter with a single lowercase mapping gets
  `<lowercase>.sc`, re-stroked at small-cap size so stems keep their weight.
  Accented small caps are composed automatically in build.add_composites.
"""
from __future__ import annotations

from ..composites import glyph_name
from ..skeleton import GLYPHS, derive

SC_H = 0.79       # small-cap height / cap height  (≈ 570 units)
SC_X = 0.86       # horizontal scale (small caps are relatively wider)
SC_W = 0.95       # stroke weight factor


def _small_caps():
    by_cp = {}
    for n, gd in GLYPHS.items():
        for u in gd.unicodes:
            by_cp.setdefault(u, n)
    made = set()
    for n, gd in list(GLYPHS.items()):
        if gd.kind != "base" or not gd.unicodes or gd.pack != "core":
            continue
        u = gd.unicodes[0]
        ch = chr(u)
        lo = ch.lower()
        if not ch.isupper() or len(lo) != 1 or lo == ch:
            continue
        lname = by_cp.get(ord(lo)) or glyph_name(ord(lo))
        sc = lname + ".sc"
        if sc in GLYPHS or sc in made:
            continue
        derive(sc, src=n, sx=SC_X, sy=SC_H, wscale=SC_W, zone="lc", families=gd.families)
        made.add(sc)


_small_caps()
