"""Math operators and currency symbols.

Operators share one math axis (`ma`, = AX 340 used by the arrows) and the
tabular figure advance, so `+ − × ÷ = < > ± ≤ ≥ ≠ ≈` line up in tables.
Currency symbols use figure height and the tabular advance too.  Round
letter-like currency forms (C, G, the £ hook, ∂, ℮ …) take their curves from
the capitals' oval-cut construction (`c_open`, `round_terminal`, `g_round` in
latin_upper.py), so terminals flow straight out of the bowl with no knuckle,
exactly like C / G / S.
"""
from __future__ import annotations

import math

from ..skeleton import G, GLYPHS, derive, glyph, mirror_x, mirror_y
from .figures import (DIAG, JOIN, NUM_S, Piece, cap_N, fit_cell, num_ws, oval_quarter, sups_dy,
                      subs_dy, tab, _clear_adv)
from .latin_upper import KR, c_open, g_round, round_terminal


def _rev(c):
    return (c[3], c[2], c[1], c[0])


def _arc(p, cx, cy, rx, ry, a0, a1, w=None):
    """Append an exact elliptical arc a0 -> a1 (degrees, CCW if a1 > a0) to pen path p."""
    n = max(1, math.ceil(abs(a1 - a0) / 90 - 1e-9))
    step = (a1 - a0) / n
    for i in range(n):
        t0 = math.radians(a0 + step * i)
        t1 = math.radians(a0 + step * (i + 1))
        kk = 4 / 3 * math.tan((t1 - t0) / 4)
        p0 = (cx + rx * math.cos(t0), cy + ry * math.sin(t0))
        p3 = (cx + rx * math.cos(t1), cy + ry * math.sin(t1))
        c1 = (p0[0] - kk * rx * math.sin(t0), p0[1] + kk * ry * math.cos(t0))
        c2 = (p3[0] + kk * rx * math.sin(t1), p3[1] - kk * ry * math.cos(t1))
        p.c(c1, c2, p3, w if i == n - 1 else None)
    return p



def lite(g: G):
    """Secondary strokes (currency bars, stubs): lighter as weight grows so
    counters between them stay open."""
    return 0.9 - g.grow * 0.0016


def thin(g: G):
    """Strokes inside rings (⊕ ⊗ ¤ ∘ °)."""
    return 0.82 - g.grow * 0.0016


def ma(g: G):
    """Math axis: centre of operators (≈ figure middle, a bit above lc centre)."""
    return g.xh * 0.5 + 70


def opw(g: G):
    """Ink width of + − = and friends."""
    return g.wd(468, 456)


def cw(g: G):
    """Ink width of currency symbols."""
    return g.wd(472, 458)


def cw_dense(g: G, extra=0.0):
    """Ink width for the busiest symbols (₦ ₩ ₪ ₡): grows faster with weight
    (still inside the tabular advance)."""
    return g.wd(472 + extra, 458 + extra * 0.3, grow=1.0)


def heavy_lite(g: G):
    """Main-stroke factor for the busiest symbols."""
    return 1.0 - g.grow * 0.0012


def dbl(g: G):
    """Distance between the two bars of ₦ ₩ ₳ € ¥ etc."""
    return 132 + g.grow * 0.7


# ---------------------------------------------------------------------------
# shared constructions
# ---------------------------------------------------------------------------

def tilde(g: G, x0, x1, cy, amp=None, w=1.0):
    """Horizontal wave (~) with ink x0..x1 centred on cy."""
    amp = (58 + g.grow * 0.18) if amp is None else amp
    hx = g.hw * w
    xl, xr = x0 + hx, x1 - hx
    span = xr - xl
    (g.pen(xl, cy - amp * 0.55, w)
        .to(xl + span * 0.29, cy + amp, (0.55, 1), "r", k=0.6)
        .to(xl + span * 0.71, cy - amp, "r", "r")
        .to(xr, cy + amp * 0.55, "r", (0.55, 1), k=0.6)
        .end())


def chevron(g: G, x0, x1, cy, half, left=True, w=DIAG):
    """< (left=True) or > with ink x0..x1, arms reaching cy±half (ink)."""
    hx, hy = g.hw * w, g.hh * w
    vx = x0 + hx * 0.9 if left else x1 - hx * 0.9
    ex = x1 - hx if left else x0 + hx
    g.line(ex, cy + half - hy, vx, cy, w)
    g.line(ex, cy - half + hy, vx, cy, w)


def c_shape(g: G, x0, x1, y0, y1, t_top=None, t_bot=None, w=1.0):
    """Open round (C / c), terminals at fractions of the height.  Drawn as the
    capitals' oval-cut C (`c_open`): each terminal is a piece of the oval
    itself, so the curve runs on unbroken into the round caps (no kink where
    the terminal leaves the bowl).  `w` is kept for compatibility (full pen)."""
    c_open(g, x0, x1, y0, y1, t_top, t_bot)


def s_shape(g: G, x0, x1, y0, y1, k=None):
    """Capital-proportioned S with ink box x0..x1, y0..y1 (overshoots incl.).
    `k` sets one rounder tension for every curve (the $, to match the figures)."""
    h = y1 - y0
    f = lambda t: y0 + h * t
    cx = (x0 + x1) / 2
    ko, ki = (0.62, 0.6) if k is None else (k, k)   # outer terminals, bowls
    ks = 0.56 if k is None else k                    # spine
    (g.pen(x1 - g.hw - 14, f(0.795))
        .to(cx + 4, y1 - g.hh, (-0.42, 1), "l", k=ko)
        .h(x0 + g.hw + 12, f(0.745), k=ki)
        .v(cx, f(0.508), k=ks)
        .h(x1 - g.hw, f(0.255), k=ks)
        .v(cx - 6, y0 + g.hh, k=ki)
        .to(x0 + g.hw + 4, f(0.2), "l", (-0.42, 1), k=ko)
        .end())


def bowl_right(g: G, xs, x1, ytop, ybot, w=1.0):
    """D-like bowl attached to a stem at skeleton x `xs`: top bar at ink ytop,
    bottom bar at ink ybot, right ink edge x1 (P, B, R, ₹…).  w: pen factor."""
    yt, yb = ytop - g.hh * w, ybot + g.hh * w
    r = x1 - g.hw * w
    rad = min((yt - yb) / 2, (r - xs) * 0.9)
    xb = r - rad
    (g.pen(xs, yt, w).l(xb, yt)
        .h(r, (yt + yb) / 2, k=0.6).v(xb, yb, k=0.6)
        .l(xs, yb).end())


def nary_y(g: G):
    return -120.0, g.cap + 30.0


def set_adv(g: G):
    tab(g)


# ---------------------------------------------------------------------------
# basic operators (tabular)
# ---------------------------------------------------------------------------

def _op(name, *cps, tabular=True):
    def deco(f):
        def fn(g: G):
            f(g)
            if tabular:
                tab(g)
        glyph(name, *cps)(fn)
        return f
    return deco


@_op("plus", 0x2B)
def plus(g: G):
    w = opw(g)
    y = ma(g)
    g.bar(0, w, y)
    g.vstem(w / 2, y - w / 2, y + w / 2)


@_op("minus", 0x2212)
def minus(g: G):
    g.bar(0, opw(g), ma(g))


def eq_d(g: G):
    return 94 + g.grow * 0.4


@_op("equal", 0x3D)
def equal(g: G):
    w = opw(g)
    y = ma(g)
    d = eq_d(g)
    g.bar(0, w, y + d)
    g.bar(0, w, y - d)


@_op("multiply", 0xD7)
def multiply(g: G):
    w = opw(g)
    y = ma(g)
    s = w * 0.38 - g.hw * DIAG * 0.5
    cx = w / 2
    g.line(cx - s, y - s, cx + s, y + s, DIAG)
    g.line(cx - s, y + s, cx + s, y - s, DIAG)


@_op("divide", 0xF7)
def divide(g: G):
    w = opw(g)
    y = ma(g)
    g.bar(0, w, y)
    d = 168 + g.grow * 0.5
    g.dot(w / 2, y + d)
    g.dot(w / 2, y - d)


def lt_w(g: G):
    return g.wd(424, 424)


def lt_h(g: G):
    return 232 + g.grow * 0.1


@_op("less", 0x3C)
def less(g: G):
    chevron(g, 0, lt_w(g), ma(g), lt_h(g), True)


@_op("greater", 0x3E)
def greater(g: G):
    chevron(g, 0, lt_w(g), ma(g), lt_h(g), False)


def _le(g: G, left):
    w = lt_w(g)
    y = ma(g)
    yb = y - 236 - g.grow * 0.1             # bar centre
    half = 172 + g.grow * 0.05
    gap = 70 + g.grow * 0.5
    cy = yb + g.hh + gap + half
    chevron(g, 0, w, cy, half, left)
    g.bar(0, w, yb)


@_op("lessequal", 0x2264)
def lessequal(g: G):
    _le(g, True)


@_op("greaterequal", 0x2265)
def greaterequal(g: G):
    _le(g, False)


@_op("notequal", 0x2260)
def notequal(g: G):
    equal(g)
    w = opw(g)
    y = ma(g)
    g.line(w / 2 - 92, y - 236, w / 2 + 92, y + 236, DIAG)


def _pm(g: G, flip):
    w = opw(g)
    y = ma(g)
    if flip:
        g.transform(mirror_y(y))
    arm = w * 0.42
    cy = y + 56 + g.grow * 0.1
    g.bar(0, w, cy)
    g.vstem(w / 2, cy - arm, cy + arm)
    g.bar(0, w, y - 236 - g.grow * 0.1)
    g.transform(None)


@_op("plusminus", 0xB1)
def plusminus(g: G):
    _pm(g, False)


@_op("uni2213", 0x2213)
def minusplus(g: G):
    _pm(g, True)


@_op("asciitilde", 0x7E)
def asciitilde(g: G):
    tilde(g, 0, opw(g), ma(g))


@_op("similar", 0x223C)
def similar(g: G):
    tilde(g, 0, opw(g), ma(g))


@_op("approxequal", 0x2248)
def approxequal(g: G):
    w = opw(g)
    y = ma(g)
    d = 92 + g.grow * 0.72
    amp = 56 - g.grow * 0.05
    tilde(g, 0, w, y + d, amp=amp)
    tilde(g, 0, w, y - d, amp=amp)


def three_d(g: G):
    return 150 + g.grow * 0.62


@_op("equivalence", 0x2261)
def equivalence(g: G):
    w = opw(g)
    y = ma(g)
    d = three_d(g)
    for k in (-1, 0, 1):
        g.bar(0, w, y + k * d)


@_op("congruent", 0x2245)
def congruent(g: G):
    w = opw(g)
    y = ma(g)
    d = three_d(g)
    tilde(g, 0, w, y + d, amp=48 - g.grow * 0.05)
    g.bar(0, w, y)
    g.bar(0, w, y - d)


@_op("logicalnot", 0xAC)
def logicalnot(g: G):
    w = opw(g)
    y = ma(g) + 40
    g.bar(0, w, y)
    g.vstem(w - g.hw, y - 196 - g.grow * 0.2, y + g.hh)


def _much(g: G, left):
    w = g.wd(520, 470)
    y = ma(g)
    cwid = w * 0.60
    off = w - cwid
    chevron(g, 0, cwid, y, lt_h(g) * 0.9, left)
    chevron(g, off, off + cwid, y, lt_h(g) * 0.9, left)


@_op("uni226A", 0x226A)
def muchless(g: G):
    _much(g, True)


@_op("uni226B", 0x226B)
def muchgreater(g: G):
    _much(g, False)


# ---------------------------------------------------------------------------
# small operators / marks of measure
# ---------------------------------------------------------------------------

@_op("dotmath", 0x22C5)
def dotmath(g: G):
    g.dot(0, ma(g))


@_op("asteriskmath", 0x2217)
def asteriskmath(g: G):
    y = ma(g)
    R = 176 + g.grow * 0.2
    w = 0.86
    for a in (90, 30, 150):
        dx, dy = R * math.cos(math.radians(a)), R * math.sin(math.radians(a))
        g.line(-dx, y - dy, dx, y + dy, w)


@_op("uni2218", 0x2218)
def ringoperator(g: G):
    d = 250 + g.grow * 1.3
    y = ma(g)
    g.oval(0, y - d / 2, d, y + d / 2, k=0.56, w=thin(g))


def _ring(g: G, d, top, w=None):
    g.oval(0, top - d, d, top, k=0.56, w=thin(g) if w is None else w)


@glyph("degree", 0xB0)
def degree(g: G):
    _ring(g, 278 + g.grow * 1.1, g.cap + 10)


def _prime(g: G, x):
    top = g.cap + 10
    g.pen(x + 62, top - g.hh, 1.0).l(x, top - 236, 0.72).end()


@glyph("minute", 0x2032)
def minute(g: G):
    _prime(g, g.hw)


@glyph("second", 0x2033)
def second(g: G):
    _prime(g, g.hw)
    _prime(g, g.hw + 118 + g.grow * 0.9)


def _dots3(g: G, up):
    d = g.W * 1.16 + 10
    sp = 310 + g.grow * 0.3
    lo, hi = d / 2, g.xh - d / 2
    if not up:
        lo, hi = hi, lo
    g.dot(d / 2, lo)
    g.dot(d / 2 + sp, lo)
    g.dot(d / 2 + sp / 2, hi)


@_op("therefore", 0x2234)
def therefore(g: G):
    _dots3(g, True)


@_op("uni2235", 0x2235)
def because(g: G):
    _dots3(g, False)


# ---------------------------------------------------------------------------
# larger math symbols
# ---------------------------------------------------------------------------

@_op("infinity", 0x221E, tabular=False)
def infinity(g: G):
    # Loops grow wider and taller with weight, the strokes lighten a little,
    # and the top/bottom of each loop and the crossing are lighter still (the
    # width change rides the round quarter arcs and the crossing, never a tight
    # turn), so even at Black each counter is a round-backed teardrop rather
    # than a pinched triangle.  The arms cross steeply (slope 1.3) so the
    # counter's tip is blunt.  Mono gets its own (wider, flatter) proportions
    # to keep the counters open inside the 600 cell.
    if g.mono:
        W_ = 480 + g.grow * 0.75
        hh = 150 + g.grow * 0.4                # half height (ink)
        lx = W_ * 0.3 + 6
        wl = 0.92 - g.grow * 0.0022
    else:
        W_ = g.wd(640, 476, grow=1.2)
        hh = 150 + g.grow * 0.8
        lx = W_ * 0.29 + 6
        wl = 1.0 - g.grow * 0.001
    y = ma(g)
    cx = W_ / 2
    wc = (0.92 - g.grow * 0.0012) * wl         # loop tops/bottoms + crossing
    top, bot = y + hh - g.hh * wc, y - hh + g.hh * wc
    rx = W_ - lx
    xl, xr = g.hw * wl, W_ - g.hw * wl
    s = 1.3                                    # crossing slope
    # two open strokes, each running from one outer extreme through the crossing
    # to the other; they meet tangentially at the extremes (vertical there), so
    # the caps vanish inside the other stroke and the figure-eight is seamless
    (g.pen(xl, y, wl)
        .v(lx, bot, k=0.58, w=wc)
        .to(cx, y, "r", (1, s), k=0.6, w=wc)
        .to(rx, top, (1, s), "r", k=0.6, w=wc)
        .h(xr, y, k=0.58, w=wl)
        .end())
    (g.pen(xr, y, wl)
        .v(rx, bot, k=0.58, w=wc)
        .to(cx, y, "l", (-1, s), k=0.6, w=wc)
        .to(lx, top, (-1, s), "l", k=0.6, w=wc)
        .h(xl, y, k=0.58, w=wl)
        .end())


@glyph("integral", 0x222B)
def integral(g: G):
    w = g.wd(330, 360)
    top, bot = g.asc + 30, g.desc + 10
    xm = w / 2
    r = 72 + g.grow * 0.25
    yt, yb = top - g.hh, bot + g.hh
    st, sb = yt - r * 1.5, yb + r * 1.5       # where the stem turns into the hooks
    # hooks cut from ovals (round_terminal): the curve flows unbroken into the caps
    ct, t0 = round_terminal(xm, st, yt, w - g.hw, top - 104, KR)
    cb, t1 = round_terminal(xm, sb, yb, g.hw, bot + 104, KR)
    t1 = _rev(t1)
    (g.pen(*t0[0])
        .c(t0[1], t0[2], t0[3])
        .h(xm, st, k=KR)
        .l(xm, sb)
        .v(cb, yb, k=KR)
        .c(t1[1], t1[2], t1[3])
        .end())


@_op("partialdiff", 0x2202)
def partialdiff(g: G):
    """∂: a mirrored 6 built like the figure (d_six): a complete round bowl,
    and a stroke that hooks over from an oval-cut terminal and runs down the
    bowl's side until it merges, tangent, at the bowl's widest point (the
    counter stays a true round; no tapered join)."""
    bw = g.wd(470, 458)
    top, bot = g.cap + g.ov, -g.ov
    l = g.hw
    bt = g.cap * 0.62 + g.ov
    by = (bt + bot) / 2
    ya = g.cap * 0.62                         # the straight side turns into the hook here
    g.transform(mirror_x(bw / 2))
    g.oval(0, bot, bw, bt, k=KR)
    ct, t = round_terminal(l, ya, top - g.hh, bw - g.hw - 14, g.cap * 0.84, KR)
    (g.pen(*t[0])
        .c(t[1], t[2], t[3])
        .h(l, ya, k=KR)
        .l(l, by)
        .end())
    g.transform(None)


@glyph("summation", 0x2211)
def summation(g: G):
    w = g.wd(560, 470)
    y0, y1 = nary_y(g)
    ym = (y0 + y1) / 2
    vx = w * 0.54
    x0 = g.hw * DIAG + 4
    g.bar(0, w, y1 - g.hh)
    g.bar(0, w, y0 + g.hh)
    g.line(x0, y1 - g.hh, vx, ym, DIAG)
    g.line(vx, ym, x0, y0 + g.hh, DIAG)
    # small returns at the bar ends: distinguishes ∑ from Σ
    t = 74 + g.grow * 0.3
    g.vstem(w - g.hw, y1 - g.hh * 2 - t, y1)
    g.vstem(w - g.hw, y0, y0 + g.hh * 2 + t)


@glyph("product", 0x220F)
def product(g: G):
    w = g.wd(620, 470)
    y0, y1 = nary_y(g)
    o = 56 + g.grow * 0.2
    g.bar(0, w, y1 - g.hh)
    g.stem(o, y0, y1)
    g.stem(w - o - g.W, y0, y1)


@glyph("radical", 0x221A)
def radical(g: G):
    w = g.wd(570, 480)
    top = g.cap + 70
    V = (w * 0.36, g.hh * DIAG)
    T = (w * 0.36 + 150 + g.grow * 0.2, top - g.hh)
    g.line(g.hw * DIAG, g.cap * 0.42, V[0], V[1], DIAG)
    g.line(V[0], V[1], T[0], T[1], DIAG)
    g.bar(T[0] - g.hw, w, top - g.hh)


def _triangle(g: G, flip):
    """∆ / ∇ drawn explicitly (no mirroring, keeps contour direction)."""
    w = g.wd(600, 480)
    hx, hy = g.hw * DIAG, g.hh * DIAG
    yb = g.cap - g.hh if flip else g.hh            # bar centre
    ya = hy if flip else g.cap - hy                # apex
    g.bar(0, w, yb)
    g.line(g.hw + 16, yb, w / 2, ya, DIAG)
    g.line(w - g.hw - 16, yb, w / 2, ya, DIAG)


@glyph("increment", 0x2206, zone="fig")
def increment(g: G):
    _triangle(g, False)


@glyph("gradient", 0x2207, zone="fig")
def gradient(g: G):
    _triangle(g, True)


@_op("emptyset", 0x2205)
def emptyset(g: G):
    D = g.wd(520, 470)
    cy = g.cap / 2
    g.oval(0, cy - D / 2, D, cy + D / 2, k=0.56)
    g.line(g.hw * DIAG - 10, 30, D - g.hw * DIAG + 10, g.cap - 30, DIAG)


def set_h(g: G):
    return 238 + g.grow * 0.45


def _subset(g: G, x0, x1, cy, half):
    """⊂ with ink x0..x1, cy±half."""
    yt, yb = cy + half - g.hh, cy - half + g.hh
    ry = (yt - yb) / 2
    rx = min(ry * 0.96, (x1 - x0) - g.W)
    xc = x0 + g.hw + rx
    (g.pen(x1 - g.hw, yt).l(xc, yt)
        .h(x0 + g.hw, cy, k=0.58).v(xc, yb, k=0.58)
        .l(x1 - g.hw, yb).end())


def sub_w(g: G):
    return g.wd(420, 420)


@_op("element", 0x2208)
def element(g: G):
    w = sub_w(g)
    y = ma(g)
    _subset(g, 0, w, y, set_h(g))
    g.bar(0, w, y)


@_op("notelement", 0x2209)
def notelement(g: G):
    element(g)
    w = sub_w(g)
    y = ma(g)
    g.line(w / 2 - 90, y - 300, w / 2 + 90, y + 300, DIAG)


@_op("propersubset", 0x2282)
def propersubset(g: G):
    _subset(g, 0, sub_w(g), ma(g), set_h(g))


@_op("propersuperset", 0x2283)
def propersuperset(g: G):
    w = sub_w(g)
    g.transform(mirror_x(w / 2))
    _subset(g, 0, w, ma(g), set_h(g))
    g.transform(None)


def _subeq(g: G, flip):
    w = sub_w(g)
    y = ma(g)
    yb = y - set_h(g) - 30 - g.grow * 0.1
    half = 178 + g.grow * 0.05
    gap = 66 + g.grow * 0.5
    cy = yb + g.hh + gap + half
    if flip:
        g.transform(mirror_x(w / 2))
    _subset(g, 0, w, cy, half)
    g.bar(0, w, yb)
    g.transform(None)


@_op("reflexsubset", 0x2286)
def reflexsubset(g: G):
    _subeq(g, False)


@_op("reflexsuperset", 0x2287)
def reflexsuperset(g: G):
    _subeq(g, True)


def _cap_shape(g: G, flip):
    w = g.wd(440, 430)
    y = ma(g)
    half = 250 + g.grow * 0.05
    top, bot = y + half, y - half
    if flip:
        g.transform(mirror_y(y))
    l, r = g.hw, w - g.hw
    rad = (r - l) / 2
    (g.pen(l, bot + g.hh).l(l, top - g.hh - rad * 1.05)
        .v(w / 2, top - g.hh, k=0.58).h(r, top - g.hh - rad * 1.05, k=0.58)
        .l(r, bot + g.hh).end())
    g.transform(None)


@_op("intersection", 0x2229)
def intersection(g: G):
    _cap_shape(g, False)


@_op("union", 0x222A)
def union(g: G):
    _cap_shape(g, True)


def _wedge(g: G, flip):
    w = g.wd(460, 450)
    y = ma(g)
    half = 250 + g.grow * 0.05
    if flip:
        g.transform(mirror_y(y))
    hx, hy = g.hw * DIAG, g.hh * DIAG
    g.line(hx, y - half + hy, w / 2, y + half - hy, DIAG)
    g.line(w - hx, y - half + hy, w / 2, y + half - hy, DIAG)
    g.transform(None)


@_op("logicaland", 0x2227)
def logicaland(g: G):
    _wedge(g, False)


@_op("logicalor", 0x2228)
def logicalor(g: G):
    _wedge(g, True)


@_op("proportional", 0x221D, tabular=False)
def proportional(g: G):
    w = g.wd(520, 470, grow=1.1)
    y = ma(g)
    hh = 150 + g.grow * 0.8
    wl = (0.92 - g.grow * 0.0016) if g.mono else 1.0
    top, bot = y + hh - g.hh * wl, y - hh + g.hh * wl
    cx = w * 0.50
    lx = w * 0.24 + 6
    wc = 0.86 * wl
    xr = w - g.hw * 0.8 * wl
    # one stroke: lower arm -> crossing -> loop -> crossing -> upper arm
    (g.pen(xr, bot, wl)
        .to(cx, y, "l", (-1, 0.95), k=0.62, w=wc)
        .to(lx, top, (-1, 0.95), "l", k=0.6, w=wl)
        .h(g.hw * wl, y, k=0.58)
        .v(lx, bot, k=0.58)
        .to(cx, y, "r", (1, 0.95), k=0.6, w=wc)
        .to(xr, top, (1, 0.95), "r", k=0.62, w=wl)
        .end())


@_op("angle", 0x2220)
def angle(g: G):
    w = g.wd(520, 470)
    g.bar(0, w, g.hh)
    g.line(g.hw * DIAG, g.hh, w * 0.84, g.cap * 0.78, DIAG)


def _circ_op(g: G, cross):
    D = g.wd(520, 486, grow=0.6)
    y = ma(g)
    k = 0.5523
    wr = 0.94 - g.grow * 0.0012
    g.oval(0, y - D / 2, D, y + D / 2, k=k, w=wr)
    cx = D / 2
    rx, ry = D / 2 - g.hw * wr, D / 2 - g.hh * wr
    wi = thin(g)
    if cross:
        c = math.sqrt(0.5)
        g.line(cx - rx * c, y - ry * c, cx + rx * c, y + ry * c, wi)
        g.line(cx - rx * c, y + ry * c, cx + rx * c, y - ry * c, wi)
    else:
        g.line(cx - rx, y, cx + rx, y, wi)
        g.line(cx, y - ry, cx, y + ry, wi)


@_op("circleplus", 0x2295)
def circleplus(g: G):
    _circ_op(g, False)


@_op("circlemultiply", 0x2297)
def circlemultiply(g: G):
    _circ_op(g, True)


@_op("perpendicular", 0x22A5)
def perpendicular(g: G):
    w = g.wd(500, 470)
    g.bar(0, w, g.hh)
    g.vstem(w / 2, 0, g.cap * 0.86)


@glyph("universal", 0x2200, zone="fig")
def universal(g: G):
    w = g.wd(540, 480)
    hx, hy = g.hw * DIAG, g.hh * DIAG
    A = (hx, g.cap - hy)
    B = (w - hx, g.cap - hy)
    V = (w / 2, hy)
    g.line(A[0], A[1], V[0], V[1], DIAG)
    g.line(B[0], B[1], V[0], V[1], DIAG)
    yb = g.cap * 0.56
    t = (A[1] - yb) / (A[1] - V[1])
    xl = A[0] + (V[0] - A[0]) * t
    g.line(xl, yb, w - xl, yb)
    tab(g)


def _exists(g: G):
    w = g.wd(420, 420, grow=0.9)
    g.vstem(w - g.hw, 0, g.cap)
    g.bar(0, w, g.cap - g.hh)
    g.bar(30, w, g.cap * 0.5 + g.hh * 0.2)
    g.bar(0, w, g.hh)
    return w


@glyph("existential", 0x2203, zone="fig")
def existential(g: G):
    _exists(g)
    tab(g)


@glyph("uni2204", 0x2204, zone="fig")
def notexistential(g: G):
    w = _exists(g)
    g.line(w / 2 - 112, -60, w / 2 + 112, g.cap + 60, lite(g) * DIAG)
    tab(g)


@glyph("estimated", 0x212E, zone="fig")
def estimated(g: G):
    w = g.wd(600, 476)
    top, bot = g.cap * 0.92 + g.ov, -g.ov
    l, r = g.hw, w - g.hw
    cx = w / 2
    yb = (top + bot) / 2
    ybt = bot + g.hh
    cb, t = round_terminal(l, yb, ybt, r - 8, bot + (top - bot) * 0.2, KR)
    t = _rev(t)
    (g.pen(r, yb)
        .v(cx, top - g.hh, k=KR)
        .h(l, yb, k=KR)
        .v(cb, ybt, k=KR)
        .c(t[1], t[2], t[3])
        .end())
    g.line(l, yb, r, yb)


@glyph("uni2113", 0x2113, zone="lc")
def litre(g: G):
    """ℓ script small l: upstroke, loop, stem, tail."""
    rl = 150 + g.grow * 1.0              # loop width (skeleton): constant counter
    x0 = g.hw
    xs = x0 + 96 + g.grow * 0.6          # stem (skeleton)
    top = g.asc + g.ov * 0.4
    yl = top - g.hh - rl * 0.95
    w = xs + 190 + g.grow * 0.7
    (g.pen(x0, 250)
        .to(xs + rl, yl, (0.55, 1), "u", k=0.6)
        .v(xs + rl / 2, top - g.hh, k=0.58)
        .h(xs, yl, k=0.58)
        .l(xs, 170)
        .v(xs + 100 + g.grow * 0.3, g.hh - g.ov * 0.3, k=0.6)
        .to(w - g.hw, 150, "r", (0.35, 1), k=0.62)
        .end())


def _cap_C(g: G, x0, x1):
    c_shape(g, x0, x1, -g.ov, g.cap + g.ov, t_top=0.79, t_bot=0.21)


@glyph("uni2103", 0x2103, zone="uc")
def celsius(g: G):
    d = 230 + g.grow * 1.0
    _ring(g, d, g.cap + g.ov)
    x0 = d + 70 + g.grow * 0.2
    _cap_C(g, x0, x0 + g.wd(560, 300))
    fit_cell(g)


@glyph("uni2109", 0x2109, zone="uc")
def fahrenheit(g: G):
    d = 230 + g.grow * 1.0
    _ring(g, d, g.cap + g.ov)
    x0 = d + 80 + g.grow * 0.2
    fw = g.wd(400, 260)
    g.stem(x0, 0, g.cap)
    g.bar(x0, x0 + fw, g.cap - g.hh)
    g.bar(x0, x0 + fw * 0.9, g.cap * 0.48)
    fit_cell(g)


# ---------------------------------------------------------------------------
# currency
# ---------------------------------------------------------------------------

def _cur(name, *cps, tabular=True):
    def deco(f):
        def fn(g: G):
            f(g)
            if tabular:
                tab(g)
        glyph(name, *cps, zone="fig")(fn)
        return f
    return deco


def stubs(g: G, x, y_in_top, y_in_bot, ext=None, w=None):
    """Short vertical strokes poking out above and below (the $ / ¢ / ₿ lines)."""
    ext = (100 + g.grow * 0.3) if ext is None else ext
    w = lite(g) if w is None else w
    g.vstem(x, y_in_top - 60, y_in_top + ext, w)
    g.vstem(x, y_in_bot - ext, y_in_bot + 60, w)


@_cur("dollar", 0x24)
def dollar(g: G):
    """Round S with stubs above and below, in the spirit of Nunito's $ (see figures.py)."""
    w = cw(g) + 14
    s_shape(g, 0, w, -g.ov, g.cap + g.ov, k=0.54)
    stubs(g, w / 2 + 2, g.cap + g.ov, -g.ov)


@_cur("cent", 0xA2)
def cent(g: G):
    """¢: a round lowercase-height c on the baseline, stubs above and below."""
    w = cw(g) - 50
    y0, y1 = -g.ov, g.xh + 24 + g.ov
    c_shape(g, 0, w, y0, y1)
    stubs(g, w / 2 + 8, y1, y0, ext=96 + g.grow * 0.2)


def _pound(g: G, w):
    """£ / ₤ body: an oval-cut hook running into the straight stem, and the foot bar."""
    xs = w * 0.30 + g.grow * 0.1
    top = g.cap + g.ov
    side_y = g.cap * 0.64
    ct, t = round_terminal(xs, side_y, top - g.hh, w - g.hw - 8, g.cap * 0.80, KR)
    (g.pen(*t[0])
        .c(t[1], t[2], t[3])
        .h(xs, side_y, k=KR)
        .l(xs, g.hh)
        .end())
    g.bar(0, w, g.hh)
    return xs


@_cur("sterling", 0xA3)
def sterling(g: G):
    w = cw(g)
    xs = _pound(g, w)
    g.bar(12, xs + 200 + g.grow * 0.4, g.cap * 0.45)


@_cur("uni20A4", 0x20A4)
def lira(g: G):
    w = cw(g)
    xs = _pound(g, w)
    ym = g.cap * 0.40
    d = dbl(g) * 0.8
    for yy in (ym + d / 2, ym - d / 2):
        g.bar(12, xs + 200 + g.grow * 0.4, yy, w=lite(g))


@_cur("yen", 0xA5)
def yen(g: G):
    w = cw(g)
    hx = g.hw * DIAG
    vy = g.cap * 0.47
    cx = w / 2
    g.line(hx, g.cap - g.hh, cx, vy, DIAG)
    g.line(w - hx, g.cap - g.hh, cx, vy, DIAG)
    g.vstem(cx, 0, vy + g.hh)
    d = dbl(g)
    yb = vy - g.hh * 0.6
    g.bar(w * 0.12, w * 0.88, yb, w=lite(g))
    g.bar(w * 0.12, w * 0.88, yb - d, w=lite(g))


@_cur("Euro", 0x20AC)
def euro(g: G):
    # the C widens with weight (bars overhang a little less), so its round
    # stays wider than the pen can fold at Black
    w = cw(g) + 10 + g.grow * 0.2
    xo = 60 - g.grow * 0.2
    c_shape(g, xo, w, -g.ov, g.cap + g.ov, t_top=0.80, t_bot=0.20)
    d = dbl(g)
    ym = g.cap * 0.5
    xr = xo + (w - xo) * 0.62
    g.bar(0, xr, ym + d / 2, w=lite(g))
    g.bar(0, xr - 20, ym - d / 2, w=lite(g))


@_cur("currency", 0xA4)
def currency(g: G):
    d = 330 + g.grow * 0.9
    L = 74 + g.grow * 0.15
    c = math.sqrt(0.5)
    y = ma(g)
    wr = thin(g) + 0.08
    o = L * c + g.hw * lite(g)
    cx = o + d / 2
    g.oval(o, y - d / 2, o + d, y + d / 2, k=0.5523, w=wr)
    rx, ry = d / 2 - g.hw * wr, d / 2 - g.hh * wr
    for sx in (-1, 1):
        for sy in (-1, 1):
            p0 = (cx + sx * rx * c, y + sy * ry * c)
            p1 = (p0[0] + sx * L * c, p0[1] + sy * L * c)
            g.line(p0[0], p0[1], p1[0], p1[1], lite(g))


@_cur("colonmonetary", 0x20A1)
def colonsign(g: G):
    w = cw_dense(g)
    _cap_C(g, 0, w)
    e = 70
    run = 150
    for x in (w * 0.30, w * 0.30 + 120 + g.grow * 0.5):
        g.line(x, -e + g.hh, x + run, g.cap + e - g.hh, lite(g) * DIAG)


@_cur("uni20B5", 0x20B5)
def cedi(g: G):
    w = cw(g)
    _cap_C(g, 0, w)
    g.vstem(w / 2 + 6, -100, g.cap + 100, lite(g))


@_cur("uni20B2", 0x20B2)
def guarani(g: G):
    w = cw(g)
    g_round(g, w)
    g.vstem(w / 2 + 6, -100, g.cap + 100, lite(g))


@_cur("franc", 0x20A3)
def franc(g: G):
    w = cw(g)
    x0 = 70 + g.grow * 0.2
    g.stem(x0, 0, g.cap)
    g.bar(x0, w, g.cap - g.hh)
    g.bar(x0, w * 0.88, g.cap * 0.49)
    g.bar(0, x0 + g.W + 150, g.cap * 0.22, w=lite(g))


@_cur("uni20A6", 0x20A6)
def naira(g: G):
    w = cw_dense(g)
    cap_N(g, 34, w - 68, w=heavy_lite(g))
    d = dbl(g)
    ym = g.cap * 0.5
    g.bar(0, w, ym + d / 2, w=lite(g))
    g.bar(0, w, ym - d / 2, w=lite(g))


@_cur("uni20A9", 0x20A9)
def won(g: G):
    w = cw_dense(g, 20)
    s = 0.86 * heavy_lite(g)
    hw = g.hw * s
    xs = [hw, w * 0.29, w * 0.5, w * 0.71, w - hw]
    lo, hi = g.hh * s, g.cap - g.hh * s
    mid = g.cap * 0.84
    g.line(xs[0], hi, xs[1], lo, s)
    g.line(xs[1], lo, xs[2], mid, s)
    g.line(xs[2], mid, xs[3], lo, s)
    g.line(xs[3], lo, xs[4], hi, s)
    d = dbl(g)
    ym = g.cap * 0.47
    g.bar(0, w, ym + d / 2, w=lite(g))
    g.bar(0, w, ym - d / 2, w=lite(g))


@_cur("sheqel", 0x20AA, tabular=False)
def sheqel(g: G):
    w = g.wd(560, 470, grow=1.1)
    sw = heavy_lite(g) * (0.92 if g.mono else 1.0)
    W, hw, hh = g.W * sw, g.hw * sw, g.hh * sw
    top = g.cap * 0.84
    rad = 110 + g.grow * 0.2
    xl, xr = hw, w - hw
    gap = (xr - xl - W * 2) / 3
    xm = xl + W + gap
    xr2 = xr - W - gap
    yt, yb = top - hh, hh
    rx = min(rad, (xr2 - xl) / 2 - 1)
    (g.pen(xl, yb, sw).l(xl, yt - rad).v(xl + rx, yt, k=0.58).l(xr2 - rx, yt)
        .h(xr2, yt - rad, k=0.58).l(xr2, top * 0.32).end())
    rx2 = min(rad, (xr - xm) / 2 - 1)
    (g.pen(xm, top * 0.68, sw).l(xm, yb + rad).v(xm + rx2, yb, k=0.58).l(xr - rx2, yb)
        .h(xr, yb + rad, k=0.58).l(xr, yt).end())


@_cur("dong", 0x20AB)
def dong(g: G):
    s = 0.86
    p = Piece(g, "d", s, s, 1.0)
    p.put(-p.box[0], 120 - p.box[1])
    x1 = p.w
    xs = x1 - g.hw
    top = 120 + p.h
    g.bar(xs - 130 - g.grow * 0.3, xs + g.hw + 60 + g.grow * 0.3, top - 90 - g.grow * 0.3, w=lite(g))
    g.bar(0, x1, -40 + g.hh, w=lite(g))


@_cur("uni20AD", 0x20AD)
def kip(g: G):
    w = cw(g)
    x0 = 60 + g.grow * 0.15
    g.stem(x0, 0, g.cap)
    jx = x0 + g.W + 6
    jy = g.cap * 0.40
    g.line(jx, jy, w - g.hw * 1.1, g.cap - g.hh, DIAG, DIAG)
    g.line(jx + 76 + g.grow * 0.3, jy + 84, w - g.hw * 1.05, g.hh, DIAG, DIAG)
    g.bar(0, w * 0.70, g.cap * 0.5, w=lite(g))


@_cur("uni20AE", 0x20AE)
def tugrik(g: G):
    w = cw(g)
    cx = w / 2
    g.bar(0, w, g.cap - g.hh)
    g.vstem(cx, 0, g.cap)
    d = dbl(g) * 1.1
    for y in (g.cap * 0.46 + d / 2, g.cap * 0.46 - d / 2):
        g.line(cx - 130 - g.grow * 0.2, y - 56, cx + 130 + g.grow * 0.2, y + 56, lite(g) * DIAG)


@_cur("uni20B1", 0x20B1)
def peso(g: G):
    w = cw(g)
    x0 = 56 + g.grow * 0.15
    xs = x0 + g.hw
    g.stem(x0, 0, g.cap)
    bowl_right(g, xs, w - 10, g.cap, g.cap * 0.34 - g.grow * 0.3)
    d = dbl(g) * 0.9
    ym = g.cap * 0.66 - g.grow * 0.15
    g.bar(0, w, ym + d / 2, w=lite(g))
    g.bar(0, w, ym - d / 2, w=lite(g))


@_cur("uni20B3", 0x20B3)
def austral(g: G):
    w = cw(g) + 20
    hx = g.hw * DIAG
    g.line(hx, g.hh, w / 2, g.cap - g.hh * DIAG, DIAG)
    g.line(w - hx, g.hh, w / 2, g.cap - g.hh * DIAG, DIAG)
    d = dbl(g)
    ym = g.cap * 0.33
    g.bar(0, w, ym + d / 2, w=lite(g))
    g.bar(0, w, ym - d / 2, w=lite(g))


@_cur("uni20B4", 0x20B4)
def hryvnia(g: G):
    w = cw(g)
    g.transform(mirror_x(w / 2))
    s_shape(g, 0, w, -g.ov, g.cap + g.ov, k=0.54)
    g.transform(None)
    d = dbl(g)
    ym = g.cap * 0.5
    g.bar(0, w, ym + d / 2, w=lite(g))
    g.bar(0, w, ym - d / 2, w=lite(g))


@_cur("uni20B8", 0x20B8)
def tenge(g: G):
    w = cw(g)
    d = 150 + g.grow * 0.62
    g.bar(0, w, g.cap - g.hh)
    y2 = g.cap - g.hh - d
    g.bar(0, w, y2)
    g.vstem(w / 2, 0, y2 + g.hh)


@_cur("uni20B9", 0x20B9)
def rupee(g: G):
    w = cw(g) - 16
    yt = g.cap - g.hh
    d = 150 + g.grow * 0.62
    y2 = yt - d
    ym = g.cap * 0.40
    g.bar(0, w, yt)
    g.bar(0, w, y2)
    r = w * 0.80 - g.hw
    rad = min((yt - ym) / 2, r - w * 0.3)
    xb = r - rad
    (g.pen(w * 0.30, yt).l(xb, yt).h(r, (yt + ym) / 2, k=0.6).v(xb, ym, k=0.6)
        .l(g.hw + 10, ym).end())
    g.line(g.hw + 54 + g.grow * 0.2, ym, w * 0.76, g.hh, DIAG)


@_cur("uni20BA", 0x20BA)
def turkishlira(g: G):
    """₺: stem whose foot runs on into one exact elliptical arc, up the right
    side and a little back over (round terminal, no hook)."""
    w = cw(g)
    xs = w * 0.32 + g.grow * 0.1
    g.vstem(xs, 0, g.cap)
    r = w - g.hw
    yb = g.hh
    ce = g.cap * 0.31                 # centre of the arc's ellipse
    ry = ce - yb
    rx = ry * 1.04
    p = g.pen(xs, yb).l(r - rx, yb)
    _arc(p, r - rx, ce, rx, ry, -90, 40)
    p.end()
    d = dbl(g) * 0.95
    for y in (g.cap * 0.54 + d / 2, g.cap * 0.54 - d / 2):
        g.line(xs - 130 - g.grow * 0.1, y - 60, xs + 140 + g.grow * 0.2, y + 64, lite(g) * DIAG)


@_cur("uni20BC", 0x20BC)
def manat(g: G):
    w = cw(g) + 20
    top = g.cap * 0.78
    l, r = g.hw, w - g.hw
    rad = (r - l) / 2
    (g.pen(l, g.hh).l(l, top - g.hh - rad * 0.9)
        .v(w / 2, top - g.hh, k=0.58).h(r, top - g.hh - rad * 0.9, k=0.58)
        .l(r, g.hh).end())
    g.vstem(w / 2, 0, g.cap + 20)


@_cur("uni20BD", 0x20BD)
def ruble(g: G):
    w = cw(g)
    x0 = 72 + g.grow * 0.2
    xs = x0 + g.hw
    g.stem(x0, 0, g.cap)
    yb = g.cap * 0.40
    bowl_right(g, xs, w - 6, g.cap, yb)
    g.bar(0, x0 + g.W, yb + g.hh * 0)      # bowl's lower bar continues left
    g.bar(0, w * 0.72, g.cap * 0.2, w=lite(g))


@_cur("uni20BF", 0x20BF)
def bitcoin(g: G):
    w = cw(g) - 6
    x0 = 0.0
    xs = x0 + g.hw
    top = g.cap
    ym = g.cap * 0.545
    g.stem(x0, 0, top)
    # upper bowl (slightly narrower) and lower bowl share the middle bar
    bowl_right(g, xs, w - 34 - g.grow * 0.1, top, ym - g.hh)
    bowl_right(g, xs, w, ym + g.hh, 0)
    # the two Bitcoin strokes, poking out above and below
    ext = 104 + g.grow * 0.3
    for f in (0.30, 0.60):
        x = x0 + g.W * 0.5 + (w - g.W) * f
        g.vstem(x, top - 60, top + ext, lite(g))
        g.vstem(x, -ext, 60, lite(g))


@_cur("uni20A8", 0x20A8, tabular=False)
def rupeesign(g: G):
    """₨ — R followed by a small s.  The Mono cell is too tight for two full-
    weight letters, so there the R gets the larger share of the cell and its
    bowl, and the small s, lighten with weight (the R counter stays open;
    every factor is linear in grow, so topology never changes)."""
    if g.mono:
        wr = 1.0 - g.grow * 0.0020            # stem + leg
        wb = 1.0 - g.grow * 0.0034            # bowl (≈ 0.67 at Black)
        ws = 1.0 - g.grow * 0.0046            # small s (≈ 0.56 at Black)
        rw = 272 + g.grow * 0.52
        sx, sy = 0.56 - g.grow * 0.0018, 0.88 - g.grow * 0.0008
        gap = 22 + g.grow * 0.02
    else:
        wr = wb = ws = 1.0
        rw = g.wd(390, 270)
        sx, sy = 0.84, 1.0
        gap = 46 + g.grow * 0.25
    xs = g.hw * wr
    g.stem(0, 0, g.cap, w=wr)
    yb = g.cap * 0.44
    bowl_right(g, xs, rw, g.cap, yb, w=wb)
    g.line(rw * 0.42 + g.grow * 0.15, yb, rw - g.hw * DIAG * wr, g.hh * wr, DIAG * wr)
    p = Piece(g, "s", sx, sy, ws)
    p.put(rw + gap - p.box[0], 0)
    fit_cell(g)


# ---------------------------------------------------------------------------
# superscript / subscript operators
# ---------------------------------------------------------------------------

def _sup_c(g: G):
    return g.cap - NUM_S * g.cap / 2


def _sub_c(g: G):
    return subs_dy(g) + NUM_S * g.cap / 2


for _src, _sup, _sub in (("plus", 0x207A, 0x208A), ("minus", 0x207B, 0x208B), ("equal", 0x207C, 0x208C)):
    derive(f"uni{_sup:04X}", _sup, src=_src, sx=NUM_S, dy=lambda g: _sup_c(g) - NUM_S * ma(g),
           wscale=num_ws, post=_clear_adv)
    derive(f"uni{_sub:04X}", _sub, src=_src, sx=NUM_S, dy=lambda g: _sub_c(g) - NUM_S * ma(g),
           wscale=num_ws, post=_clear_adv)

# parentheses come from punctuation.py (another module); only derive them if present
try:  # noqa: SIM105
    from . import punctuation as _punct  # noqa: F401
except Exception:  # pragma: no cover - module missing or mid-edit
    _punct = None

if "parenleft" in GLYPHS and "parenright" in GLYPHS:
    def _paren_mid(g: G, name):
        p = Piece(g, name)
        return (p.box[1] + p.box[3]) / 2

    for _src, _sup, _sub in (("parenleft", 0x207D, 0x208D), ("parenright", 0x207E, 0x208E)):
        derive(f"uni{_sup:04X}", _sup, src=_src, sx=NUM_S,
               dy=lambda g, s=_src: _sup_c(g) - NUM_S * _paren_mid(g, s), wscale=num_ws, post=_clear_adv)
        derive(f"uni{_sub:04X}", _sub, src=_src, sx=NUM_S,
               dy=lambda g, s=_src: _sub_c(g) - NUM_S * _paren_mid(g, s), wscale=num_ws, post=_clear_adv)
