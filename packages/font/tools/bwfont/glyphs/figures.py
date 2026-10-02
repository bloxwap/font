"""Figures: tabular lining digits (default), proportional `.pnum`, alternates
(ss02 open digits, ss06 flat-top 3 / plain 1, slashed zero), numerics
(sups/subs/numr/dnom + Unicode super/subscripts), fractions, percent family,
ordinals, numero and circled digits.

Shapes take their spirit from Nunito's figures (see DESIGN.md: spirit only,
nothing traced or measured): round, elliptical bowls rather than the squarish
Latin curves, a footed 1, and 6/9 whose stems are one continuous arc.

Default digits are TABULAR: in Sans every digit has the same advance
(`fig_adv`), ink centred automatically; in Mono they sit in the 600 cell.
"""
from __future__ import annotations

import math

from ..skeleton import G, GLYPHS, derive, glyph, _transform_stroke

JOIN = 0.52      # bowls / arches emerging from stems
DIAG = 0.92      # diagonals a touch lighter than stems
KF = 0.56        # figure curve tension: rounder than the Latin 0.58-0.62
LEAD = 0.84      # width where a bowl rides along a stroke before peeling off (as latin_lower)


def circ(path, x, y, u=None, v=None, w=None):
    """Append a true circular arc from the path's current point to (x, y), given
    the unit tangent at the start (u) or at the end (v).  Terminals drawn this way
    keep the bowl's even curvature to the very end (no hook from an over-turned
    tangent).  Raw cubic, so soften() does not touch it."""
    x0, y0 = path.cur
    dx, dy = x - x0, y - y0
    L = math.hypot(dx, dy)
    c = (dx / L, dy / L)
    t = u if u is not None else v
    n = math.hypot(*t)
    t = (t[0] / n, t[1] / n)
    d = c[0] * t[0] + c[1] * t[1]
    o = (2 * d * c[0] - t[0], 2 * d * c[1] - t[1])     # t reflected across the chord
    u, v = (t, o) if u is not None else (o, t)
    half = math.acos(max(-1.0, min(1.0, d)))           # half the turning angle
    if half < 1e-6:
        return path.l(x, y, w=w)
    R = L / (2 * math.sin(half))
    h = 4 / 3 * math.tan(half / 2) * R
    return path.c((x0 + u[0] * h, y0 + u[1] * h), (x - v[0] * h, y - v[1] * h), (x, y), w=w)

# numerics (superiors, numerators, ...)
NUM_S = 0.58     # skeleton scale of small figures


def num_ws(g: G):
    """Stroke-weight factor of small figures (lighter in heavy weights so
    counters stay open)."""
    return 0.80 - g.grow * 0.0016


def num_sx(g: G):
    """Horizontal scale of small figures: a little wider as weight grows."""
    return NUM_S + g.grow * (0.0010 if g.mono else 0.0005)


def fig_adv(g: G):
    return round(560 + g.grow * 0.5)


def tab(g: G):
    """Make the glyph tabular (Sans: fixed figure advance; Mono: the cell)."""
    if not g.mono:
        g.advance = fig_adv(g)


def rot180(cx, cy):
    return lambda p: (2 * cx - p[0], 2 * cy - p[1])


# ---------------------------------------------------------------------------
# small geometry helpers
# ---------------------------------------------------------------------------

def _cubic(p0, p1, p2, p3, t):
    mt = 1 - t
    a, b, c, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _cubic_d(p0, p1, p2, p3, t):
    mt = 1 - t
    return (3 * mt * mt * (p1[0] - p0[0]) + 6 * mt * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0]),
            3 * mt * mt * (p1[1] - p0[1]) + 6 * mt * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1]))


def _x_at_y(pts, y):
    """x of a y-monotonic cubic at height y (bisection)."""
    lo, hi = 0.0, 1.0
    up = pts[3][1] > pts[0][1]
    for _ in range(50):
        mid = (lo + hi) / 2
        if (_cubic(*pts, mid)[1] < y) == up:
            lo = mid
        else:
            hi = mid
    return _cubic(*pts, (lo + hi) / 2)[0]


def _tangent_point(pts, T):
    """Point on cubic `pts` where the line from T touches it tangentially."""
    best = None
    prev = None
    N = 200
    for i in range(N + 1):
        t = i / N
        P = _cubic(*pts, t)
        d = _cubic_d(*pts, t)
        v = (T[0] - P[0]) * d[1] - (T[1] - P[1]) * d[0]
        if prev is not None and (v > 0) != (prev[1] > 0):
            best = t
            break
        prev = (t, v)
    if best is None:
        best = 0.5
    return _cubic(*pts, best)


def oval_quarter(x0, y0, x1, y1, k, quad):
    """Control points of one quarter of `G.ovalc(x0,y0,x1,y1,k)` (skeleton
    box).  quad: 'tl' top->left, 'bl' left->bottom, 'br' bottom->right,
    'tr' right->top (counter-clockwise like ovalc)."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if quad == "tl":
        return ((cx, y1), (cx + (x0 - cx) * k, y1), (x0, cy + (y1 - cy) * k), (x0, cy))
    if quad == "bl":
        return ((x0, cy), (x0, cy + (y0 - cy) * k), (cx + (x0 - cx) * k, y0), (cx, y0))
    if quad == "br":
        return ((cx, y0), (cx + (x1 - cx) * k, y0), (x1, cy + (y0 - cy) * k), (x1, cy))
    return ((x1, cy), (x1, cy + (y1 - cy) * k), (cx + (x1 - cx) * k, y1), (cx, y1))


# ---------------------------------------------------------------------------
# pieces: reuse another glyph's skeleton, scaled, with weight re-applied
# ---------------------------------------------------------------------------

class Piece:
    def __init__(self, g: G, name, sx=1.0, sy=None, ws=1.0):
        sy = sx if sy is None else sy
        sub = G(g.p, name)
        GLYPHS[name].func(sub)
        T = lambda p: (p[0] * sx, p[1] * sy)
        self.g = g
        self.strokes = []
        for st in sub.strokes:
            s2 = _transform_stroke(st, T)
            s2.scale *= ws
            self.strokes.append(s2)
        self.extra = []
        for cn in sub.extra:
            pts = list(cn.points())
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            k = (sx + sy) / 2 * 0.5 + ws * 0.5
            nc = T((cx, cy))
            self.extra.append(cn.transform(lambda p, cx=cx, cy=cy, nc=nc, k=k:
                                           (nc[0] + (p[0] - cx) * k, nc[1] + (p[1] - cy) * k)))
        self.box = stroke_box(g, self.strokes, self.extra)

    @property
    def w(self):
        return self.box[2] - self.box[0]

    @property
    def h(self):
        return self.box[3] - self.box[1]

    def put(self, dx, dy=0.0):
        g = self.g
        T = lambda p: (p[0] + dx, p[1] + dy)
        for st in self.strokes:
            g._add(_transform_stroke(st, T))
        for cn in self.extra:
            c2 = cn.transform(T)
            if g._tx is not None:
                c2 = c2.transform(g._tx)
            g.extra.append(c2)
        return self


def stroke_box(g: G, strokes, extra=()):
    """Approximate ink box of skeleton strokes (sampled, pen radii added)."""
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    for st in strokes:
        for i, sg in enumerate(st.segs):
            w = max(st.widths[i], st.widths[i + 1]) * st.scale
            rx, ry = g.hw * w, g.hh * w
            if sg.kind == "line":
                pts = list(sg.pts)
            else:
                pts = [_cubic(*sg.pts, j / 12) for j in range(13)]
            for (x, y) in pts:
                x0, x1 = min(x0, x - rx), max(x1, x + rx)
                y0, y1 = min(y0, y - ry), max(y1, y + ry)
    for cn in extra:
        for (x, y) in cn.points():
            x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
    return (x0, y0, x1, y1)


def fit_cell(g: G, limit=566):
    """Mono: squeeze the drawn skeleton horizontally so the ink fits the cell
    (only kicks in for wide symbols at heavy weights; topology unchanged)."""
    if not g.mono:
        return
    x0, _, x1, _ = stroke_box(g, g.strokes, g.extra)
    w = x1 - x0
    pw = g.W
    if w <= limit:
        return
    f = (limit - pw) / (w - pw)
    T = lambda p: (x0 + (p[0] - x0) * f, p[1])
    g.strokes = [_transform_stroke(st, T) for st in g.strokes]
    g.extra = [c.transform(T) for c in g.extra]


# ---------------------------------------------------------------------------
# digit skeletons (ink starts at x = 0)
# ---------------------------------------------------------------------------

def d_zero(g: G, slash=False):
    bw = g.wd(486, 456)
    l, r = g.hw, bw - g.hw
    b, t = -g.ov + g.hh, g.cap + g.ov - g.hh
    k = 0.57
    ry = (t - b) * 0.47            # nearly elliptical; a short straight run keeps it from going limp
    cx = bw / 2
    cy = (b + t) / 2
    (g.pen(cx, t).h(l, t - ry, k=k).l(l, b + ry).v(cx, b, k=k)
        .h(r, b + ry, k=k).l(r, t - ry).v(cx, t, k=k).close())
    if slash:
        # wall-to-wall slash, ends buried in the walls' centre-lines
        dy = (t - b) * 0.27
        ylo, yhi = cy - dy, cy + dy
        bl = ((l, b + ry), (l, b + ry - ry * k), (cx + (l - cx) * k, b), (cx, b))
        tr = ((r, t - ry), (r, t - ry + ry * k), (cx + (r - cx) * k, t), (cx, t))
        xl = l if ylo >= b + ry else _x_at_y(bl, ylo)
        xr = r if yhi <= t - ry else _x_at_y(tr, yhi)
        g.line(xl, ylo, xr, yhi, 0.8 - g.grow * 0.0012)
    return bw


def d_one(g: G, flag=True, prop=False):
    """Flagged 1 on a foot (the plain ss06 1 has neither)."""
    top = g.cap
    if g.mono:
        bw = g.wd(0, 440)
        xs = bw * 0.54
        g.vstem(xs, 0, top)
        if flag:
            fl = 176 + g.grow * 0.45
            g.line(xs, top - g.hh, xs - fl, top - g.hh - 136 - g.grow * 0.15, DIAG)
        f = 170 + g.grow * 0.3
        g.bar(xs - f, xs + f, g.hh)
        return bw
    fl = (164 if not prop else 152) + g.grow * 0.45
    if not flag:
        g.vstem(g.hw, 0, top)
        return g.W
    f = fl + g.hw * DIAG             # foot reaches as far left as the flag
    xs = f
    g.vstem(xs, 0, top)
    g.line(xs, top - g.hh, xs - fl, top - g.hh - 112 - g.grow * 0.2, DIAG)
    g.bar(0, 2 * f, g.hh)
    return 2 * f


def d_two(g: G):
    """2: a round bowl whose right side keeps turning on one circle until it runs
    straight down the diagonal to the base (no corner where curve meets line), and a
    top terminal that ends as a plain circular arc (no hook)."""
    bw = g.wd(476, 452)
    top = g.cap + g.ov
    cx = bw / 2 + 4
    r = bw - g.hw
    yr = g.cap * 0.66                           # right extreme of the bowl
    R = r - cx                                  # its horizontal radius, kept on the way down
    C = (r - R, yr)                             # centre of that circle
    B = (g.hw + 4, g.hh + 2)                    # foot of the neck (bar's left cap)
    P = (r, yr)
    for _ in range(12):                         # point where the circle's tangent aims at B
        d = (B[0] - P[0], B[1] - P[1])
        n = math.hypot(*d)
        d = (d[0] / n, d[1] / n)
        phi = math.atan2(d[0], -d[1])           # clockwise tangent (sin, -cos) = d
        P = (C[0] + R * math.cos(phi), C[1] + R * math.sin(phi))
    p = g.pen(g.hw + 4, g.cap * 0.80)           # top terminal
    circ(p, cx, top - g.hh, v=(1, 0))
    p.h(r, yr, k=KF)
    circ(p, P[0], P[1], u=(0, -1))
    p.l(B[0], B[1]).end()
    g.bar(0, bw, g.hh)
    return bw


def _three_lower(g: G, bw, jx, jy):
    r = bw - g.hw
    cx = bw / 2
    xj = bw * 0.52
    p = (g.pen(jx, jy).l(xj, jy)
        .h(r, (jy + (-g.ov)) / 2 + g.hh * 0.15, k=KF)
        .v(cx - 4, -g.ov + g.hh, k=KF))
    circ(p, g.hw + 4, g.cap * 0.18, u=(-1, 0)).end()


def d_three(g: G):
    bw = g.wd(476, 448)
    top = g.cap + g.ov
    cx = bw / 2
    r = bw - g.hw - (18 if g.mono else 30)   # upper bowl narrower than the lower (room permitting)
    jy = g.cap * 0.53              # waist just above the middle; lower bowl fuller than the upper
    jx = bw * 0.27                 # a real flat bar at the waist
    p = g.pen(g.hw + 4, g.cap * 0.80)       # top terminal
    circ(p, cx - 4, top - g.hh, v=(1, 0))
    (p.h(r, (top + jy) / 2 + g.hh * 0.1, k=KF)
        .v(bw * 0.48, jy, k=KF)
        .l(jx, jy)
        .end())
    _three_lower(g, bw, jx, jy)
    return bw


def d_three_flat(g: G):
    bw = g.wd(448, 448)
    jy = g.cap * 0.545
    jx = bw * 0.36
    xr = bw - 22 - g.hw * DIAG
    g.bar(14, bw - 22, g.cap - g.hh)
    g.line(xr, g.cap - g.hh, jx, jy, DIAG)
    _three_lower(g, bw, jx, jy)
    return bw


def d_four(g: G, open_=False):
    bw = g.wd(496, 470)
    if g.mono:   # tighter cell: crossbar overhang shrinks so the counter stays open
        xs = bw - 44 - g.grow * 0.05 - g.hw
    else:
        xs = bw - 62 - g.grow * 0.25 - g.hw  # stem centre
    yb = g.cap * 0.28 - g.grow * 0.05         # crossbar centre
    g.bar(0, bw, yb)
    g.vstem(xs, 0, g.cap)
    if open_:
        xt = g.hw + (40 if g.mono else 58)
        g.line(xt, g.cap - g.hh, g.hw, yb, DIAG)
    else:
        g.line(xs, g.cap - g.hh, g.hw * DIAG, yb, DIAG)
    return bw


def d_five(g: G):
    """5: vertical left stroke under a long top bar. The bowl starts exactly where the
    vertical ends and sets off up and to the right at an angle, so the junction is a
    round outer corner below and a clean V-notch above (nothing hangs under it), then
    curves into a broad, low round and ends in a shallow flick like the 3."""
    bw = g.wd(478, 448)
    xv = g.hw + 22                 # left stroke: vertical
    bt = g.cap * 0.60 + g.ov + g.grow * 0.2   # bowl top (ink); rises a little with weight
    yb = g.cap * 0.44 + g.grow * 0.1          # bottom of the vertical = start of the bowl
    g.bar(xv - g.hw, bw - 10, g.cap - g.hh)
    g.line(xv, g.cap - g.hh, xv, yb)
    r = bw - g.hw
    cx = bw * 0.52
    p = (g.pen(xv, yb)
        .to(cx + 10, bt - g.hh, (1.0, 0.8), "r", k=KF)
        .h(r, (bt - g.ov) / 2, k=KF)
        .v(cx - 2, -g.ov + g.hh, k=KF))
    # the terminal drops a little with weight so the aperture under the vertical stays open
    circ(p, g.hw + 4, g.cap * 0.18 - g.grow * 0.3, u=(-1, 0)).end()
    return bw


SIX_W = (484, 450)    # 6 and 9 (sans, mono): about as wide as the round bowl


def d_six(g: G):
    """6: a complete round bowl, with the stem arching over from a terminal that
    curls back down and running down the bowl's left side until it merges, tangent,
    at the bowl's widest point (so the counter stays a true round)."""
    bw = g.wd(*SIX_W)
    top, bot = g.cap + g.ov, -g.ov
    l, r = g.hw, bw - g.hw
    cx = bw / 2
    bt = g.cap * 0.60 + g.ov       # bowl top
    by = (bt + bot) / 2
    ya = g.cap * 0.64              # the straight left side turns into the arch here
    g.oval(0, bot, bw, bt, k=KF)
    (g.pen(r - 10, g.cap * 0.85)
        .to(cx + 8, top - g.hh, (-0.55, 1), "l", k=KF)
        .h(l, ya, k=KF)
        .l(l, by)
        .end())
    return bw


def d_six_straight(g: G):
    """6 with a straight diagonal stem (ss02)."""
    bw = g.wd(474, 462)
    bot = -g.ov
    bt = g.cap * 0.63 + g.ov
    k = 0.6
    g.oval(0, bot, bw, bt, k=k)
    x0, y0, x1, y1 = g.hw, bot + g.hh, bw - g.hw, bt - g.hh
    T = (bw * 0.64 + g.grow * 0.15, g.cap - g.hh)
    P = _tangent_point(oval_quarter(x0, y0, x1, y1, k, "tl"), T)
    g.line(T[0], T[1], P[0], P[1], DIAG)
    return bw


def d_seven(g: G):
    """7: the diagonal starts exactly at the bar's end at full width, so bar and
    diagonal share one round cap there and the corner turns cleanly (no lump), then
    thins to the usual diagonal weight and lands well to the left."""
    bw = g.wd(448, 448)
    K = (bw - g.hw, g.cap - g.hh)               # the bar's skeleton end = the corner
    g.bar(0, bw, K[1])
    g.line(K[0], K[1], bw * 0.20 + g.grow * 0.15, g.hh, 1.0, DIAG)
    return bw


def d_eight(g: G):
    bw = g.wd(494, 464)
    ym = g.cap * 0.555
    ins = 24
    g.oval(ins, ym - g.hh, bw - ins, g.cap + g.ov, k=KF)
    g.oval(0, -g.ov, bw, ym + g.hh, k=KF)
    return bw


def d_nine(g: G):
    bw = g.wd(*SIX_W)
    g.transform(rot180(bw / 2, g.cap / 2))
    d_six(g)
    g.transform(None)
    return bw


def d_nine_straight(g: G):
    bw = g.wd(474, 462)
    g.transform(rot180(bw / 2, g.cap / 2))
    d_six_straight(g)
    g.transform(None)
    return bw


DIGITS = [
    ("zero", 0x30, d_zero),
    ("one", 0x31, d_one),
    ("two", 0x32, d_two),
    ("three", 0x33, d_three),
    ("four", 0x34, d_four),
    ("five", 0x35, d_five),
    ("six", 0x36, d_six),
    ("seven", 0x37, d_seven),
    ("eight", 0x38, d_eight),
    ("nine", 0x39, d_nine),
]
DIGIT_NAMES = [n for n, _, _ in DIGITS]


def _tabular(fn):
    def f(g: G):
        fn(g)
        tab(g)
    return f


for _n, _cp, _fn in DIGITS:
    if _n == "zero":
        # Mono: slashed zero by default (code font); Sans: plain
        def _z(g: G):
            d_zero(g, slash=g.mono)
            tab(g)
        glyph("zero", 0x30, zone="fig")(_z)
        glyph("zero.pnum", zone="fig")(lambda g: d_zero(g, slash=g.mono))
        continue
    glyph(_n, _cp, zone="fig")(_tabular(_fn))
    if _n == "one":
        glyph("one.pnum", zone="fig")(lambda g: d_one(g, prop=True))
    else:
        glyph(_n + ".pnum", zone="fig")(_fn)


@glyph("zero.zero", zone="fig")
def zero_zero(g: G):
    d_zero(g, slash=True)
    tab(g)


@glyph("zero.pnum.zero", zone="fig")
def zero_pnum_zero(g: G):
    d_zero(g, slash=True)


# ss02: open digits ------------------------------------------------------------
glyph("four.ss02", zone="fig")(_tabular(lambda g: d_four(g, open_=True)))
glyph("six.ss02", zone="fig")(_tabular(d_six_straight))
glyph("nine.ss02", zone="fig")(_tabular(d_nine_straight))
glyph("four.pnum.ss02", zone="fig")(lambda g: d_four(g, open_=True))
glyph("six.pnum.ss02", zone="fig")(d_six_straight)
glyph("nine.pnum.ss02", zone="fig")(d_nine_straight)

# ss06: plain 1, flat-top 3 -------------------------------------------------------
glyph("one.ss06", zone="fig")(_tabular(lambda g: d_one(g, flag=False)))
glyph("three.ss06", zone="fig")(_tabular(d_three_flat))
glyph("one.pnum.ss06", zone="fig")(lambda g: d_one(g, flag=False, prop=True))
glyph("three.pnum.ss06", zone="fig")(d_three_flat)


# ---------------------------------------------------------------------------
# numerics
# ---------------------------------------------------------------------------

def _clear_adv(g: G):
    g.advance = None


def sups_dy(g: G):
    return g.cap * (1 - NUM_S)


def subs_dy(g: G):
    return -g.cap * 0.2


SUPS_U = {"zero": (0x2070, "uni2070"), "one": (0xB9, "onesuperior"), "two": (0xB2, "twosuperior"),
          "three": (0xB3, "threesuperior")}
for _i, _n in enumerate(DIGIT_NAMES[4:], start=4):
    SUPS_U[_n] = (0x2070 + _i, f"uni{0x2070 + _i:04X}")

for _i, _n in enumerate(DIGIT_NAMES):
    src = _n + ".pnum"
    for suf, dy in ((".sups", sups_dy), (".numr", sups_dy), (".dnom", 0.0), (".subs", subs_dy)):
        derive(_n + suf, src=src, sx=num_sx, sy=NUM_S, dy=dy, wscale=num_ws, zone="auto", post=_clear_adv)
    cp, nm = SUPS_U[_n]
    derive(nm, cp, src=src, sx=num_sx, sy=NUM_S, dy=sups_dy, wscale=num_ws, zone="auto", post=_clear_adv)
    derive(f"uni{0x2080 + _i:04X}", 0x2080 + _i, src=src, sx=num_sx, sy=NUM_S, dy=subs_dy, wscale=num_ws,
           zone="auto", post=_clear_adv)


# ---------------------------------------------------------------------------
# fractions
# ---------------------------------------------------------------------------

FRAC_W = 0.86         # fraction slash weight factor
FRAC_RUN = 0.56       # horizontal run per unit of height (≈ 61° from horizontal)


def _frac_geom(g: G):
    ws = FRAC_W * num_ws(g) / 0.86
    ay = g.hh * ws
    by = g.cap - g.hh * ws
    run = (by - ay) * FRAC_RUN
    return ws, ay, by, run


@glyph("fraction", 0x2044, zone="auto")
def fraction(g: G):
    ws, ay, by, run = _frac_geom(g)
    g.line(0, ay, run, by, ws)
    # tuck numerator / denominator under the slash (see _frac below)
    tuck = run * (1 - NUM_S) * 0.92 - 6 - g.W * 0.1
    sb = -(tuck - 48)
    g.lsb = g.rsb = sb


def _frac(num, den):
    def f(g: G):
        ws, ay, by, run = _frac_geom(g)
        gap = 4 + g.W * 0.12
        dgap = 26 + g.W * 0.25
        hx = g.hw * ws
        # Mono: two-digit parts must fit the cell -> slightly smaller, lighter
        sc = 0.9 if g.mono else 1.0
        wsx = 0.88 if g.mono else 1.0
        nps = [Piece(g, d + ".numr", sc, sc, wsx) for d in num]
        dps = [Piece(g, d + ".dnom", sc, sc, wsx) for d in den]
        ndy = g.cap * (1 - sc)
        # numerator, left to right
        plan = []
        x = 0.0
        for p in nps:
            plan.append((p, x - p.box[0]))
            x += p.w + dgap
        nx1 = x - dgap
        ynb = min(p.box[1] for p in nps) + ndy
        sx = lambda y: ax + run * (y - ay) / (by - ay)
        ax = nx1 + gap + hx - run * (ynb - ay) / (by - ay)
        x = None
        if dps:
            ydt = max(p.box[3] for p in dps)
            x = sx(ydt) + hx + gap
            for p in dps:
                plan.append((p, x - p.box[0]))
                x += p.w + dgap
            x -= dgap
        right = max(x if x is not None else 0, ax + run + hx)
        sq = 1.0
        if g.mono:
            sq = min(1.0, 548 / right)
        g.transform(lambda q: (q[0] * sq, q[1]))
        for p, dx in plan:
            p.put(dx, ndy if p in nps else 0.0)
        g.line(ax, ay, ax + run, by, ws)
        g.transform(None)
    return f


FRACS = [
    ("onehalf", 0xBD, "one", "two"), ("onequarter", 0xBC, "one", "four"),
    ("threequarters", 0xBE, "three", "four"),
    ("uni2150", 0x2150, "one", "seven"), ("uni2151", 0x2151, "one", "nine"),
    ("uni2152", 0x2152, "one", "one zero"), ("onethird", 0x2153, "one", "three"),
    ("twothirds", 0x2154, "two", "three"), ("uni2155", 0x2155, "one", "five"),
    ("uni2156", 0x2156, "two", "five"), ("uni2157", 0x2157, "three", "five"),
    ("uni2158", 0x2158, "four", "five"), ("uni2159", 0x2159, "one", "six"),
    ("uni215A", 0x215A, "five", "six"), ("oneeighth", 0x215B, "one", "eight"),
    ("threeeighths", 0x215C, "three", "eight"), ("fiveeighths", 0x215D, "five", "eight"),
    ("seveneighths", 0x215E, "seven", "eight"), ("uni215F", 0x215F, "one", ""),
    ("uni2189", 0x2189, "zero", "three"),
]
for _nm, _cp, _a, _b in FRACS:
    glyph(_nm, _cp, zone="auto")(_frac(_a.split(), _b.split()))


# ---------------------------------------------------------------------------
# percent family
# ---------------------------------------------------------------------------

def _pct_ring(g: G, x0, y0, ow, oh, w):
    g.oval(x0, y0, x0 + ow, y0 + oh, k=0.6, w=w)


def _percent(g: G, extra):
    """Two (or more) small rings and a slash.  extra = number of rings on the
    bottom right (1: %, 2: ‰, 3: ‱)."""
    w = num_ws(g) * (1.02 if (not g.mono or extra == 1) else 0.86 - g.grow * 0.001)
    if g.mono:
        ow = {1: 196, 2: 150, 3: 116}[extra] + g.grow * 0.25
        oh = 300 + g.grow * 0.2
        gap = {1: 0, 2: 22, 3: 14}[extra] + g.grow * 0.1
        run = {1: 250, 2: 210, 3: 170}[extra]
    else:
        ow = 222 + g.grow * 0.5
        oh = 312 + g.grow * 0.3
        gap = 40 + g.grow * 0.25
        run = 270 + g.grow * 0.2
    top = g.cap + g.ov
    bot = -g.ov
    _pct_ring(g, 0, top - oh, ow, oh, w)
    # slash: starts below/right of the first ring, ends above/left of the last
    sw = DIAG * 0.95
    hx = g.hw * sw
    x0 = ow * 0.5 + 10 + g.grow * 0.1
    g.line(x0 + hx, g.hh * sw, x0 + hx + run, g.cap - g.hh * sw, sw)
    xb = x0 + run + hx * 2 - ow * 0.5 - 10 - g.grow * 0.1
    for i in range(extra):
        _pct_ring(g, xb + i * (ow + gap), bot, ow, oh, w)
    fit_cell(g)


@glyph("percent", 0x25, zone="fig")
def percent(g: G):
    _percent(g, 1)


@glyph("perthousand", 0x2030, zone="fig")
def perthousand(g: G):
    _percent(g, 2)


@glyph("uni2031", 0x2031, zone="fig")
def perthenthousand(g: G):
    _percent(g, 3)


# ---------------------------------------------------------------------------
# ordinals, numero
# ---------------------------------------------------------------------------

ORD_S = 0.62


def _ordinal(src):
    def f(g: G):
        ws = num_ws(g)
        p = Piece(g, src, ORD_S, ORD_S, ws)
        top = g.cap + g.ov * ORD_S
        dy = top - p.box[3]
        p.put(-p.box[0], dy)
        yb = dy + p.box[1] - 64 - g.H * ws * 0.5 - g.grow * 0.12
        g.bar(0, p.w, yb, w=ws)
    return f


glyph("ordfeminine", 0xAA, zone="auto")(_ordinal("a"))
glyph("ordmasculine", 0xBA, zone="auto")(_ordinal("o"))


def cap_N(g: G, x0, nw, y0=0.0, y1=None, w=1.0):
    """Self-contained capital N skeleton (ink x0..x0+nw)."""
    y1 = g.cap if y1 is None else y1
    hw, hh = g.hw * w, g.hh * w
    l, r = x0 + hw, x0 + nw - hw
    g.line(l, y0 + hh, l, y1 - hh, w)
    g.line(r, y0 + hh, r, y1 - hh, w)
    g.line(l, y1 - hh, r, y0 + hh, w * DIAG)


@glyph("uni2116", 0x2116, zone="fig")
def numero(g: G):
    if g.mono:
        nw = 330 + g.grow * 0.6
        s = 0.44
        wn = 0.84
    else:
        nw = 540 + g.grow * 0.5
        s = 0.58
        wn = 1.0
    cap_N(g, 0, nw, w=wn)
    ws = num_ws(g)
    p = Piece(g, "o", s, s, ws)
    gap = (30 if g.mono else 62) + g.grow * 0.1
    dy = g.cap - p.box[3]
    p.put(nw + gap - p.box[0], dy)
    yb = dy + p.box[1] - 58 - g.H * ws * 0.5 - g.grow * 0.1
    g.bar(nw + gap, nw + gap + p.w, yb, w=ws)
    fit_cell(g)


# ---------------------------------------------------------------------------
# circled digits
# ---------------------------------------------------------------------------

def _circled(digits):
    def f(g: G):
        ws = 0.80 - g.grow * (0.0019 if g.mono else 0.0016)
        if g.mono:
            D = 560 + g.grow * 0.2
            s1, s2x, s2y = 0.44, 0.34, 0.42
        else:
            D = 820 + g.grow * 0.5
            s1, s2x, s2y = 0.56, 0.44, 0.52
        s1 += g.grow * 0.0008
        s1x = s1 + g.grow * 0.0006
        s2x += g.grow * 0.0004
        cy = g.cap / 2
        cx = D / 2
        g.oval(0, cy - D / 2, D, cy + D / 2, k=0.56, w=ws * (0.86 if g.mono else 1.0))
        if len(digits) == 1:
            ps = [Piece(g, digits[0] + ".pnum", s1x, s1, ws)]
        else:
            ws2 = ws - (0.06 + g.grow * 0.0006 if g.mono else 0.0)
            ps = [Piece(g, d + ".pnum", s2x, s2y, ws2) for d in digits]
        gap = 24 + g.grow * 0.15
        tw = sum(p.w for p in ps) + gap * (len(ps) - 1)
        x = cx - tw / 2
        for p in ps:
            yc = (p.box[1] + p.box[3]) / 2
            p.put(x - p.box[0], cy - yc)
            x += p.w + gap
    return f


glyph("uni24EA", 0x24EA, zone="auto")(_circled(["zero"]))
for _i in range(1, 21):
    _ds = [DIGIT_NAMES[int(c)] for c in str(_i)]
    glyph(f"uni{0x245F + _i:04X}", 0x245F + _i, zone="auto")(_circled(_ds))
