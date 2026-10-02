"""Latin lowercase skeletons."""
from __future__ import annotations

import math

from ..skeleton import glyph, mirror_x, mirror_y, G

JOIN = 0.52      # legacy taper width where strokes started on a stem (kept for importers;
                 # new drawing rides the stem instead: see LEAD, arch(), bowl_left())


def rot180(cx, cy):
    return lambda p: (2 * cx - p[0], 2 * cy - p[1])


# ---------------------------------------------------------------------------
# shared constructions
# ---------------------------------------------------------------------------

LEAD = 0.84      # width factor of the short run where an arch / hook rides along a stem
EPS = 1.0        # bowls sit this far inside the stem centre-line, so the counter edge
                 # never coincides with the stem's (the union stays clean and round)


def loop(g: G, l, b, r, t, ry0=None, ry1=None, xt=None, xb=None, yl=None, k=None, kr=None,
         w=1.0, top_run=0.0, bot_run=0.0):
    """Closed round loop on a skeleton box l..r, b..t (centre-line coordinates).
    The right side runs straight from ry0 up to ry1 (default: no straight run, a
    plain oval); xt / xb: x of the (right end of the) top / (left end of the) bottom
    extreme, which run straight for top_run / bot_run units; yl: y of the left
    extreme; k: tension of the left half, kr: of the right half.  Drawn as one
    smooth closed stroke, so its counter is a clean round with no joins in it.
    Straight runs must be > 0 in every master or 0 in all (same structure)."""
    cy = (b + t) / 2
    ry0 = cy if ry0 is None else ry0
    ry1 = ry0 if ry1 is None else ry1
    xt = (l + r) / 2 if xt is None else xt
    xb = xt if xb is None else xb
    yl = cy if yl is None else yl
    kr = k if kr is None else kr
    p = g.pen(r, ry1, w).v(xt, t, k=kr, k2=k)
    if top_run:
        p.l(xt - top_run, t)
    p.h(l, yl, k=k).v(xb, b, k=k)
    if bot_run:
        p.l(xb + bot_run, b)
    p.h(r, ry0, k=k, k2=kr).close()


def arch(g: G, xl, xr, top, base_y, join_y=None, end_y=None, apex=0.54, k=None, w=1.0,
         lead=None):
    """n-style shoulder from a stem centred on xl (skeleton x): the stroke rides up
    the stem's centre-line for a short run (`lead`), then peels off tangentially,
    rises to `top` (ink), comes down to xr (skeleton x), vertical from `end_y`, and
    runs straight down to base_y.  Riding the stem (instead of starting on it with a
    thin JOIN taper) keeps the counter round, with no lobe or dent at the join.
    w: stroke width factor (pass the stem's, e.g. 0.84 in a condensed Mono m)."""
    join_y = g.xh * 0.56 if join_y is None else join_y
    ty = top - g.hh * w
    ax = xl + (xr - xl) * apex
    end_y = top - (top - join_y) * 0.62 if end_y is None else end_y
    lead = (top - join_y) * 0.24 if lead is None else lead
    kk = 0.62 if k is None else k
    (g.pen(xl, join_y - lead, LEAD * w)
        .l(xl, join_y)
        .v(ax, ty, k=kk, w=w, k2=0.56)
        .h(xr, end_y, k=kk)
        .l(xr, base_y + g.hh * w)
        .end())


def bowl_left(g: G, xs, x0, y0, y1, j_top=None, j_bot=None, k=None, run=None):
    """Bowl on the left of a stem (d, q, a-like).  xs: stem skeleton x;
    x0: left ink edge; y0/y1: ink bottom/top of the bowl.
    Drawn as a complete round loop whose right side lies on the stem's centre-line,
    so the stem overlaps it and the counter stays a true round (notches where the
    bowl leaves the stem, no tapered stroke ends).  The right side runs straight
    along the stem from j_bot to j_top when given, else for `run` units centred on
    the bowl (default: short at Thin, longer in heavy weights to keep the counter
    open; run=0 gives a plain oval touching the stem at its widest point)."""
    l, r = x0 + g.hw, xs - EPS
    b, t = y0 + g.hh, y1 - g.hh
    cy = (b + t) / 2
    if j_top is not None or j_bot is not None:
        ry1 = cy if j_top is None else max(cy, j_top)
        ry0 = cy if j_bot is None else min(cy, j_bot)
    else:
        if run is None:
            # a short straight run along the stem, growing with weight, keeps heavy
            # counters open (always > 0, so every master has the same structure)
            run = 10 + (g.W - 22) * 0.6
        ry0, ry1 = cy - run / 2, cy + run / 2
    loop(g, l, b, r, t, ry0, ry1, k=k)


def c_shape(g: G, x0, x1, y0, y1, t_top=0.74, t_bot=0.24, xr_top=None, xr_bot=None, k=None,
            end_top=True, end_bot=True, dir_top=(0.36, -1), dir_bot=(0.34, 1)):
    """Open round (c, e-lower, etc.).  Terminals at fractions of height."""
    cx = (x0 + x1) / 2
    left = x0 + g.hw
    cy = (y0 + y1) / 2
    h = y1 - y0
    xt = (x1 - g.hw - 4) if xr_top is None else xr_top
    xb = (x1 - g.hw - 2) if xr_bot is None else xr_bot
    p = g.pen(xt, y0 + h * t_top)
    # direction of travel from top terminal towards apex: up-left
    p.to(cx + 6, y1 - g.hh, (-dir_top[0], -dir_top[1]), "l", k=0.62)
    p.h(left, cy, k=k).v(cx + 6, y0 + g.hh, k=k)
    p.to(xb, y0 + h * t_bot, "r", dir_bot, k=0.62)
    p.end()


# ---------------------------------------------------------------------------
# glyphs
# ---------------------------------------------------------------------------

@glyph("n", 0x6E, zone="lc")
def n(g: G):
    bw = g.wd(436, 456)
    g.stem(0, 0, g.xh)
    arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, 0)


@glyph("h", 0x68, zone="lc")
def h(g: G):
    bw = g.wd(436, 456)
    g.stem(0, 0, g.asc)
    arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, 0)


@glyph("m", 0x6D, zone="lc")
def m(g: G):
    if g.mono:
        bw = g.wd(0, 500)
        g.stem(0, 0, g.xh, w=0.84)
        x1 = bw / 2
        a = g.hw * 0.84
        arch(g, a, x1, g.xh + g.ov * 0.4, 0, apex=0.5, w=0.84)
        arch(g, x1, bw - a, g.xh + g.ov * 0.4, 0, apex=0.5, w=0.84)
        return
    bw = g.wd(720, grow=1.0)
    g.stem(0, 0, g.xh)
    x1 = bw / 2
    arch(g, g.hw, x1, g.xh + g.ov * 0.4, 0, apex=0.52)
    arch(g, x1, bw - g.hw, g.xh + g.ov * 0.4, 0, apex=0.52)


@glyph("u", 0x75, zone="lc")
def u(g: G):
    bw = g.wd(436, 456)
    g.transform(rot180(bw / 2, g.xh / 2))
    g.stem(0, 0, g.xh)
    arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, 0)
    g.transform(None)


@glyph("o", 0x6F, zone="lc")
def o(g: G):
    bw = g.wd(478, 476)
    g.oval(0, -g.ov, bw, g.xh + g.ov)


@glyph("c", 0x63, zone="lc")
def c(g: G):
    bw = g.wd(446, 456)
    c_shape(g, 0, bw, -g.ov, g.xh + g.ov)


@glyph("e", 0x65, zone="lc")
def e(g: G):
    bw = g.wd(468, 466)
    y0, y1 = -g.ov, g.xh + g.ov
    cx = bw / 2
    yb = g.xh * 0.5 + g.hh * 0.2
    left, right = g.hw, bw - g.hw
    (g.pen(right, yb)
        .v(cx, y1 - g.hh, k=0.6)
        .h(left, (y0 + y1) / 2)
        .v(cx + 6, y0 + g.hh)
        .to(bw - g.hw - 6, (y1 - y0) * 0.2 + y0, "r", (0.38, 1), k=0.62)
        .end())
    g.line(left, yb, right, yb)


@glyph("a", 0x61, zone="lc")
def a(g: G):
    bw = g.wd(432, 440)
    xs = bw - g.hw
    top = g.xh + g.ov
    cx = bw / 2
    # hook + stem
    (g.pen(g.hw + 14, g.xh * 0.76 + g.grow * 0.1)
        .to(cx - 4, top - g.hh, (0.34, 1), "r", k=0.62)
        .h(xs, g.xh * 0.6, k=0.6)
        .l(xs, g.hh)
        .end())
    # bowl: a closed round loop riding the stem (no tapered ends, round counter):
    # a fairly flat top meeting the stem, a ROUND left side and a ROUND bottom that
    # sweeps up into the stem (no flat bottom run), and a straight right side lying
    # on the stem (always > 0 long, so masters match)
    t = g.xh * 0.56 - g.hh * 0.2 - g.grow * 0.2
    b = -g.ov + g.hh
    l, r = g.hw, xs - EPS
    hb = t - b
    yl = b + hb * 0.5                      # left extreme
    rt = hb * 0.22 + g.hw * 0.4            # corner under the bowl's top (> pen radius)
    xt = r - rt * 1.25                     # where the top corner begins
    # round left: the left quarters reach well past the pen, so the counter (not just
    # the outline) is round at every weight; the flat top shrinks as weight grows
    ax = g.hw + (t - yl - g.hh) * 0.95 + 26
    xb = l + (r - l) * 0.47                # bottom extreme: one round sweep, no flat
    ry0 = b + hb * 0.36 + g.hh * 0.3       # where the bottom sweep meets the stem
    loop(g, l, b, r, t, ry0, t - rt, xt=xt, top_run=xt - (l + ax),
         xb=xb, yl=yl)


@glyph("a.ss01", zone="lc")
def a_single(g: G):
    bw = g.wd(474, 466)
    xs = bw - g.hw
    g.stem(bw - g.W, 0, g.xh)
    bowl_left(g, xs, 0, -g.ov, g.xh + g.ov)


@glyph("d", 0x64, zone="lc")
def d(g: G):
    bw = g.wd(474, 466)
    xs = bw - g.hw
    g.stem(bw - g.W, 0, g.asc)
    bowl_left(g, xs, 0, -g.ov, g.xh + g.ov)


@glyph("q", 0x71, zone="lc")
def q(g: G):
    bw = g.wd(474, 466)
    xs = bw - g.hw
    g.stem(bw - g.W, g.desc, g.xh)
    bowl_left(g, xs, 0, -g.ov, g.xh + g.ov)


@glyph("b", 0x62, zone="lc")
def b(g: G):
    bw = g.wd(474, 466)
    g.transform(mirror_x(bw / 2))
    d(g)
    g.transform(None)


@glyph("p", 0x70, zone="lc")
def p(g: G):
    bw = g.wd(474, 466)
    g.transform(mirror_x(bw / 2))
    q(g)
    g.transform(None)


@glyph("g", 0x67, zone="lc")
def g_(g: G):
    bw = g.wd(474, 466)
    xs = bw - g.hw
    bowl_left(g, xs, 0, -g.ov + 4, g.xh + g.ov)
    bot = g.desc - g.ov
    cx = bw / 2
    (g.pen(xs, g.xh - g.hh)
        .l(xs, 0)
        .v(cx, bot + g.hh, k=0.6)
        .to(g.hw + 18, g.desc * 0.42, "l", (-0.36, 1), k=0.62)
        .end())


@glyph("l", 0x6C, zone="lc")
def l(g: G):
    if g.mono:
        bw = g.wd(0, 440)
        x = bw * 0.48 - g.hw
        g.bar(bw * 0.10, x + g.W, g.asc - g.hh)
        (g.pen(x + g.hw, g.asc - g.hh).l(x + g.hw, 150)
            .v(x + g.hw + 120, g.hh, k=0.6).l(bw - g.hw * 0.8, g.hh).end())
        return
    g.stem(0, 0, g.asc)


@glyph("i", 0x69, zone="lc")
def i(g: G):
    if g.mono:
        bw = g.wd(0, 440)
        x = bw * 0.5 - g.hw
        g.bar(bw * 0.12, x + g.W, g.xh - g.hh)
        g.stem(x, 0, g.xh)
        g.bar(bw * 0.04, bw * 0.96, g.hh)
        g.dot(x + g.hw, g.asc - g.W * 0.58 - 10)
        g.anchor("top", x + g.hw, g.xh)
        return
    g.stem(0, 0, g.xh)
    g.dot(g.hw, g.asc - g.W * 0.58 - 10)
    g.anchor("top", g.hw, g.xh)


@glyph("dotlessi", 0x131, zone="lc")
def dotlessi(g: G):
    if g.mono:
        bw = g.wd(0, 440)
        x = bw * 0.5 - g.hw
        g.bar(bw * 0.12, x + g.W, g.xh - g.hh)
        g.stem(x, 0, g.xh)
        g.bar(bw * 0.04, bw * 0.96, g.hh)
        return
    g.stem(0, 0, g.xh)


@glyph("j", 0x6A, zone="lc")
def j(g: G):
    if g.mono:
        bw = g.wd(0, 400)
        xs = bw * 0.66 - g.hw
        g.bar(bw * 0.12, xs + g.hw, g.xh - g.hh)
    else:
        bw = g.wd(170, grow=0.6)
        xs = bw - g.hw
    bot = g.desc - g.ov * 0.4
    xe = g.hw * 0.8
    xc = xs - (xs - xe) * 0.6
    (g.pen(xs, g.xh - g.hh).l(xs, -10 - g.grow * 0.3)
        .v(xc, bot + g.hh, k=0.6)
        .l(xe, bot + g.hh)
        .end())
    g.dot(xs, g.asc - g.W * 0.58 - 10)
    g.anchor("top", xs, g.xh)


@glyph("dotlessj", 0x237, zone="lc")
def dotlessj(g: G):
    j(g)
    g.extra.clear()


@glyph("r", 0x72, zone="lc")
def r(g: G):
    if g.mono:
        bw = g.wd(0, 430)
        x = bw * 0.26
        g.stem(x, 0, g.xh)
        g.bar(bw * 0.05, x + g.W, g.xh - g.hh)
        g.bar(bw * 0.05, bw * 0.78, g.hh)
        jy = g.xh * 0.5
        (g.pen(x + g.hw, jy - 56, LEAD).l(x + g.hw, jy)
            .v(x + g.hw + 150, g.xh + g.ov * 0.4 - g.hh, k=0.62, w=1.0)
            .l(bw - g.hw * 0.7, g.xh + g.ov * 0.4 - g.hh).end())
        return
    bw = g.wd(290, grow=0.75)
    g.stem(0, 0, g.xh)
    jy = g.xh * 0.52
    (g.pen(g.hw, jy - 56, LEAD)            # ride the stem, then peel off (see arch())
        .l(g.hw, jy)
        .v(g.hw + 140 + g.grow * 0.3, g.xh + g.ov * 0.4 - g.hh, k=0.62, w=1.0)
        .l(bw - g.hw, g.xh + g.ov * 0.4 - g.hh - 4)
        .end())


@glyph("t", 0x74, zone="lc")
def t(g: G):
    bw = g.wd(300, 430, grow=0.7)
    if g.mono:
        xs = bw * 0.38
    else:
        xs = 74 + g.hw + g.grow * 0.2
    xe = bw - g.hw * 0.7                   # tail end (skeleton)
    xc = xs + (xe - xs) * 0.6              # where the curve meets the flat tail
    (g.pen(xs, g.cap * 0.92 - g.hh)
        .l(xs, 130 + g.grow * 0.35)
        .v(xc, g.hh - g.ov * 0.3, k=0.6)
        .l(xe, g.hh - g.ov * 0.3)
        .end())
    g.bar(0, bw - (0 if g.mono else 10), g.xh - g.hh)


@glyph("f", 0x66, zone="lc")
def f(g: G):
    bw = g.wd(300, 440, grow=0.7)
    if g.mono:
        xs = bw * 0.4
    else:
        xs = 70 + g.hw + g.grow * 0.25
    top = g.asc + g.ov * 0.4
    xe = bw - g.hw * 0.7
    xc = xs + (xe - xs) * 0.6
    (g.pen(xs, g.hh)
        .l(xs, g.asc - 150 - g.grow * 0.35)
        .v(xc, top - g.hh, k=0.6)
        .l(xe, top - g.hh)
        .end())
    g.bar(0, bw - 10 if not g.mono else bw, g.xh - g.hh)


@glyph("k", 0x6B, zone="lc")
def k(g: G):
    bw = g.wd(430, 456)
    g.stem(0, 0, g.asc)
    jx = g.W + 8
    jy = g.xh * 0.36
    g.line(jx, jy, bw - g.hw * 1.1, g.xh - g.hh, w0=0.9, w1=0.92)
    g.line(jx + 70 + g.grow * 0.2, jy + 70 * 0.95, bw - g.hw * 1.05, g.hh, w0=0.92, w1=0.92)


@glyph("v", 0x76, zone="lc")
def v(g: G):
    bw = g.wd(452, 470)
    vy = g.hh
    g.line(g.hw * 0.94, g.xh - g.hh, bw / 2, vy, 0.92)
    g.line(bw - g.hw * 0.94, g.xh - g.hh, bw / 2, vy, 0.92)


@glyph("w", 0x77, zone="lc")
def w(g: G):
    bw = g.wd(700, 500, grow=1.2)
    s = 0.9 if not g.mono else 0.8
    hw = g.hw * s
    xs = [hw, bw * 0.29, bw * 0.5, bw * 0.71, bw - hw]
    lo = g.hh * s
    hi = g.xh - g.hh * s
    g.line(xs[0], hi, xs[1], lo, s)
    g.line(xs[1], lo, xs[2], hi * 0.94, s)
    g.line(xs[2], hi * 0.94, xs[3], lo, s)
    g.line(xs[3], lo, xs[4], hi, s)


@glyph("x", 0x78, zone="lc")
def x(g: G):
    bw = g.wd(446, 466)
    r = g.hw * 0.92
    g.line(r, g.hh, bw - r, g.xh - g.hh, 0.92)
    g.line(r, g.xh - g.hh, bw - r, g.hh, 0.92)


@glyph("y", 0x79, zone="lc")
def y(g: G):
    bw = g.wd(456, 470)
    hw = g.hw * 0.94
    vx = bw / 2 - 6
    vy = g.hh - 6
    g.line(hw, g.xh - g.hh, vx, vy, 0.92)
    # descender: the right diagonal runs straight on to a round cap (no tail),
    # which stays clear and simple at small sizes
    x1, y1 = bw - hw, g.xh - g.hh
    dx, dy = vx - x1, vy - y1
    bot = g.desc + g.hh + 6
    tb = (bot - y1) / dy
    g.line(x1, y1, x1 + dx * tb, bot, 0.92)


@glyph("y.ss04", zone="lc")
def y_ss04(g: G):
    """The earlier y, its descender curling into a short tail (ss04)."""
    bw = g.wd(456, 470)
    hw = g.hw * 0.94
    vx = bw / 2 - 6
    vy = g.hh - 6
    g.line(hw, g.xh - g.hh, vx, vy, 0.92)
    x1, y1 = bw - hw, g.xh - g.hh
    dx, dy = vx - x1, vy - y1
    bot = g.desc + g.hh
    tb = (bot + 30 - y1) / dy
    xb = x1 + dx * tb
    (g.pen(x1, y1, 0.92)
        .l(xb, bot + 30)
        .to(xb - 90, bot, (dx, dy), "l", k=0.5)
        .l(g.hw + 10, bot)
        .end())


@glyph("z", 0x7A, zone="lc")
def z(g: G):
    bw = g.wd(410, 440)
    g.bar(10, bw - 10, g.xh - g.hh)
    g.bar(0, bw, g.hh)
    g.line(bw - 10 - g.hw * 1.1, g.xh - g.hh, g.hw * 1.1, g.hh, 0.92)


@glyph("s", 0x73, zone="lc")
def s(g: G):
    bw = g.wd(418, 436)
    top = g.xh + g.ov
    bot = -g.ov
    cx = bw / 2
    lx = g.hw + 6
    rx = bw - g.hw
    (g.pen(bw - g.hw - 12, g.xh * 0.79)
        .to(cx, top - g.hh, (-0.4, 1), "l", k=0.62)
        .h(lx, g.xh * 0.73 + g.hh * 0.1, k=0.6)
        .v(cx, g.xh * 0.5 + g.hh * 0.05, k=0.56)
        .h(rx, g.xh * 0.26 - g.hh * 0.1, k=0.56)
        .v(cx - 6, bot + g.hh, k=0.6)
        .to(g.hw + 6, g.xh * 0.2, "l", (-0.4, 1), k=0.62)
        .end())
