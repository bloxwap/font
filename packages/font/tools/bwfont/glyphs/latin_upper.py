"""Latin capital skeletons (A-Z) and their stylistic alternates.

Construction notes
------------------
* Stems / bars / diagonals are separate strokes; their round caps make the
  rounded corners (E, L, T, ...).
* Bowls of B D P R are one smooth stroke that leaves the stem centre-line
  horizontally (top bar), turns round the bowl and comes back to the stem
  centre-line (bottom bar): the caps sit exactly on the stem's own caps, so
  the corners are rounded the same way as E.
* Round letters (O C G Q S J) are built from oval quarters.  A terminal
  (C G S J) is a piece *cut from the oval it belongs to* (`round_terminal`),
  so the curvature runs on unbroken into the terminal: no flat spot or
  knuckle where the stroke leaves the bowl (Nunito-like smoothness).
"""
from __future__ import annotations

from ..geometry import cubic_point, cubic_split
from ..skeleton import glyph, G, soften, CIRCLE_K, SQUARENESS

JOIN = 0.52      # width factor where a curve merges into a stem
DIAG = 0.92      # width factor of diagonals
KR = 0.6         # tension of capital rounds
C_TOP = 0.81     # height (fraction) of the upper C / G terminal (lower: 1 - C_TOP)


# ---------------------------------------------------------------------------
# widths (shared with latin_core_extra through the functions below)
# ---------------------------------------------------------------------------

def w_A(g): return g.wd(600, 490, grow=0.8)
def w_B(g): return g.wd(500, 440, grow=0.8)
def w_C(g): return g.wd(560, 450, grow=0.6)
def w_D(g): return g.wd(560, 450, grow=0.6)
def w_E(g): return g.wd(440, 420, grow=0.5)
def w_F(g): return g.wd(420, 420, grow=0.5)
def w_G(g): return g.wd(590, 456, grow=0.6)
def w_H(g): return g.wd(540, 440, grow=0.7)
def w_J(g): return g.wd(420, 420, grow=0.5)
def w_K(g): return g.wd(530, 460, grow=0.6)
def w_L(g): return g.wd(400, 410, grow=0.5)
def w_M(g): return g.wd(670, 480, grow=1.3)
def w_N(g): return g.wd(560, 440, grow=0.8)
def w_O(g): return g.wd(640, 470, grow=0.6)
def w_P(g): return g.wd(490, 440, grow=0.6)
def w_R(g): return g.wd(510, 450, grow=0.6)
def w_S(g): return g.wd(500, 446, grow=0.6)
def w_T(g): return g.wd(520, 460, grow=0.5)
def w_U(g): return g.wd(540, 440, grow=0.7)
def w_V(g): return g.wd(590, 490, grow=0.8)
def w_W(g): return g.wd(860, 520, grow=1.2)
def w_X(g): return g.wd(570, 480, grow=0.7)
def w_Y(g): return g.wd(580, 490, grow=0.7)
def w_Z(g): return g.wd(520, 440, grow=0.5)


def bar_y(g):
    """Centre of the E / F / H crossbar (a touch above the middle)."""
    return g.cap * 0.5 + 6


# ---------------------------------------------------------------------------
# shared constructions
# ---------------------------------------------------------------------------

def bowl_r(g: G, xs, x1, y0, y1, rx=None, sv=0.0, k=KR, wt=1.0, wb=1.0):
    """D-shaped bowl to the right of a stem.  xs: stem skeleton x; x1: right
    ink edge; y0/y1: ink bottom/top of the bowl.  rx: horizontal radius of
    the round part (default = vertical radius); sv: straight vertical part as
    a fraction of the vertical radius (0 = none; constant per glyph).
    wt / wb: width factors of the top / bottom bar (thinner middle bars)."""
    yt, yb = y1 - g.hh * wt, y0 + g.hh * wb
    xr = x1 - g.hw
    ry = (yt - yb) / 2
    cy = (yt + yb) / 2
    rx = ry if rx is None else rx
    xc = max(xr - rx, xs + 2)
    s = ry * sv
    p = g.pen(xs, yt, wt).l(xc, yt, w=wt)
    if sv > 0:
        p.h(xr, cy + s, k=k, w=1.0).l(xr, cy - s).v(xc, yb, k=k, w=wb)
    else:
        p.h(xr, cy, k=k, w=1.0).v(xc, yb, k=k, w=wb)
    p.l(xs, yb).end()


def _rev(c):
    return (c[3], c[2], c[1], c[0])


def _t_at(c, axis, v):
    """Parameter where the (monotone) cubic `c` reaches coordinate v."""
    a, b = 0.0, 1.0
    up = c[3][axis] > c[0][axis]
    for _ in range(50):
        m = (a + b) / 2
        if (cubic_point(*c, m)[axis] < v) == up:
            a = m
        else:
            b = m
    return (a + b) / 2


def _kstart(c):
    """Curvature of cubic c at its start."""
    d = (c[1][0] - c[0][0], c[1][1] - c[0][1])
    e = (c[2][0] - c[1][0], c[2][1] - c[1][1])
    L = (d[0] ** 2 + d[1] ** 2) ** 0.5
    return 2 / 3 * abs(d[0] * e[1] - d[1] * e[0]) / L ** 3


def _kend(c):
    return _kstart(_rev(c))


def _solve(f, lo, hi):
    """Root of f(x)[0] (sign change between lo and hi); clamps to the ends."""
    flo = f(lo)[0]
    if flo * f(hi)[0] > 0:
        return lo if abs(flo) < abs(f(hi)[0]) else hi
    for _ in range(40):
        m = (lo + hi) / 2
        if (f(m)[0] > 0) == (flo > 0):
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def round_terminal(side_x, side_y, ext_y, term_x, term_y, k=KR):
    """Terminal cut from an oval (C / G / S / J ends).

    The oval quarter runs from a vertical-tangent *side* point (side_x, side_y)
    over the horizontal-tangent *extreme* (top or bottom, at ext_y) and on
    down the far side.  The horizontal radius is solved so that the far side
    passes through the terminal (term_x, term_y).  Returns (ext_x, cubic):
    ext_x = x of the extreme; cubic = the piece from the terminal to the
    extreme (skeleton points).  Drawing the near quarter with the same k
    (`.h` / `.v` between the side and the extreme) makes the two halves one
    curvature-continuous oval, so the terminal flows straight out of the bowl.
    """
    kk = soften(k)
    s = 1.0 if term_x > side_x else -1.0
    ry = ext_y - side_y

    def piece(rx):
        ce = side_x + s * rx
        far = side_x + 2 * s * rx
        q = ((far, side_y), (far, side_y + ry * kk), (ce + s * rx * kk, ext_y), (ce, ext_y))
        t = _t_at(q, 1, term_y)
        return ce, cubic_split(*q, t)[1]

    lo, hi = abs(term_x - side_x) * 0.5, abs(term_x - side_x) * 1.5
    for _ in range(50):
        m = (lo + hi) / 2
        if s * (piece(m)[1][0][0] - term_x) < 0:
            lo = m
        else:
            hi = m
    ce, c = piece((lo + hi) / 2)
    c = ((term_x, term_y),) + tuple(c[1:])
    return ce, c


def c_open(g: G, x0, x1, y0, y1, t_top=None, t_bot=None, k=KR, xt=None, xb=None,
           dir_top=(0.36, -1), dir_bot=(0.34, 1), arc=True):
    """Open round (C).  Terminals at fractions of the height.
    arc=True (default): the terminals are cut from the oval itself
    (`round_terminal`), so the curve is unbroken into each end.  arc=False:
    the old construction with explicit terminal directions dir_top/dir_bot.
    t_top / t_bot default to 0.81 / 0.19 (arc) or 0.77 / 0.23 (old)."""
    if t_top is None:
        t_top = C_TOP if arc else 0.77
    if t_bot is None:
        t_bot = 1 - C_TOP if arc else 0.23
    cx = (x0 + x1) / 2
    left = x0 + g.hw
    cy = (y0 + y1) / 2
    h = y1 - y0
    xt = (x1 - g.hw - 4) if xt is None else xt
    xb = (x1 - g.hw - 2) if xb is None else xb
    yt, yb = y1 - g.hh, y0 + g.hh
    if arc:
        ct, top = round_terminal(left, cy, yt, xt, y0 + h * t_top, k)
        cb, bot = round_terminal(left, cy, yb, xb, y0 + h * t_bot, k)
        bot = _rev(bot)
        (g.pen(*top[0])
            .c(top[1], top[2], top[3])
            .h(left, cy, k=k)
            .v(cb, yb, k=k)
            .c(bot[1], bot[2], bot[3])
            .end())
        return
    (g.pen(xt, y0 + h * t_top)
        .to(cx + 8, yt, (-dir_top[0], -dir_top[1]), "l", k=0.62)
        .h(left, cy, k=k)
        .v(cx + 8, yb, k=k)
        .to(xb, y0 + h * t_bot, "r", dir_bot, k=0.62)
        .end())


def diag_x(p0, p1, y):
    """x on the line p0-p1 at height y."""
    (x0, y0), (x1, y1) = p0, p1
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def a_shape(g: G, bw, bar=True):
    """Two diagonals meeting at the apex (+ optional crossbar).  Returns the
    skeleton points (left foot, apex, right foot)."""
    r, rh = g.hw * DIAG, g.hh * DIAG
    cx = bw / 2
    L, T, R = (r, rh), (cx, g.cap - rh), (bw - r, rh)
    g.line(*L, *T, DIAG)
    g.line(*R, *T, DIAG)
    if bar:
        yb = g.cap * 0.28 + g.grow * 0.05
        g.bar(diag_x(L, T, yb) - g.hw * 0.55, diag_x(R, T, yb) + g.hw * 0.55, yb, w=0.96)
    return L, T, R


def e_bars(g: G, x0, bw, top=True, mid=True, bottom=True, mid_y=None):
    """E-style bars from a stem whose left ink edge is x0."""
    if top:
        g.bar(x0, bw - 8, g.cap - g.hh)
    if mid:
        g.bar(x0, bw - 36 - g.grow * 0.05, bar_y(g) if mid_y is None else mid_y)
    if bottom:
        g.bar(x0, bw, g.hh)


def mono_slabs(g: G, bw, top=True, bottom=True):
    if top:
        g.bar(bw * 0.12, bw * 0.88, g.cap - g.hh)
    if bottom:
        g.bar(bw * 0.12, bw * 0.88, g.hh)


# ---------------------------------------------------------------------------
# glyphs
# ---------------------------------------------------------------------------

@glyph("A", 0x41, zone="uc")
def A(g: G):
    bw = w_A(g)
    L, T, R = a_shape(g, bw)
    g.anchor("ogonek", R[0] + 4, 0)


@glyph("B", 0x42, zone="uc")
def B(g: G):
    bw = w_B(g)
    xs = g.hw
    g.stem(0, 0, g.cap)
    jm = g.cap * 0.535
    m = 0.88                       # lighter middle bar keeps Black counters open
    bowl_r(g, xs, bw - 26 - g.grow * 0.1, jm - g.hh * m, g.cap, sv=0.04, wb=m)
    bowl_r(g, xs, bw, 0, jm + g.hh * m, sv=0.06, wt=m)


@glyph("C", 0x43, zone="uc")
def C(g: G):
    bw = w_C(g)
    c_open(g, 0, bw, -g.ov, g.cap + g.ov)


@glyph("D", 0x44, zone="uc")
def D(g: G):
    bw = w_D(g)
    g.stem(0, 0, g.cap)
    ry = (g.cap - g.H) / 2
    bowl_r(g, g.hw, bw, 0, g.cap, rx=ry * 0.95, sv=0.04, k=0.6)   # near-semicircular (Nunito-like)


@glyph("E", 0x45, zone="uc")
def E(g: G):
    bw = w_E(g)
    g.stem(0, 0, g.cap)
    e_bars(g, 0, bw)
    g.anchor("ogonek", bw - 60 - g.grow * 0.2, 0)


@glyph("F", 0x46, zone="uc")
def F(g: G):
    bw = w_F(g)
    g.stem(0, 0, g.cap)
    e_bars(g, 0, bw, bottom=False, mid_y=bar_y(g) - 14)


def g_round(g: G, bw, spur=False):
    """G: the C's oval (top terminal cut from it), a round bottom that turns
    up into the straight right side, and the bar.  The bottom extreme sits
    where the left and right quarters have equal curvature, so the bowl is
    one unbroken round.  spur (ss05): a stem continues the right side down
    to the baseline; the bowl leaves it tangentially (clean notch, no lump)."""
    y0, y1 = -g.ov, g.cap + g.ov
    h = y1 - y0
    cx = bw / 2
    left, xr = g.hw, bw - g.hw
    yt, ybt = y1 - g.hh, y0 + g.hh
    cy = (y0 + y1) / 2
    yb = g.cap * 0.45 - g.grow * 0.05          # bar centre
    yj = g.cap * 0.27                          # right side turns into the bottom here
    ct, top = round_terminal(left, cy, yt, xr - 6, y0 + h * C_TOP, KR)
    # equal end curvatures: rx_R / rx_L = sqrt(ry_R / ry_L)
    q = ((yj - ybt) / (cy - ybt)) ** 0.5
    cb = left + (xr - left) / (1 + q)
    (g.pen(*top[0])
        .c(top[1], top[2], top[3])
        .h(left, cy, k=KR)
        .v(cb, ybt, k=KR)
        .h(xr, yj, k=KR)
        .l(xr, yb)
        .end())
    if spur:
        g.stem(bw - g.W, 0, yj + g.hh + (yb - yj) * 0.5)
    g.bar(cx + 14, bw, yb)


@glyph("G", 0x47, zone="uc")
def G_(g: G):
    g_round(g, w_G(g))


@glyph("G.ss05", zone="uc")
def G_ss05(g: G):
    g_round(g, w_G(g), spur=True)


@glyph("H", 0x48, zone="uc")
def H(g: G):
    bw = w_H(g)
    g.stem(0, 0, g.cap)
    g.stem(bw - g.W, 0, g.cap)
    g.bar(g.hw, bw - g.hw, bar_y(g))


@glyph("I", 0x49, zone="uc")
def I(g: G):
    if g.mono:
        bw = g.wd(0, 380)
        g.vstem(bw / 2, 0, g.cap)
        mono_slabs(g, bw)
        g.anchor("ogonek", bw / 2 + 10, 0)
        g.anchor("top", bw / 2, g.cap)
        return
    g.stem(0, 0, g.cap)
    g.anchor("ogonek", g.hw + 6, 0)


@glyph("I.ss08", zone="uc")
def I_ss08(g: G):
    bw = g.wd(320, 380, grow=0.8)
    g.vstem(bw / 2, 0, g.cap)
    if g.mono:
        mono_slabs(g, bw)
    else:
        g.bar(0, bw, g.cap - g.hh)
        g.bar(0, bw, g.hh)
    g.anchor("ogonek", bw / 2 + 10, 0)
    g.anchor("top", bw / 2, g.cap)


@glyph("J", 0x4A, zone="uc")
def J(g: G):
    """J: the stem turns round one oval quarter into the bottom; the hook's
    terminal is cut from the same oval (`round_terminal`), so the bowl runs
    on unbroken and ends low and open (Nunito-like), no tight curl."""
    bw = w_J(g)
    if g.mono:
        xs = bw * 0.7 + g.grow * 0.3               # roomier hook when heavy
        g.bar(bw * 0.16, xs + g.hw, g.cap - g.hh)
    else:
        xs = bw - g.hw
    yb = -g.ov + g.hh
    ry = (xs - g.hw) * (0.62 + g.grow * 0.0012)    # taller hook when heavy
    yj = yb + ry
    ft = 0.4 - g.grow * 0.001                      # lower, more open end when heavy
    cb, t = round_terminal(xs, yj, yb, g.hw, yb + ry * ft, KR)
    t = _rev(t)
    (g.pen(xs, g.cap - g.hh)
        .l(xs, yj)
        .v(cb, yb, k=KR)
        .c(t[1], t[2], t[3])
        .end())
    g.anchor("top", xs, g.cap)


@glyph("K", 0x4B, zone="uc")
def K(g: G):
    bw = w_K(g)
    g.stem(0, 0, g.cap)
    r, rh = g.hw * DIAG, g.hh * DIAG
    j0 = (g.W + 6, g.cap * 0.29)
    j1 = (bw - r * 1.06, g.cap - rh)
    g.line(*j0, *j1, w0=0.9, w1=DIAG)
    t = 0.3 + g.grow * 0.0006
    s = (j0[0] + (j1[0] - j0[0]) * t, j0[1] + (j1[1] - j0[1]) * t)
    g.line(*s, bw - r, rh, DIAG)


@glyph("L", 0x4C, zone="uc")
def L(g: G):
    bw = w_L(g)
    g.stem(0, 0, g.cap)
    g.bar(0, bw, g.hh)
    g.anchor("top", g.hw + 24, g.cap)
    g.anchor("caron", g.W + 56 + g.grow * 0.2, g.cap + 10)
    g.anchor("dotright", g.W + 96 + g.grow * 0.35, g.cap * 0.46)


@glyph("M", 0x4D, zone="uc")
def M(g: G):
    bw = w_M(g)
    s = 0.86 if g.mono else 1.0
    d = 0.76 if g.mono else DIAG
    g.stem(0, 0, g.cap, w=s)
    g.stem(bw - g.W * s, 0, g.cap, w=s)
    cx = bw / 2
    vy = g.cap * 0.3 if g.mono else g.hh * d + 1   # +1: keeps pathops happy
    a = g.hw * s
    g.line(a, g.cap - g.hh * s, cx, vy, d)
    g.line(bw - a, g.cap - g.hh * s, cx, vy, d)


@glyph("N", 0x4E, zone="uc")
def N(g: G):
    bw = w_N(g)
    g.stem(0, 0, g.cap)
    g.stem(bw - g.W, 0, g.cap)
    g.line(g.hw, g.cap - g.hh, bw - g.hw, g.hh, DIAG)


def o_k(g: G):
    """Tension of the O.  The narrow Mono O gets a touch squarer from Regular
    to Black, so its counter stays a rounded oval instead of pinching into a
    pointed lens (piecewise linear in weight, matching the masters)."""
    if not g.mono:
        return KR
    kk = soften(KR) + max(0.0, g.grow) * 0.0007
    return CIRCLE_K + (kk - CIRCLE_K) / SQUARENESS   # value soften() maps to kk


@glyph("O", 0x4F, zone="uc")
def O(g: G):
    bw = w_O(g)
    g.oval(0, -g.ov, bw, g.cap + g.ov, k=o_k(g))


@glyph("P", 0x50, zone="uc")
def P(g: G):
    bw = w_P(g)
    g.stem(0, 0, g.cap)
    jb = g.cap * 0.40
    bowl_r(g, g.hw, bw, jb - g.hh, g.cap, sv=0.06)


def r_bowl(g: G, bw):
    g.stem(0, 0, g.cap)
    jb = g.cap * 0.43
    xr = bw - 12 - g.grow * 0.1
    ry = (g.cap - jb) / 2
    bowl_r(g, g.hw, xr, jb - g.hh, g.cap, rx=ry * 0.98, sv=0.06)
    return jb, xr


@glyph("R", 0x52, zone="uc")
def R(g: G):
    bw = w_R(g)
    jb, xr = r_bowl(g, bw)
    r, rh = g.hw * DIAG, g.hh * DIAG
    x0 = bw * 0.5 - 20 + g.grow * 0.1
    g.line(x0, jb, bw - r, rh, w0=DIAG)


@glyph("R.ss05", zone="uc")
def R_ss05(g: G):
    bw = w_R(g)
    jb, xr = r_bowl(g, bw)
    x0 = bw * 0.44 + g.grow * 0.1
    xe = bw - g.hw
    (g.pen(x0, jb)
        .to(xe, g.cap * 0.14, (1, -0.15), (0, -1), k=0.6)
        .l(xe, g.hh)
        .end())


def _line_hits_cubic(c, p, d):
    """Parameter where cubic c crosses the line through p with direction d."""
    f = lambda t: ((cubic_point(*c, t)[0] - p[0]) * d[1] - (cubic_point(*c, t)[1] - p[1]) * d[0])
    a, b = 0.0, 1.0
    fa = f(a)
    for _ in range(50):
        m = (a + b) / 2
        if (f(m) > 0) == (fa > 0):
            a = m
        else:
            b = m
    return cubic_point(*c, (a + b) / 2)


@glyph("Q", 0x51, zone="uc")
def Q(g: G):
    """Q: the O and a tail crossing its lower right.  The tail starts a fixed
    distance inside the bowl's centre-line that shrinks with weight, so the
    round cap reads as a short entry at Regular and never swells into a
    blob inside the small Black counter."""
    bw = w_O(g)
    O(g)
    r = g.hw * DIAG
    e = (bw - r + 6, -86 - g.grow * 0.2)
    s0 = (bw * 0.6 + g.grow * 0.1, g.cap * 0.2)
    d = (s0[0] - e[0], s0[1] - e[1])
    n = (d[0] ** 2 + d[1] ** 2) ** 0.5
    d = (d[0] / n, d[1] / n)
    kk = soften(o_k(g))
    x0, y0, x1, y1 = g.hw, -g.ov + g.hh, bw - g.hw, g.cap + g.ov - g.hh
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    br = ((cx, y0), (cx + (x1 - cx) * kk, y0), (x1, cy + (y0 - cy) * kk), (x1, cy))
    p = _line_hits_cubic(br, e, d)
    a = 104 - g.grow * 1.05
    g.line(p[0] + d[0] * a, p[1] + d[1] * a, *e, DIAG)
    g.anchor("top", bw / 2, g.cap)


@glyph("Q.ss05", zone="uc")
def Q_ss05(g: G):
    bw = w_O(g)
    O(g)
    cx = bw / 2
    g.line(cx + 4, g.hh - g.ov, cx + 150 + g.grow * 0.3, -110 - g.grow * 0.15, DIAG)
    g.anchor("top", bw / 2, g.cap)


def s_shape(g: G, bw, c, top, bot, tt=None, tb=None):
    """S: two oval-cut terminals (`round_terminal`) and a spine of quarters.
    c: height of the letter (cap / x-height); top / bot: ink extremes;
    tt / tb: terminal heights as fractions of c (rise a little with weight
    so heavy apertures stay open)."""
    tt = 0.82 + g.grow * 0.0004 if tt is None else tt
    tb = 0.19 - g.grow * 0.0004 if tb is None else tb
    cx = bw / 2
    lx, rx = g.hw + 6, bw - g.hw
    yT, yB = top - g.hh, bot + g.hh
    ym = c * 0.515 + g.hh * 0.05              # spine centre
    ks, kq = soften(0.56), soften(KR)

    # left / right extremes: the heights where the bowl quarter and the spine
    # quarter have the same curvature (one smooth S, no knuckles)
    def upper(y1):
        ct, t0 = round_terminal(lx, y1, yT, bw - g.hw - 10, c * tt, KR)
        a = _kend(((ct, yT), (ct + (lx - ct) * kq, yT), (lx, y1 + (yT - y1) * kq), (lx, y1)))
        b = _kstart(((lx, y1), (lx, y1 + (ym - y1) * ks), (cx + (lx - cx) * ks, ym), (cx, ym)))
        return a - b, ct, t0

    def lower(y2):
        cb, t1 = round_terminal(rx, y2, yB, g.hw + 6, c * tb, KR)
        a = _kend(((cx, ym), (cx + (rx - cx) * ks, ym), (rx, y2 + (ym - y2) * ks), (rx, y2)))
        b = _kstart(((rx, y2), (rx, y2 + (yB - y2) * kq), (cb + (rx - cb) * kq, yB), (cb, yB)))
        return b - a, cb, t1

    y1 = _solve(upper, ym + 30, yT - 30)      # upper curve too tight -> move down
    y2 = _solve(lower, yB + 30, ym - 30)
    _, ct, t0 = upper(y1)
    _, cb, t1 = lower(y2)
    t1 = _rev(t1)
    (g.pen(*t0[0])
        .c(t0[1], t0[2], t0[3])
        .h(lx, y1, k=KR)
        .v(cx, ym, k=0.56)
        .h(rx, y2, k=0.56)
        .v(cb, yB, k=KR)
        .c(t1[1], t1[2], t1[3])
        .end())


@glyph("S", 0x53, zone="uc")
def S(g: G):
    s_shape(g, w_S(g), g.cap, g.cap + g.ov, -g.ov)


@glyph("T", 0x54, zone="uc")
def T(g: G):
    bw = w_T(g)
    g.bar(0, bw, g.cap - g.hh)
    g.vstem(bw / 2, 0, g.cap)


@glyph("U", 0x55, zone="uc")
def U(g: G):
    bw = w_U(g)
    cx = bw / 2
    yj = 250 + g.grow * 0.2
    (g.pen(g.hw, g.cap - g.hh)
        .l(g.hw, yj)
        .v(cx, -g.ov + g.hh, k=KR)
        .h(bw - g.hw, yj, k=KR)
        .l(bw - g.hw, g.cap - g.hh)
        .end())
    g.anchor("ogonek", cx + bw * 0.16, 0)


@glyph("V", 0x56, zone="uc")
def V(g: G):
    bw = w_V(g)
    r, rh = g.hw * DIAG, g.hh * DIAG
    g.line(r, g.cap - rh, bw / 2, rh, DIAG)
    g.line(bw - r, g.cap - rh, bw / 2, rh, DIAG)


@glyph("W", 0x57, zone="uc")
def W(g: G):
    bw = w_W(g)
    s = 0.8 if g.mono else 0.9
    r, rh = g.hw * s, g.hh * s
    xs = [r, bw * 0.265, bw * 0.5, bw * 0.735, bw - r]
    lo, hi = rh, g.cap - rh
    mid = g.cap * 0.74 if g.mono else hi
    g.line(xs[0], hi, xs[1], lo, s)
    g.line(xs[1], lo, xs[2], mid, s)
    g.line(xs[2], mid, xs[3], lo, s)
    g.line(xs[3], lo, xs[4], hi, s)


@glyph("X", 0x58, zone="uc")
def X(g: G):
    bw = w_X(g)
    r, rh = g.hw * DIAG, g.hh * DIAG
    g.line(r, rh, bw - r - 8, g.cap - rh, DIAG)
    g.line(r + 8, g.cap - rh, bw - r, rh, DIAG)


@glyph("Y", 0x59, zone="uc")
def Y(g: G):
    bw = w_Y(g)
    r, rh = g.hw * DIAG, g.hh * DIAG
    cx = bw / 2
    ym = g.cap * 0.42
    g.line(r, g.cap - rh, cx, ym, DIAG)
    g.line(bw - r, g.cap - rh, cx, ym, DIAG)
    g.line(cx, g.hh, cx, ym)


@glyph("Z", 0x5A, zone="uc")
def Z(g: G):
    bw = w_Z(g)
    g.bar(10, bw - 8, g.cap - g.hh)
    g.bar(0, bw, g.hh)
    r = g.hw * 1.1
    g.line(bw - 8 - r, g.cap - g.hh, r, g.hh, DIAG)
