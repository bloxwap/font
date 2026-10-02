"""Punctuation, dashes, enclosures, quotes and spacing accents."""
from __future__ import annotations

import math

from ..skeleton import glyph, G, mirror_x, mirror_y

DIAG = 0.92          # diagonal width factor
JOIN = 0.52          # bowl-from-stem join width
TOP, BOT = 760, -170  # enclosure span (parens, brackets, slashes, bars)
CASE_DY = 88         # x-height centre -> cap-height centre (dashes, guillemets, bullets)
ENC_DY = 64          # raise of .case enclosures
DASH_Y = 290         # centre of hyphen / dashes
NUDGE = 0.8          # keeps coincident round caps at corners from confusing overlap removal


def rot180(cx, cy):
    return lambda p: (2 * cx - p[0], 2 * cy - p[1])


def shift(dx, dy=0.0):
    return lambda p: (p[0] + dx, p[1] + dy)


def _d(g: G):
    """Default punctuation dot diameter."""
    return g.W * 1.16 + 10


def _tail(g: G):
    return 118 + g.grow * 0.2


def _comma(g: G, cx, cy, flip=False, mirror=False, d=None, tail=None):
    """Comma: round dot with a tapering tail.  `cy` is the dot centre.
    flip: rotated 180 degrees (tail rises up-right; for quoteleft).
    mirror: tail goes down-right (quotereversed).
    d / tail: dot diameter and tail length (default: punctuation sizes; marks
    pass smaller ones)."""
    d = _d(g) if d is None else d
    r = d / 2
    g.dot(cx, cy, d)
    L = _tail(g) if tail is None else tail
    # the tail leaves the dot's right side tangentially (its right edge runs
    # along the dot's edge), then sweeps down-left in one even curve
    sx = r - g.hw
    ex, ey = -r * 0.5 - 8 - g.grow * 0.1, -r - L
    sgn_x = -1 if mirror else 1
    if flip:
        sgn_x, sgn_y = -sgn_x, -1
    else:
        sgn_y = 1
    P = lambda x, y: (cx + x * sgn_x, cy + y * sgn_y)
    (g.pen(*P(sx, 0), 1.0)
        .to(*P(ex, ey), (0, -sgn_y), (-0.5 * sgn_x, -sgn_y), k=0.62, w=0.62)
        .end())


def _comma_ext(g: G):
    """Total height of a comma (dot top to tail ink bottom)."""
    d = _d(g)
    return d + _tail(g) + g.hh * 0.62 * 0.9


def _dash(g: G, length, cy=DASH_Y):
    g.bar(0, length, cy)


# ---------------------------------------------------------------------------
# dots, commas, colons
# ---------------------------------------------------------------------------

@glyph("period", 0x2E)
def period(g: G):
    d = _d(g)
    g.dot(0, d / 2, d)


@glyph("comma", 0x2C)
def comma(g: G):
    d = _d(g)
    _comma(g, 0, d / 2)


@glyph("quotesinglbase", 0x201A)
def quotesinglbase(g: G):
    comma(g)


@glyph("quotedblbase", 0x201E)
def quotedblbase(g: G):
    d = _d(g)
    p = _qpitch(g)
    _comma(g, 0, d / 2)
    _comma(g, p, d / 2)


@glyph("colon", 0x3A)
def colon(g: G):
    d = _d(g)
    g.dot(0, d / 2, d)
    g.dot(0, g.xh - d / 2, d)


@glyph("semicolon", 0x3B)
def semicolon(g: G):
    d = _d(g)
    _comma(g, 0, d / 2)
    g.dot(0, g.xh - d / 2, d)


@glyph("ellipsis", 0x2026)
def ellipsis(g: G):
    if g.mono:
        d = g.W * 0.7 + 30
        width = 470 + g.grow * 0.72
        pitch = (width - d) / 2
    else:
        d = _d(g)
        pitch = d + 96 + g.grow * 0.1
    for i in range(3):
        g.dot(i * pitch, d / 2, d)


@glyph("periodcentered", 0xB7)
def periodcentered(g: G):
    d = _d(g)
    g.dot(0, DASH_Y + 4, d)


@glyph("periodcentered.loclCAT")
def periodcentered_cat(g: G):
    periodcentered(g)
    if not g.mono:
        g.lsb = g.rsb = 14 + g.grow * 0.05


@glyph("periodcentered.case")
def periodcentered_case(g: G):
    d = _d(g)
    g.dot(0, DASH_Y + 4 + CASE_DY, d)


# ---------------------------------------------------------------------------
# exclamation & question
# ---------------------------------------------------------------------------

def _exclam(g: G, x=0.0):
    d = _d(g)
    yb = d + 76 + g.grow * 0.2
    (g.pen(x, g.cap - g.hh, 1.0).l(x, yb + g.hh * 0.88, 0.88).end())
    g.dot(x, d / 2, d)


@glyph("exclam", 0x21)
def exclam(g: G):
    _exclam(g)


@glyph("exclamdown", 0xA1)
def exclamdown(g: G):
    # rotate about a centre that puts the dot top on x-height
    _rot_glyph(g, _exclam, g.xh / 2)


@glyph("exclamdown.case")
def exclamdown_case(g: G):
    _rot_glyph(g, _exclam, g.cap / 2)


def _rot_glyph(g: G, fn, cy):
    """Draw fn rotated 180 degrees about (0, cy) (dots included)."""
    n0 = len(g.extra)
    g.transform(rot180(0, cy))
    fn(g)
    g.transform(None)
    T = rot180(0, cy)
    g.extra[n0:] = [c.transform(T) for c in g.extra[n0:]]


def _question(g: G, with_bang=False):
    """?: round hook whose right side swings in one even S onto a short straight
    stem above the dot."""
    bw = g.wd(392, 400, grow=0.5)
    cx = bw / 2
    sx = cx - 8 + g.grow * 0.2
    d = _d(g)
    yb = d + 70 - g.grow * 0.1            # ink bottom of the stem
    top = g.cap + g.ov
    yr = g.cap * 0.71                     # right extreme of the hook
    # the straight stem is > 0 in every master (it used to run backwards in the
    # heavy masters, so the hook ran into the dot in heavy Mono)
    ys = yb + g.hh * 0.88 + 110 - g.grow * 0.9
    sy = yr - ys
    p = (g.pen(g.hw + 4, g.cap * 0.74)
         .to(cx, top - g.hh, (0.3, 1), "r", k=0.62)
         .h(bw - g.hw, yr, k=0.6))
    p.c((bw - g.hw, yr - sy * 0.5), (sx, ys + sy * 0.5), (sx, ys))
    p.l(sx, yb + g.hh * 0.88, 0.88).end()
    if with_bang:
        (g.pen(sx, g.cap - g.hh, 1.0).l(sx, ys, 1.0).end())
    g.dot(sx, d / 2, d)
    return sx


@glyph("question", 0x3F)
def question(g: G):
    _question(g)


@glyph("uni2E2E", 0x2E2E)
def questionreversed(g: G):
    bw = g.wd(392, 400, grow=0.5)
    n0 = len(g.extra)
    g.transform(mirror_x(bw / 2))
    _question(g)
    g.transform(None)
    g.extra[n0:] = [c.transform(mirror_x(bw / 2)) for c in g.extra[n0:]]


@glyph("questiondown", 0xBF)
def questiondown(g: G):
    _rot_glyph(g, _question, g.xh / 2)


@glyph("questiondown.case")
def questiondown_case(g: G):
    _rot_glyph(g, _question, g.cap / 2)


@glyph("uni203D", 0x203D)
def interrobang(g: G):
    _question(g, with_bang=True)


# ---------------------------------------------------------------------------
# quotes
# ---------------------------------------------------------------------------

def _qpitch(g: G):
    return _d(g) + 62 + g.grow * 0.25


def _qright(g: G, x, mirror=False):
    d = _d(g)
    _comma(g, x, g.cap - d / 2 + 4, mirror=mirror)


def _qleft(g: G, x):
    d = _d(g)
    cy = g.cap + 4 - _comma_ext(g) + d / 2
    _comma(g, x, cy, flip=True)


@glyph("quoteright", 0x2019)
def quoteright(g: G):
    _qright(g, 0)


@glyph("quoteleft", 0x2018)
def quoteleft(g: G):
    _qleft(g, 0)


@glyph("quotereversed", 0x201B)
def quotereversed(g: G):
    _qright(g, 0, mirror=True)


@glyph("quotedblright", 0x201D)
def quotedblright(g: G):
    _qright(g, 0)
    _qright(g, _qpitch(g))


@glyph("quotedblleft", 0x201C)
def quotedblleft(g: G):
    _qleft(g, 0)
    _qleft(g, _qpitch(g))


@glyph("uni201F", 0x201F)
def quotedblreversed(g: G):
    _qright(g, 0, mirror=True)
    _qright(g, _qpitch(g), mirror=True)


def _tick(g: G, x):
    """Straight quote: tapering vertical stroke hanging from cap height."""
    top = g.cap + 4
    (g.pen(x, top - g.hh, 1.0).l(x, top - 236 - g.grow * 0.25 + g.hh * 0.72, 0.72).end())


@glyph("quotesingle", 0x27)
def quotesingle(g: G):
    _tick(g, 0)


@glyph("quotedbl", 0x22)
def quotedbl(g: G):
    _tick(g, 0)
    _tick(g, g.W + 84 + g.grow * 0.2)


# ---------------------------------------------------------------------------
# guillemets
# ---------------------------------------------------------------------------

def _chev(g: G, x, cy, left=True):
    """Chevron with ink tip at x (pointing left) or ink tip at x+width (right)."""
    w = DIAG
    wd = 168 + g.grow * 0.35
    hs = 150 + g.grow * 0.12
    rx = g.hw * w
    tip = x + rx
    if left:
        g.line(tip, cy, tip + wd, cy + hs, w)
        g.line(tip + NUDGE, cy, tip + wd, cy - hs, w)
    else:
        g.line(tip + wd, cy, tip, cy + hs, w)
        g.line(tip + wd - NUDGE, cy, tip, cy - hs, w)


def _gpitch(g: G):
    return 150 + g.grow * 0.62


GUIL_Y = 274


def _guil(g: G, n, left, dy=0.0):
    for i in range(n):
        _chev(g, i * _gpitch(g), GUIL_Y + dy, left)


for _nm, _cp, _n, _left in (("guilsinglleft", 0x2039, 1, True), ("guilsinglright", 0x203A, 1, False),
                            ("guillemotleft", 0xAB, 2, True), ("guillemotright", 0xBB, 2, False)):
    def _mk(n=_n, left=_left):
        def f(g: G):
            _guil(g, n, left)

        def fc(g: G):
            _guil(g, n, left, CASE_DY)
        return f, fc
    _f, _fc = _mk()
    glyph(_nm, _cp)(_f)
    glyph(_nm + ".case")(_fc)


# ---------------------------------------------------------------------------
# dashes
# ---------------------------------------------------------------------------

def _hyph_len(g: G):
    return g.wd(280, 330, grow=0.4)


@glyph("hyphen", 0x2D)
def hyphen(g: G):
    _dash(g, _hyph_len(g))


@glyph("hyphen.case")
def hyphen_case(g: G):
    _dash(g, _hyph_len(g), DASH_Y + CASE_DY)


def _en_len(g: G):
    return 470 + g.grow * 0.3 if g.mono else 480 + g.grow * 0.3


def _em_len(g: G):
    return 560 + g.grow * 0.2 if g.mono else 920


@glyph("endash", 0x2013)
def endash(g: G):
    _dash(g, _en_len(g))
    if not g.mono:
        g.lsb = g.rsb = 40 + g.grow * 0.05


@glyph("endash.case")
def endash_case(g: G):
    _dash(g, _en_len(g), DASH_Y + CASE_DY)
    if not g.mono:
        g.lsb = g.rsb = 40 + g.grow * 0.05


@glyph("emdash", 0x2014)
def emdash(g: G):
    _dash(g, _em_len(g))
    if not g.mono:
        g.lsb = g.rsb = 40


@glyph("emdash.case")
def emdash_case(g: G):
    _dash(g, _em_len(g), DASH_Y + CASE_DY)
    if not g.mono:
        g.lsb = g.rsb = 40


@glyph("figuredash", 0x2012)
def figuredash(g: G):
    if g.mono:
        _dash(g, 470 + g.grow * 0.3)
        return
    _dash(g, 470 + g.grow * 0.25)
    g.advance = 560 + g.grow * 0.25


@glyph("horizontalbar", 0x2015)
def horizontalbar(g: G):
    if g.mono:
        _dash(g, 600 + g.hw)
        return
    _dash(g, 980)
    g.lsb = g.rsb = 10


@glyph("underscore", 0x5F)
def underscore(g: G):
    ln = (600 + g.hw) if g.mono else (500 + g.grow * 0.4)
    g.bar(0, ln, -132)
    g.lsb = g.rsb = -g.hw * 0.5


@glyph("uni2017", 0x2017)
def underscoredbl(g: G):
    ln = (600 + g.hw) if g.mono else (500 + g.grow * 0.4)
    g.bar(0, ln, -110 + g.grow * 0.1)
    g.bar(0, ln, -110 - g.H - 46 - g.grow * 0.35)
    g.lsb = g.rsb = -g.hw * 0.5


# ---------------------------------------------------------------------------
# enclosures
# ---------------------------------------------------------------------------

def _arc_to(p, x, y, d0, w=None):
    """Append an exact circular arc (one cubic) from the pen's current point to
    (x, y), leaving along d0.  Unlike .to(), the handles are not softened, so
    shallow arcs keep an even curvature instead of bunching it in the middle."""
    x0, y0 = p.cur
    dx, dy = x - x0, y - y0
    ch = math.hypot(dx, dy)
    a = math.hypot(*d0)
    ax, ay = d0[0] / a, d0[1] / a
    # half the turning angle = angle between the start tangent and the chord
    cosb = max(-1.0, min(1.0, (ax * dx + ay * dy) / ch))
    beta = math.acos(cosb)
    if beta < 1e-6:
        return p.l(x, y, w)
    cr = ax * dy - ay * dx
    # end tangent: the start tangent reflected about the chord's normal
    ux, uy = dx / ch, dy / ch
    dot = ax * ux + ay * uy
    bx, by = 2 * dot * ux - ax, 2 * dot * uy - ay
    R = ch / (2 * math.sin(beta))
    hl = 4.0 / 3.0 * math.tan(beta / 2) * R
    _ = cr
    return p.c((x0 + ax * hl, y0 + ay * hl), (x - bx * hl, y - by * hl), (x, y), w)


def _paren(g: G, dy=0.0):
    """Parenthesis: one even circular arc (Nunito-like), round caps."""
    bw = g.wd(196, 212, grow=0.55)
    top, bot = TOP + dy, BOT + dy
    mid = (top + bot) / 2
    xr = bw - g.hw
    xl = g.hw
    e = g.hh * 0.86
    h = top - e - mid                     # half chord (skeleton)
    sx = xr - xl                          # sagitta
    R = (sx * sx + h * h) / (2 * sx)
    cx = xl + R                           # circle centre (cx, mid)
    # tangent at the top end, heading down-left (perpendicular to the radius)
    t0 = (-(top - e - mid), -(cx - xr))
    p = g.pen(xr, top - e)
    _arc_to(p, xl, mid, t0)
    _arc_to(p, xr, bot + e, (0, -1))
    p.end()
    return bw


def _bracket(g: G, dy=0.0):
    bw = g.wd(186, 200, grow=0.45)
    top, bot = TOP + dy, BOT + dy
    g.stem(0, bot, top)
    g.bar(0, bw, top - g.hh)
    g.bar(0, bw, bot + g.hh)
    return bw


def _brace(g: G, dy=0.0):
    bw = g.wd(236, 300, grow=0.9)
    top, bot = TOP + dy, BOT + dy
    mid = (top + bot) / 2
    sc = 1.0 - 0.0011 * g.grow           # braces lighten a little when heavy
    xv = bw * 0.47 + g.hw * 0.2          # vertical part (skeleton)
    xr = bw - g.hw * 0.8                 # end of the arms
    xt = g.hw                            # tip
    rad = 64 + g.grow * 0.5
    rt = 60 + g.grow * 0.5
    for s in (1, -1):
        yt = mid + s * (top - mid - g.hh)
        (g.pen(xr, yt)
            .l(xv + rad, yt)
            .h(xv, yt - s * rad, k=0.58)
            .l(xv, mid + s * rt)
            .v(xt, mid, k=0.6)
            .end(scale=sc))
    return bw


def _angle(g: G, dy=0.0):
    bw = g.wd(200, 220, grow=0.5)
    top, bot = TOP + dy, BOT + dy
    mid = (top + bot) / 2
    rx = g.hw * DIAG
    e = g.hh * DIAG * 0.9
    g.line(rx, mid, bw - rx, top - e, DIAG)
    g.line(rx + NUDGE, mid, bw - rx, bot + e, DIAG)
    return bw


def _mirrored(fn, dy=0.0):
    def f(g: G):
        # draw once to learn the width, then mirror
        probe = G(g.p, g.name)
        bw = fn(probe, dy)
        g.transform(mirror_x(bw / 2))
        fn(g, dy)
        g.transform(None)
    return f


for _base, _fn, _cl, _cr in (("paren", _paren, 0x28, 0x29), ("bracket", _bracket, 0x5B, 0x5D),
                             ("brace", _brace, 0x7B, 0x7D)):
    glyph(_base + "left", _cl)(lambda g, fn=_fn: fn(g))
    glyph(_base + "right", _cr)(_mirrored(_fn))
    glyph(_base + "left.case")(lambda g, fn=_fn: fn(g, ENC_DY))
    glyph(_base + "right.case")(_mirrored(_fn, ENC_DY))

glyph("uni27E8", 0x27E8)(lambda g: _angle(g))
glyph("uni27E9", 0x27E9)(_mirrored(_angle))
glyph("uni27E8.case")(lambda g: _angle(g, ENC_DY))
glyph("uni27E9.case")(_mirrored(_angle, ENC_DY))


# ---------------------------------------------------------------------------
# slashes and bars
# ---------------------------------------------------------------------------

def _slash(g: G, back=False):
    dx = g.wd(300, 330, grow=0.4)
    rx = g.hw * DIAG
    e = g.hh * DIAG * 0.8
    if back:
        g.line(rx, TOP - e, rx + dx, BOT + e, DIAG)
    else:
        g.line(rx, BOT + e, rx + dx, TOP - e, DIAG)


@glyph("slash", 0x2F)
def slash(g: G):
    _slash(g)


@glyph("backslash", 0x5C)
def backslash(g: G):
    _slash(g, back=True)


@glyph("bar", 0x7C)
def bar(g: G):
    g.stem(0, BOT - 40, TOP + 20)


@glyph("brokenbar", 0xA6)
def brokenbar(g: G):
    mid = (TOP + BOT) / 2 - 10
    gap = 50 + g.grow * 0.3
    g.stem(0, BOT - 40, mid - gap)
    g.stem(0, mid + gap, TOP + 20)


@glyph("uni2016", 0x2016)
def dblverticalbar(g: G):
    g.stem(0, BOT - 40, TOP + 20)
    g.stem(g.W + 90 + g.grow * 0.2, BOT - 40, TOP + 20)


# ---------------------------------------------------------------------------
# @ & * # ^
# ---------------------------------------------------------------------------

def _at(g: G, dy=0.0):
    """@: a round single-storey a (closed loop ridden by its stem, as in d / q)
    wrapped by a ring that springs from the stem's foot."""
    from .latin_lower import loop, EPS
    if g.mono:
        bw = g.wd(0, 530, grow=0.9)
        y0, y1 = -150 - g.grow * 0.3, 690 + g.grow * 0.3
        ih = 162 + g.grow * 0.32
        iw = 252 + g.grow * 0.6
        w = 0.88 - 0.0022 * g.grow        # Mono: lighter as it gets heavier, to fit the cell
        cx = bw / 2 + 4
    else:
        bw = g.wd(800, grow=1.5)
        y0, y1 = -150 - g.grow * 0.25, 700 + g.grow * 0.25
        ih = 172 + g.grow * 0.5
        iw = 290 + g.grow * 1.45
        w = 1.0
        cx = bw / 2 - 6
    hw, hh = g.hw * w, g.hh * w
    y0 += dy
    y1 += dy
    cy = (y0 + y1) / 2
    xs = cx + iw * 0.5 - hw               # stem skeleton
    ix0 = cx - iw * 0.5                   # inner bowl left ink
    ib0, ib1 = cy - ih, cy + ih
    # inner bowl: complete round loop whose right side lies on the stem
    run = 10 + (g.W - 22) * 0.5
    loop(g, ix0 + hw, ib0 + hh, xs - EPS, ib1 - hh, cy - run / 2, cy + run / 2, w=w)
    # stem riding the bowl, turning at its foot into the outer ring
    xr = bw - hw
    fx = xs + (xr - xs) * 0.45
    rv = 40 + hw * 1.1                    # foot radius (always above the pen radius)
    (g.pen(xs, ib1 - hh, w)
        .l(xs, ib0 + hh + rv)
        .v(fx, ib0 + hh, k=0.6)
        .h(xr, cy + 10, k=0.6)
        .v(bw / 2, y1 - hh, k=0.58)
        .h(hw, cy, k=0.58)
        .v(bw / 2, y0 + hh, k=0.58)
        .to(bw * 0.8, y0 + hh + 28 + g.grow * 0.1, "r", (1, 0.22), k=0.6)
        .end())


@glyph("at", 0x40)
def at(g: G):
    _at(g)


@glyph("at.case")
def at_case(g: G):
    _at(g, 70)


@glyph("ampersand", 0x26)
def ampersand(g: G):
    """&: round lower bowl that rises in one smooth S through the crossing into a
    small top loop, whose left side falls as the straight-ish leg."""
    bw = g.wd(612, 480, grow=0.7)
    cap = g.cap
    top = cap + g.ov
    lxl = (64 if not g.mono else 40) + g.hw * 0.8            # upper loop left (skel)
    lxr = bw * 0.60 - g.hw * 0.2 + g.grow * 0.25             # upper loop right (skel)
    lcx = (lxl + lxr) / 2
    lmy = cap * 0.785 - g.grow * 0.32
    yl = cap * 0.23                                          # bowl's left extreme
    leg = (bw - g.hw * 0.95 + g.grow * 0.15, g.hh)
    p = (g.pen(bw - g.hw - 4, cap * 0.42 + g.grow * 0.4)
         .to(bw * 0.43, -g.ov + g.hh, (-0.28, -1), "l", k=0.62)
         .h(g.hw, yl, k=0.6))
    # S from the bowl's left side up to the loop's right side (parallel tangents,
    # so the handles are set directly: an even, diagonal middle)
    dy = lmy - yl
    p.c((g.hw, yl + dy * 0.5), (lxr, lmy - dy * 0.46), (lxr, lmy))
    (p.v(lcx, top - g.hh, k=0.6)
        .h(lxl, lmy - 6, k=0.6)
        .to(leg[0], leg[1], "d", (0.82, -1), k=0.5)
        .end())


@glyph("asterisk", 0x2A)
def asterisk(g: G):
    R = 158 + g.grow * 0.35
    cy = g.cap - R - (0 if not g.mono else 20) + 6
    w = 0.9
    for a in (90, 30, 150):
        t = math.radians(a)
        ex, ey = math.cos(t) * (R - g.hw * w), math.sin(t) * (R - g.hh * w)
        g.line(-ex, cy - ey, ex, cy + ey, w)


@glyph("numbersign", 0x23)
def numbersign(g: G):
    bw = g.wd(548, 480, grow=0.6)
    sl = 40
    h0, h1 = 0, g.cap
    w = 0.96
    for fx in (0.33, 0.70):
        xb = bw * fx - sl / 2 - 6
        g.line(xb, h0 + g.hh * w, xb + sl, h1 - g.hh * w, w)
    for fy in (0.335, 0.665):
        g.bar(0 if fy < 0.5 else sl * 0.3, bw - (sl * 0.3 if fy < 0.5 else 0), g.cap * fy, w=1.0)


@glyph("asciicircum", 0x5E)
def asciicircum(g: G):
    bw = g.wd(400, 420, grow=0.5)
    rx = g.hw * DIAG
    e = g.hh * DIAG
    y0 = g.cap - 330 - g.grow * 0.2
    g.line(rx, y0 + e, bw / 2, g.cap - e, DIAG)
    g.line(bw - rx, y0 + e, bw / 2 + NUDGE, g.cap - e, DIAG)


# ---------------------------------------------------------------------------
# reference marks
# ---------------------------------------------------------------------------

@glyph("dagger", 0x2020)
def dagger(g: G):
    bw = g.wd(380, 400, grow=0.5)
    cx = bw / 2
    g.vstem(cx, BOT, g.cap)
    g.bar(0, bw, g.cap - 216)


@glyph("daggerdbl", 0x2021)
def daggerdbl(g: G):
    bw = g.wd(380, 400, grow=0.5)
    cx = bw / 2
    g.vstem(cx, BOT, g.cap)
    g.bar(0, bw, g.cap - 216)
    g.bar(0, bw, BOT + 216 - 30)


@glyph("section", 0xA7)
def section(g: G):
    bw = g.wd(410, 420, grow=0.6)
    y_hi, y_lo = g.cap + g.ov, -140
    cy = (y_hi + y_lo) / 2
    cx = bw / 2
    rr = 156 + g.grow * 0.5          # ring half-height (ink)
    L, R = g.hw, bw - g.hw
    T = lambda p: p
    for tf in (None, rot180(cx, cy)):
        g.transform(tf)
        (g.pen(R - 10, y_hi - 128)
            .to(cx, y_hi - g.hh, (-0.4, 1), "l", k=0.62)
            .h(L, y_hi - 148 - g.grow * 0.25, k=0.6)
            .v(cx, cy + rr - g.hh, k=0.56)
            .h(R, cy, k=0.58)
            .v(cx, cy - rr + g.hh, k=0.58)
            .h(L, cy, k=0.58)
            .end())
        g.transform(None)


@glyph("paragraph", 0xB6)
def paragraph(g: G):
    from ..geometry import Contour
    bw = g.wd(440, 440, grow=0.6)
    top = g.cap
    s1 = bw * 0.56            # left stem left ink
    s2 = bw - g.W             # right stem left ink
    g.stem(s1, BOT + 20, top - g.hh)
    g.stem(s2, BOT + 20, top - g.hh)
    g.bar(s1, bw, top - g.hh)
    g.bar(s1 - 4, s1 + g.W, top - g.hh)
    # filled bowl
    yb = top * 0.40
    xr = s1 + g.hw
    x0 = 0
    cyb = (top + yb) / 2
    k = 0.58
    c = Contour((xr, top))
    c.ops.append(("line", (xr - (xr - x0) * 0.42, top)))
    c.ops.append(("curve", (xr - (xr - x0) * (0.42 + 0.58 * k), top), (x0, top - (top - cyb) * (1 - k)), (x0, cyb)))
    c.ops.append(("curve", (x0, yb + (cyb - yb) * (1 - k)), (xr - (xr - x0) * (0.42 + 0.58 * k), yb),
                  (xr - (xr - x0) * 0.42, yb)))
    c.ops.append(("line", (xr, yb)))
    c.ops.append(("line", (xr, top)))
    g.extra.append(c)


# ---------------------------------------------------------------------------
# bullets
# ---------------------------------------------------------------------------

def _bul_d(g: G):
    return 196 + g.grow * 0.62


@glyph("bullet", 0x2022)
def bullet(g: G):
    g.dot(0, DASH_Y, _bul_d(g))


@glyph("bullet.case")
def bullet_case(g: G):
    g.dot(0, DASH_Y + CASE_DY, _bul_d(g))


@glyph("uni2023", 0x2023)
def trianglebullet(g: G):
    from ..geometry import Contour
    s = _bul_d(g) * 1.12
    h = s * 0.58
    r = 16 + g.grow * 0.08
    cy = DASH_Y
    pts = [(0, cy - h), (s * 0.92, cy), (0, cy + h)]
    g.extra.append(_rpoly(pts, r))


@glyph("uni2043", 0x2043)
def hyphenbullet(g: G):
    g.bar(0, _bul_d(g) * 1.3, DASH_Y, scale=1.2)


def _rpoly(pts, r, k=0.6):
    """Filled CCW polygon with rounded corners (Contour)."""
    from ..geometry import Contour
    area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))
    if area < 0:
        pts = pts[::-1]
    n = len(pts)
    rs = r if isinstance(r, (list, tuple)) else [r] * n
    corners = []
    for i in range(n):
        p, a, b = pts[i], pts[i - 1], pts[(i + 1) % n]
        la = math.hypot(a[0] - p[0], a[1] - p[1])
        lb = math.hypot(b[0] - p[0], b[1] - p[1])
        ri = rs[i]
        p1 = (p[0] + (a[0] - p[0]) / la * ri, p[1] + (a[1] - p[1]) / la * ri)
        p2 = (p[0] + (b[0] - p[0]) / lb * ri, p[1] + (b[1] - p[1]) / lb * ri)
        corners.append((p1, p, p2))
    c = Contour(corners[0][2])
    for i in list(range(1, n)) + [0]:
        p1, p, p2 = corners[i]
        c.ops.append(("line", p1))
        c.ops.append(("curve", (p1[0] + (p[0] - p1[0]) * k, p1[1] + (p[1] - p1[1]) * k),
                      (p2[0] + (p[0] - p2[0]) * k, p2[1] + (p[1] - p2[1]) * k), p2))
    return c


# ---------------------------------------------------------------------------
# spacing accents (drawn from the combining marks)
# ---------------------------------------------------------------------------

for _nm, _cp, _src in (
        ("grave", 0x60, "gravecomb"), ("acute", 0xB4, "acutecomb"), ("dieresis", 0xA8, "dieresiscomb"),
        ("macron", 0xAF, "macroncomb"), ("cedilla", 0xB8, "cedillacomb"),
        ("circumflex", 0x2C6, "circumflexcomb"), ("caron", 0x2C7, "caroncomb"),
        ("breve", 0x2D8, "brevecomb"), ("dotaccent", 0x2D9, "dotaccentcomb"),
        ("ring", 0x2DA, "ringcomb"), ("ogonek", 0x2DB, "ogonekcomb"), ("tilde", 0x2DC, "tildecomb"),
        ("hungarumlaut", 0x2DD, "hungarumlautcomb"), ("uni02C9", 0x2C9, "macroncomb"),
        ("uni02CA", 0x2CA, "acutecomb"), ("uni02CB", 0x2CB, "gravecomb")):
    def _mk(src=_src):
        def f(g: G):
            g.include(src)
        return f
    glyph(_nm, _cp)(_mk())
