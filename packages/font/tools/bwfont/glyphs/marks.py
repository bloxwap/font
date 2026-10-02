"""Combining marks.

Marks are drawn around x=0.  Top marks carry `_top` at (0, xh) (or (0, cap)
for the `.case` variants used over capitals and ascenders) and a `top`
anchor at their own top for stacking.  Bottom marks carry `_bottom` at
(0, 0) and `bottom` below themselves.
"""
from __future__ import annotations

import math

from ..skeleton import glyph, G

MW = 0.84       # legacy constant (other modules import it); prefer mw(g)


def mw(g):
    """Mark weight factor: marks get relatively lighter as weight grows."""
    return 0.9 - 0.0013 * g.grow


def _base(g: G, case: bool):
    return (g.cap if case else g.xh) + (36 if case else 58) + g.grow * 0.1


def _h(g: G, case: bool):
    return (120 if case else 152) + g.grow * 0.85


def _top(g: G, case: bool, y_top_ink: float):
    base_y = g.cap if case else g.xh
    g.anchor("_top", 0, base_y)
    g.anchor("top", 0, y_top_ink)


def topmark(name, cp, case_too=True):
    def deco(f):
        def regular(g: G):
            f(g, False)
        glyph(name, cp, kind="mark")(regular)
        if case_too:
            def case(g: G):
                f(g, True)
            glyph(name + ".case", kind="mark")(case)
        return f
    return deco


def bottommark(name, cp):
    def deco(f):
        glyph(name, cp, kind="mark")(f)
        return f
    return deco


@topmark("acutecomb", 0x301)
def acute(g: G, case):
    y0 = _base(g, case)
    h = _h(g, case)
    r = g.hh * mw(g)
    g.line(-46 + 8, y0 + r, 46 + 8, y0 + h - r, mw(g))
    _top(g, case, y0 + h)


@topmark("gravecomb", 0x300)
def grave(g: G, case):
    y0 = _base(g, case)
    h = _h(g, case)
    r = g.hh * mw(g)
    g.line(46 - 8, y0 + r, -46 - 8, y0 + h - r, mw(g))
    _top(g, case, y0 + h)


@topmark("hungarumlautcomb", 0x30B)
def hungarumlaut(g: G, case):
    y0 = _base(g, case)
    h = _h(g, case)
    r = g.hh * mw(g)
    d = 72 + g.grow * 0.75
    for dx in (-d, d):
        g.line(dx - 34, y0 + r, dx + 40, y0 + h - r, mw(g))
    _top(g, case, y0 + h)


@topmark("dblgravecomb", 0x30F)
def dblgrave(g: G, case):
    y0 = _base(g, case)
    h = _h(g, case)
    r = g.hh * mw(g)
    d = 72 + g.grow * 0.75
    for dx in (-d, d):
        g.line(dx + 34, y0 + r, dx - 40, y0 + h - r, mw(g))
    _top(g, case, y0 + h)


def _chevron(g: G, case, up=True):
    y0 = _base(g, case)
    h = _h(g, case) * (0.8 if case else 0.84)
    wdt = 120 + g.grow * 0.75
    r = g.hh * mw(g)
    lo, hi = y0 + r, y0 + h - r
    if up:
        g.line(-wdt + r, lo, 0, hi, mw(g))
        g.line(wdt - r, lo, 0, hi, mw(g))
    else:
        g.line(-wdt + r, hi, 0, lo, mw(g))
        g.line(wdt - r, hi, 0, lo, mw(g))
    _top(g, case, y0 + h)


@topmark("circumflexcomb", 0x302)
def circumflex(g: G, case):
    _chevron(g, case, True)


@topmark("caroncomb", 0x30C)
def caron(g: G, case):
    _chevron(g, case, False)


@topmark("brevecomb", 0x306)
def breve(g: G, case):
    y0 = _base(g, case)
    h = _h(g, case) * (0.78 if case else 0.84)
    wdt = 114 + g.grow * 0.7
    r = g.hh * mw(g)
    (g.pen(-wdt + g.hw * mw(g), y0 + h - r, mw(g))
        .v(0, y0 + r, k=0.58)
        .h(wdt - g.hw * mw(g), y0 + h - r, k=0.58)
        .end())
    _top(g, case, y0 + h)


@topmark("invertedbrevecomb", 0x311)
def invbreve(g: G, case):
    y0 = _base(g, case)
    h = _h(g, case) * (0.78 if case else 0.84)
    wdt = 114 + g.grow * 0.7
    r = g.hh * mw(g)
    (g.pen(-wdt + g.hw * mw(g), y0 + r, mw(g))
        .v(0, y0 + h - r, k=0.58)
        .h(wdt - g.hw * mw(g), y0 + r, k=0.58)
        .end())
    _top(g, case, y0 + h)


@topmark("tildecomb", 0x303)
def tilde(g: G, case):
    y0 = _base(g, case) + 6
    h = _h(g, case) * (0.66 if case else 0.7)
    _tilde(g, y0, y0 + h, 128 + g.grow * 0.75)
    _top(g, case, y0 + h)


def _tilde(g: G, y0, y1, wdt):
    """Tilde in the ink box -wdt..wdt, y0..y1: one even wave.  The humps are
    horizontal at their extremes and the middle is a plain S, so the stroke is
    smooth all through (the old middle segment left each hump at an angle)."""
    w = mw(g)
    r = g.hh * w
    lo, hi = y0 + r, y1 - r
    a = -wdt + g.hw * w
    b = wdt - g.hw * w
    (g.pen(a, lo + (hi - lo) * 0.2, w)
        .to(a * 0.5, hi, (0.5, 1), "r", k=0.6)
        .to(b * 0.5, lo, "r", "r")
        .to(b, hi - (hi - lo) * 0.2, "r", (0.5, 1), k=0.6)
        .end())


@topmark("macroncomb", 0x304)
def macron(g: G, case):
    y0 = _base(g, case) + 22
    wdt = 122 + g.grow * 0.75
    g.bar(-wdt, wdt, y0 + g.hh * mw(g), mw(g))
    _top(g, case, y0 + g.H * mw(g))


def _dotd(g):
    return g.W * 1.08 + 18


@topmark("dotaccentcomb", 0x307)
def dotaccent(g: G, case):
    y0 = _base(g, case) + 4
    d = _dotd(g)
    g.dot(0, y0 + d / 2, d)
    _top(g, case, y0 + d)


@topmark("dieresiscomb", 0x308)
def dieresis(g: G, case):
    y0 = _base(g, case) + 4
    d = _dotd(g)
    sp = 98 + g.grow * 0.72
    g.dot(-sp, y0 + d / 2, d)
    g.dot(sp, y0 + d / 2, d)
    _top(g, case, y0 + d)


@topmark("ringcomb", 0x30A)
def ring(g: G, case):
    y0 = _base(g, case) - (6 if case else 4)
    s = (184 if not case else 164) + g.grow * 1.2
    w = _ring_w(g)
    g.oval(-s / 2, y0, s / 2, y0 + s, w=w)
    _top(g, case, y0 + s)


def _ring_w(g):
    """Ring weight: lighter as weight grows, so heavy rings keep a counter."""
    return 0.8 - 0.0015 * g.grow


def _dir(dx, dy):
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def _hook_w(g):
    """Hook-above weight: lighter as weight grows (a little faster than the
    ring, since the curl is smaller), so heavy hooks keep an open counter."""
    return 0.76 - 0.0018 * g.grow


@topmark("hookabovecomb", 0x309)
def hookabove(g: G, case):
    """Hook above: the top of a question mark.  Rises from a left terminal over
    the top, down the right side and sweeps down to an open end under its
    middle: one smooth stroke (no corner where the old stem turned down).
    The curl stacks two strokes over its counter, so as the weight grows the
    pen lightens and the curl gets taller and wider faster than the pen."""
    y0 = _base(g, case)
    # a curl needs more height than a flat mark
    if case:
        # over capitals the line has less room above, so the curl grows less
        # and its pen lightens a little more instead
        h = _h(g, case) * 1.12 + g.grow * 0.1
        w = _hook_w(g) - 0.0006 * g.grow
    else:
        h = _h(g, case) + 8 + g.grow * 0.32
        w = _hook_w(g)
    r = g.hh * w
    rx = 60 + g.grow * 0.55
    ym = y0 + h * 0.54
    ye = y0 + r
    xe = 4
    ux, uy = _dir(-0.8, -1)
    sy = ym - ye
    p = (g.pen(-rx + 6, y0 + h * 0.55, w)
         .to(0, y0 + h - r, (0.25, 1), "r", k=0.6)
         .h(rx, ym, k=0.6))
    p.c((rx, ym - sy * 0.7), (xe - ux * sy * 0.45, ye - uy * sy * 0.45), (xe, ye))
    p.end()
    _top(g, case, y0 + h)


def _comma_above(g: G, case, head_top: bool, tail_dir: float):
    """Comma-shaped mark built from the punctuation comma.  head_top: ’ (dot
    above, tail falling); else ‘ (dot below, tail rising).  tail_dir -1 = the
    tail falls to the left (normal comma), +1 = to the right (reversed)."""
    from .punctuation import _comma, _comma_ext, _d
    y0 = _base(g, case)
    d = _d(g)
    ext = _comma_ext(g)
    if head_top:
        _comma(g, 0, y0 + ext - d / 2, flip=False, mirror=tail_dir > 0)
    else:
        _comma(g, 0, y0 + d / 2, flip=True, mirror=tail_dir > 0)
    _top(g, case, y0 + ext)


@topmark("commaturnedabovecomb", 0x312)
def commaturned(g: G, case):
    # ‘ : head below, tail rising to the right
    _comma_above(g, case, head_top=False, tail_dir=-1)


@topmark("commaabovecomb", 0x313)
def commaabove(g: G, case):
    # ’ : head on top, tail falling to the left
    _comma_above(g, case, head_top=True, tail_dir=-1)


@topmark("reversedcommaabovecomb", 0x314)
def rcommaabove(g: G, case):
    # ‛ : head on top, tail falling to the right
    _comma_above(g, case, head_top=True, tail_dir=1)


@topmark("perispomenicomb", 0x342)
def perispomeni(g: G, case):
    tilde(g, case)


@topmark("verticallineabovecomb", 0x30D)
def vline(g: G, case):
    y0 = _base(g, case)
    h = _h(g, case)
    g.vstem(0, y0, y0 + h, mw(g))
    _top(g, case, y0 + h)


# --- bottom marks -------------------------------------------------------

def _bot(g: G, y_ink_bottom):
    g.anchor("_bottom", 0, 0)
    g.anchor("bottom", 0, y_ink_bottom)


@bottommark("dotbelowcomb", 0x323)
def dotbelow(g: G):
    d = _dotd(g)
    y = -60 - d / 2 - g.grow * 0.1
    g.dot(0, y, d)
    _bot(g, y - d / 2)


@bottommark("dieresisbelowcomb", 0x324)
def dieresisbelow(g: G):
    d = _dotd(g)
    y = -60 - d / 2 - g.grow * 0.1
    sp = 96 + g.grow * 0.62
    g.dot(-sp, y, d)
    g.dot(sp, y, d)
    _bot(g, y - d / 2)


@bottommark("ringbelowcomb", 0x325)
def ringbelow(g: G):
    s = 164 + g.grow * 1.2
    y1 = -50
    g.oval(-s / 2, y1 - s, s / 2, y1, w=_ring_w(g))
    _bot(g, y1 - s)


@bottommark("commaaccentcomb", 0x326)
def commabelow(g: G):
    """Comma below: the punctuation comma's construction at mark size."""
    from .punctuation import _comma
    d = _dotd(g) * 0.95
    y = -64 - d / 2 - g.grow * 0.1
    L = 92 + g.grow * 0.2
    _comma(g, 0, y, d=d, tail=L)
    _bot(g, y - d / 2 - L - g.hh * 0.62 * 0.9)


@bottommark("cedillacomb", 0x327)
def cedilla(g: G):
    """Cedilla: one smooth clockwise hook.  It drops out of the letter's bottom
    stroke heading down-right, swings round its right side and runs back left
    (no stub-to-hook corner)."""
    w = mw(g)
    r = g.hh * w
    hk = 124 + g.grow * 0.7           # hook height (below y0)
    hx = 64 + g.grow * 0.55           # hook reach to the right (skeleton)
    y0 = -58 - g.grow * 0.1
    yb = y0 - hk + r * 0.2            # bottom (skeleton)
    ym = y0 - hk * 0.45               # right extreme (skeleton)
    xs, ys = -8, 24
    ux, uy = _dir(0.5, -1)
    sy = ys - ym
    p = g.pen(xs, ys, w)
    p.c((xs + ux * sy * 0.5, ys + uy * sy * 0.5), (hx, ym + sy * 0.36), (hx, ym))
    (p.v(12, yb, k=0.6)
        .l(-hx * 0.55, yb)
        .end())
    _bot(g, y0 - hk - r)


@bottommark("ogonekcomb", 0x328)
def ogonek(g: G):
    """Ogonek: a round tail that falls down-left out of the letter, turns
    through a round bottom and runs out to the right."""
    w = mw(g)
    r = g.hh * w
    yb = -226 + r                     # bottom (skeleton)
    xl = -34 - g.grow * 0.15          # leftmost (skeleton)
    ym = -104 + g.grow * 0.25         # where the tail turns vertical
    ux, uy = _dir(-0.42, -1)
    sy = 30 - ym
    p = g.pen(0, 30, w)
    p.c((ux * sy * 0.45, 30 + uy * sy * 0.45), (xl, ym + sy * 0.4), (xl, ym))
    (p.v(xl + 66 + g.grow * 0.45, yb, k=0.6)
        .l(96 + g.grow * 0.4, yb)
        .end())
    g.anchor("_ogonek", 0, 0)
    g.anchor("_bottom", 0, 0)


@bottommark("circumflexbelowcomb", 0x32D)
def circumflexbelow(g: G):
    wdt = 112 + g.grow * 0.45
    r = g.hh * mw(g)
    lo, hi = -190 + r, -60 - r
    g.line(-wdt + r, lo, 0, hi, mw(g))
    g.line(wdt - r, lo, 0, hi, mw(g))
    _bot(g, -190)


@bottommark("brevebelowcomb", 0x32E)
def brevebelow(g: G):
    wdt = 112 + g.grow * 0.6
    w = _ring_w(g)                     # lightens with weight, so the bowl stays open
    r = g.hh * w
    yb = -180 - g.grow * 0.6           # grows, so heavy breves keep their curve
    (g.pen(-wdt + r, -60 - r, w)
        .v(0, yb + r, k=0.58)
        .h(wdt - r, -60 - r, k=0.58)
        .end())
    _bot(g, yb)


@bottommark("tildebelowcomb", 0x330)
def tildebelow(g: G):
    h = 110 + g.grow * 0.7             # grows, so heavy tildes keep their wave
    _tilde(g, -66 - h, -66, 128 + g.grow * 0.75)
    _bot(g, -66 - h)


@bottommark("macronbelowcomb", 0x331)
def macronbelow(g: G):
    wdt = 120 + g.grow * 0.5
    y = -80 - g.hh * mw(g)
    g.bar(-wdt, wdt, y, mw(g))
    _bot(g, y - g.hh)


@bottommark("lowlinecomb", 0x332)
def lowline(g: G):
    y = -100 - g.hh * mw(g)
    g.bar(-250, 250, y, mw(g))
    _bot(g, y - g.hh)


@bottommark("verticallinebelowcomb", 0x329)
def vlinebelow(g: G):
    g.vstem(0, -200, -60, mw(g))
    _bot(g, -200)


@bottommark("ypogegrammenicomb", 0x345)
def ypogegrammeni(g: G):
    w = mw(g)
    top = -58 - g.hh * w
    bot = top - 110 - g.grow * 0.6
    (g.pen(0, top, w)
        .l(0, bot + 40 + g.grow * 0.2)
        .v(46 + g.grow * 0.3, bot, k=0.6)
        .l(70 + g.grow * 0.4, bot)
        .end())
    _bot(g, bot - g.hh * w)


@glyph("horncomb", 0x31B, kind="mark")
def horn(g: G):
    # attaches at the 'horn' anchor (top right of o / u)
    r = g.hh * mw(g)
    (g.pen(-g.hw * 0.4, -20, mw(g))
        .to(50 + g.grow * 0.3, 70, (1, 0.4), (0, 1), k=0.6)
        .l(50 + g.grow * 0.3, 112)
        .end())
    g.anchor("_horn", 0, 0)


@glyph("strokeshortcomb", 0x335, kind="mark")
def strokeshort(g: G):
    g.bar(-110, 110, 0)
    g.anchor("_center", 0, 0)


@glyph("strokelongcomb", 0x336, kind="mark")
def strokelong(g: G):
    g.bar(-230, 230, 0)
    g.anchor("_center", 0, 0)


@glyph("slashlongcomb", 0x338, kind="mark")
def slashlong(g: G):
    g.line(-150, -260, 150, 260, 0.9)
    g.anchor("_center", 0, 0)


# --- caron as a vertical apostrophe for ď ľ ť Ľ -------------------------

@glyph("caroncomb.alt", kind="mark")
def caronalt(g: G):
    """Caron as a vertical apostrophe (ď ľ ť Ľ): the comma construction."""
    from .punctuation import _comma
    d = _dotd(g) * 0.9
    _comma(g, 0, -d / 2, d=d, tail=104 + g.grow * 0.1)
    g.anchor("_caron", 0, 0)


# --- Greek tonos (placed to the left of capitals) -------------------------

@glyph("tonoscomb", kind="mark")
def tonos(g: G):
    y0 = g.xh + 56
    h = 170 + g.grow * 0.25
    r = g.hh * mw(g)
    g.line(-28, y0 + r, 30, y0 + h - r, mw(g))
    g.anchor("_top", 0, g.xh)
    g.anchor("top", 0, y0 + h)


# --- Vietnamese stacked marks ----------------------------------------------

def _viet(name, first, second, dx, dy):
    def f(g: G):
        sub = g.include(first)
        a = sub.anchors
        g.anchor("_top", *a["_top"])
        g.anchor("top", a["top"][0], a["top"][1])
        from ..skeleton import shift
        sub2 = G(g.p, second)
        from ..skeleton import GLYPHS
        GLYPHS[second].func(sub2)
        off_x = dx(g)
        off_y = a["top"][1] - sub2.anchors["_top"][1] + (dy(g) if callable(dy) else dy)
        for s in sub2.strokes:
            from ..skeleton import _transform_stroke
            g.strokes.append(_transform_stroke(s, shift(off_x, off_y)))
        for c in sub2.extra:
            g.extra.append(c.transform(shift(off_x, off_y)))
    glyph(name, kind="mark")(f)


for case in ("", ".case"):
    _viet(f"circumflexcomb_acutecomb{case}", f"circumflexcomb{case}", f"acutecomb{case}",
          lambda g: 150 + g.grow * 0.95, lambda g: -150 - g.grow * 0.5)
    _viet(f"circumflexcomb_gravecomb{case}", f"circumflexcomb{case}", f"gravecomb{case}",
          lambda g: 150 + g.grow * 0.95, lambda g: -150 - g.grow * 0.5)
    # the hook sits off the circumflex's right arm; the capital circumflex is
    # flatter, so its hook drops less (or it would land on the arm)
    _viet(f"circumflexcomb_hookabovecomb{case}", f"circumflexcomb{case}", f"hookabovecomb{case}",
          (lambda g: 200 + g.grow * 1.2) if case else (lambda g: 156 + g.grow * 1.12),
          (lambda g: -110 - g.grow * 0.55) if case else (lambda g: -136 - g.grow * 0.45))
    _viet(f"circumflexcomb_tildecomb{case}", f"circumflexcomb{case}", f"tildecomb{case}",
          lambda g: 0, -44)
    _viet(f"brevecomb_acutecomb{case}", f"brevecomb{case}", f"acutecomb{case}", lambda g: 0, -44)
    _viet(f"brevecomb_gravecomb{case}", f"brevecomb{case}", f"gravecomb{case}", lambda g: 0, -44)
    _viet(f"brevecomb_hookabovecomb{case}", f"brevecomb{case}", f"hookabovecomb{case}", lambda g: 0,
          lambda g: -44 - g.grow * 0.15)   # the hook's tail settles into the breve's dip
    _viet(f"brevecomb_tildecomb{case}", f"brevecomb{case}", f"tildecomb{case}", lambda g: 0, -44)
