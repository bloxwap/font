"""Extra Latin base letters (Æ Ø Þ Œ Ł Ħ Ŧ Ŋ ẞ Ð IJ and lowercase partners),
plus the ss08 disambiguation l."""
from __future__ import annotations

from ..skeleton import glyph, G, shift, mirror_x
from .latin_upper import JOIN, DIAG, KR, bowl_r, diag_x, bar_y, w_D, w_H, w_J, w_O, w_T  # noqa: F401
from .latin_lower import LEAD, EPS, bowl_left, loop


# ---------------------------------------------------------------------------
# local helpers
# ---------------------------------------------------------------------------

def slash(g: G, x0, y0, x1, y1, w=0.9):
    """Stroke for Ø ø: a diagonal line (skeleton points)."""
    g.line(x0, y0, x1, y1, w)


def lc_arch(g: G, xl, xr, top, join_y=None, apex=0.54, lead=None):
    """n-shoulder without its descending leg (leg drawn by caller).  Like
    `latin_lower.arch`, the stroke first rides up the stem's centre-line for a
    short run (`lead`, width LEAD), then peels off tangentially, so the counter
    has no lobe or dent at the join."""
    join_y = g.xh * 0.56 if join_y is None else join_y
    ty = top - g.hh
    ax = xl + (xr - xl) * apex
    lead = (top - join_y) * 0.24 if lead is None else lead
    return (g.pen(xl, join_y - lead, LEAD)
            .l(xl, join_y)
            .v(ax, ty, k=0.62, w=1.0, k2=0.56)
            .h(xr, top - (top - join_y) * 0.62, k=0.62))


def lc_bowl_right(g: G, xs, x1, y0, y1):
    """Bowl on the right of a stem (b, p, thorn): the mirror of `bowl_left`, a
    complete round loop whose left side lies on the stem's centre-line (the
    caller draws the stem over it).  xs: stem skeleton x; x1: right ink edge."""
    g.transform(mirror_x(xs))
    bowl_left(g, xs, 2 * xs - x1, y0, y1)
    g.transform(None)


def mono_l_x(g: G):
    """Skeleton x of the mono l stem (matches latin_lower.l)."""
    bw = g.wd(0, 440)
    return bw * 0.48


# ---------------------------------------------------------------------------
# capitals
# ---------------------------------------------------------------------------

@glyph("AE", 0xC6, zone="uc")
def AE(g: G):
    if g.mono:
        bw = g.wd(0, 510)
        xs = bw * 0.47              # E stem left ink
        s = 0.8                     # lighter strokes keep the cell open
    else:
        bw = g.wd(840, grow=1.3)
        xs = bw * 0.44
        s = 1.0
    hw, hh = g.hw * s, g.hh * s
    d = DIAG * s
    top = (xs + hw, g.cap - hh)
    foot = (g.hw * d, g.hh * d)
    g.line(*foot, *top, d)
    g.stem(xs, 0, g.cap, w=s)
    yb = g.cap * 0.28 + g.grow * 0.05
    g.bar(diag_x(foot, top, yb) - hw * 0.55, xs + g.W * s, yb, w=0.96 * s)
    # E part
    g.bar(xs, bw - 8, g.cap - hh, w=s)
    g.bar(xs, bw - 36 - g.grow * 0.05, bar_y(g), w=s)
    g.bar(xs, bw, hh, w=s)
    g.anchor("top", (bw + xs) / 2 - 20, g.cap)


@glyph("Oslash", 0xD8, zone="uc")
def Oslash(g: G):
    bw = w_O(g)
    g.oval(0, -g.ov, bw, g.cap + g.ov, k=KR)
    slash(g, bw * 0.12, -36 + g.hh, bw * 0.88, g.cap + 36 - g.hh)
    g.anchor("top", bw / 2, g.cap)


@glyph("Thorn", 0xDE, zone="uc")
def Thorn(g: G):
    bw = g.wd(500, 440, grow=0.6)
    g.stem(0, 0, g.cap)
    y0, y1 = g.cap * 0.17, g.cap * 0.82
    bowl_r(g, g.hw, bw, y0, y1, sv=0.06)


@glyph("OE", 0x152, zone="uc")
def OE(g: G):
    if g.mono:
        bw = g.wd(0, 510)
        xs = bw * 0.5 - g.hw * 0.8
        s = 0.8
    else:
        bw = g.wd(900, grow=1.1)
        xs = bw * 0.47
        s = 1.0
    hw, hh = g.hw * s, g.hh * s
    # left round: from the stem's top round the left to the stem's bottom
    xc = xs + hw
    yt, yb = g.cap - hh, hh
    (g.pen(xc, yt, s)
        .h(hw, g.cap / 2, k=0.6)
        .v(xc, yb, k=0.6)
        .end())
    g.stem(xs, 0, g.cap, w=s)
    g.bar(xs, bw - 8, g.cap - hh, w=s)
    g.bar(xs, bw - 36 - g.grow * 0.05, bar_y(g), w=s)
    g.bar(xs, bw, hh, w=s)


@glyph("Lslash", 0x141, zone="uc")
def Lslash(g: G):
    g.include("L")
    xs = g.hw
    d = 92 + g.grow * 0.35
    g.line(xs - d, g.cap * 0.38, xs + d, g.cap * 0.58, 0.9)
    g.anchor("top", g.hw + 24, g.cap)


@glyph("Hbar", 0x126, zone="uc")
def Hbar(g: G):
    bw = w_H(g)
    g.include("H")
    ext = 46 + g.grow * 0.2
    y = g.cap * 0.78 - g.grow * 0.15
    g.bar(-ext, bw + ext, y, w=0.9)
    g.anchor("top", bw / 2, g.cap)


@glyph("Tbar", 0x166, zone="uc")
def Tbar(g: G):
    bw = w_T(g)
    g.include("T")
    h = 110 + g.grow * 0.5
    g.bar(bw / 2 - h, bw / 2 + h, g.cap * 0.46, w=0.9)
    g.anchor("top", bw / 2, g.cap)


@glyph("Eng", 0x14A, zone="uc")
def Eng(g: G):
    bw = g.wd(560, 440, grow=0.8)
    g.stem(0, 0, g.cap)
    xr = bw - g.hw
    top = g.cap + g.ov * 0.4
    bot = g.desc * 0.82
    p = lc_arch(g, g.hw, xr, top, join_y=g.cap * 0.62, apex=0.52)
    (p.l(xr, 0)
        .v(xr - 110 - g.grow * 0.3, bot + g.hh, k=0.6)
        .l(xr - 190 - g.grow * 0.3, bot + g.hh)
        .end())


@glyph("Germandbls", 0x1E9E, zone="uc")
def Germandbls(g: G):
    # Mono widens with weight more than g.wd's 0.25 so the counter under the
    # bar stays open in Black
    bw = 450 + g.grow * 0.6 if g.mono else g.wd(560, grow=0.7)
    c = g.cap
    xs = g.hw
    # stem with rounded top-left corner, flat top bar
    rr = 150 + g.grow * 0.3
    xt = bw - g.hw * 1.1 - 20
    (g.pen(xs, g.hh)
        .l(xs, c - rr)
        .v(xs + rr * 0.9, c - g.hh, k=0.6)
        .l(xt, c - g.hh)
        .end())
    # diagonal down to the waist: the waist drops and the diagonal's round
    # end moves right with weight, so it stays clear of the stem and the
    # counter under the bar stays open
    if g.mono:                            # narrow cell: lighter diagonal
        yw = c * 0.56 - g.grow * 0.5
        xw = 207 + g.grow * 1.0
        wd = 0.82
    else:
        yw = c * 0.56 - g.grow * 0.4
        xw = 258 + g.grow * 0.75
        wd = DIAG
    g.line(xt, c - g.hh, xw, yw, wd)
    # lower bowl
    xr = bw - g.hw
    xe = g.W + 80 + g.grow * 0.5          # tail end: a constant gap from the stem
    xb = xe + (xr - xe) * 0.3             # bottom extreme (run > 0 in every master)
    (g.pen(xw, yw)
        .l(xw + 30, yw)
        .to(xr, (yw + g.hh) / 2 - 10, "r", "d", k=0.6)
        .to(xb, -g.ov + g.hh, "d", "l", k=0.6)
        .l(xe, -g.ov + g.hh)
        .end())


@glyph("Eth", 0xD0, 0x110, 0x189, zone="uc")
def Eth(g: G):
    bw = w_D(g)
    g.include("D")
    ext = 56 + g.grow * 0.2
    g.bar(-ext, g.W + 110 + g.grow * 0.3, g.cap * 0.5, w=0.9)
    g.anchor("top", bw / 2, g.cap)
    g.anchor("bottom", bw / 2, 0)


@glyph("IJ", 0x132, zone="uc")
def IJ(g: G):
    if g.mono:
        bw = g.wd(0, 480)
        g.stem(0, 0, g.cap, w=0.86)
        xs = bw - g.hw * 0.86
        cx = (xs + g.W + 90) / 2
        (g.pen(xs, g.cap - g.hh * 0.86, 0.86)
            .l(xs, 230)
            .v(cx, -g.ov + g.hh * 0.86, k=KR)
            .to(g.W + 70, 170, "l", (0, 1), k=0.6)
            .end())
        return
    g.stem(0, 0, g.cap)
    dx = g.W + 96 + g.grow * 0.2
    g.transform(shift(dx))
    J(g)
    g.transform(None)


def J(g: G):
    """Sans J skeleton (same as latin_upper.J) — used for IJ."""
    bw = w_J(g)
    xs = bw - g.hw
    cx = (xs + g.hw) / 2 + 6
    (g.pen(xs, g.cap - g.hh)
        .l(xs, 250)
        .v(cx, -g.ov + g.hh, k=KR)
        .to(g.hw, 200, "l", (0, 1), k=0.6)
        .end())


# ---------------------------------------------------------------------------
# lowercase
# ---------------------------------------------------------------------------

@glyph("ae", 0xE6, zone="lc")
def ae(g: G):
    """æ: the a (hook running down a shared middle, closed round bowl riding it,
    as in `latin_lower.a`) and the e's right half springing from the same
    middle.  No tapered joins: the counters are clean rounds."""
    if g.mono:
        # lighter and a little wider in heavy weights so the counters stay
        # open (g.wd's mono grow is only 0.25); still fits the 600 cell
        bw = 500 + g.grow * 0.45
        s = 0.84 - g.grow * 0.0008
    else:
        bw = g.wd(730, grow=1.0)
        s = 1.0
    hw, hh = g.hw * s, g.hh * s
    xm = bw * 0.49                         # shared middle (skeleton x)
    top = g.xh + g.ov
    # a: hook running down the middle
    (g.pen(hw + 12, g.xh * 0.76 + g.grow * 0.1, s)
        .to((hw + xm) / 2 - 2, top - hh, (0.34, 1), "r", k=0.62)
        .h(xm, g.xh * 0.6, k=0.6)
        .l(xm, g.xh * 0.3)
        .end())
    # a: bowl, a closed round loop whose right side rides the middle
    t = g.xh * 0.56 - hh * 0.2 - g.grow * 0.2
    b = -g.ov + hh
    l, r = hw, xm - EPS
    rt = (t - b) * 0.22 + hw * 0.4
    rb = (t - b) * 0.30 + hw * 0.4
    xt, xbr = r - rt * 1.25, r - rb * 1.45
    xl_t = l + (t - b) * 0.5
    xl_b = l + (t - b) * 0.52
    loop(g, l, b, r, t, b + rb, t - rt, xt=xt, top_run=xt - xl_t,
         xb=xl_b, bot_run=xbr - xl_b, yl=(t + b) / 2 + 2, w=s)
    # e: right half
    yb2 = g.xh * 0.5 + hh * 0.2
    right = bw - hw
    cx = (xm + right) / 2
    (g.pen(right, yb2, s)
        .v(cx, top - hh, k=0.6)
        .h(xm, g.xh / 2, k=0.6)
        .v(cx + 6, -g.ov + hh, k=0.6)
        .to(bw - hw - 6, (g.xh + 2 * g.ov) * 0.2 - g.ov, "r", (0.38, 1), k=0.62)
        .end())
    g.line(xm, yb2, right, yb2, s)


@glyph("oslash", 0xF8, zone="lc")
def oslash(g: G):
    bw = g.wd(478, 476)
    g.oval(0, -g.ov, bw, g.xh + g.ov)
    slash(g, bw * 0.08, -30 + g.hh, bw * 0.92, g.xh + 30 - g.hh)
    g.anchor("top", bw / 2, g.xh)


@glyph("thorn", 0xFE, zone="lc")
def thorn(g: G):
    bw = g.wd(474, 466)
    lc_bowl_right(g, g.hw, bw, -g.ov, g.xh + g.ov)
    g.stem(0, g.desc, g.asc)


@glyph("oe", 0x153, zone="lc")
def oe(g: G):
    if g.mono:
        bw = g.wd(0, 510)
        s = 0.84
    else:
        bw = g.wd(790, grow=1.0)
        s = 1.0
    hw, hh = g.hw * s, g.hh * s
    xm = bw * 0.5                          # shared middle (skeleton x)
    y0, y1 = -g.ov, g.xh + g.ov
    g.ovalc(hw, y0 + hh, xm, y1 - hh, w=s)
    yb2 = g.xh * 0.5 + hh * 0.2
    right = bw - hw
    cx = (xm + right) / 2
    (g.pen(right, yb2, s)
        .v(cx, y1 - hh, k=0.6)
        .h(xm, g.xh / 2, k=0.6)
        .v(cx + 6, y0 + hh, k=0.6)
        .to(bw - hw - 6, (y1 - y0) * 0.2 + y0, "r", (0.38, 1), k=0.62)
        .end())
    g.line(xm, yb2, right, yb2, s)


@glyph("lslash", 0x142, zone="lc")
def lslash(g: G):
    g.include("l")
    xs = mono_l_x(g) if g.mono else g.hw
    d = 84 + g.grow * 0.35
    g.line(xs - d, g.asc * 0.4, xs + d, g.asc * 0.6, 0.9)
    g.anchor("top", xs, g.asc)


@glyph("hbar", 0x127, zone="lc")
def hbar(g: G):
    g.include("h")
    y = g.asc * 0.86 - g.grow * 0.12
    g.bar(-40 - g.grow * 0.2, g.W + 150 + g.grow * 0.3, y, w=0.9)


@glyph("tbar", 0x167, zone="lc")
def tbar(g: G):
    g.include("t")
    bw = g.wd(300, 430, grow=0.7)
    y = g.xh * 0.47
    if g.mono:
        g.bar(bw * 0.12, bw * 0.84, y, w=0.9)
    else:
        g.bar(14, bw - 30, y, w=0.9)


@glyph("eng", 0x14B, zone="lc")
def eng(g: G):
    bw = g.wd(436, 456)
    g.stem(0, 0, g.xh)
    xr = bw - g.hw
    bot = g.desc - g.ov * 0.4
    p = lc_arch(g, g.hw, xr, g.xh + g.ov * 0.4)
    (p.l(xr, -10)
        .v(xr - 100 - g.grow * 0.3, bot + g.hh, k=0.6)
        .l(xr - 170 - g.grow * 0.3, bot + g.hh)
        .end())


@glyph("germandbls", 0xDF, zone="lc")
def germandbls(g: G):
    """ß: a stem arching over into a small upper bowl that turns in at the waist
    (a short tongue kept clear of the stem at every weight), then a larger lower
    bowl ending in a flat run along the baseline, also clear of the stem."""
    xs = g.hw
    top = g.asc + g.ov
    # upper bowl right side moves out less than the pen grows, and the waist
    # drops a little with weight, so the upper counter keeps its size; the
    # waist tongue is lighter (wt) and its round tip stays a weight-linear
    # distance (gap) clear of the stem's inner edge, so the counter never closes
    if g.mono:                            # narrow cell: tighter, lighter
        bw = 456 + g.grow * 0.6           # (g.wd's mono grow is only 0.25)
        wt = 0.8
        rx1 = bw * 0.85 - g.hw * 0.5
        yw = g.xh * 0.86 - g.grow * 0.5
        gap = 16 + g.hw * 0.4
    else:
        bw = g.wd(500, grow=0.7)
        wt = 0.85
        rx1 = bw * 0.82 - g.hw * 0.6
        yw = g.xh * 0.86 - g.grow * 0.4
        gap = 24 + g.hw * 0.5
    cx1 = (xs + rx1) / 2
    xw = g.W + gap + g.hw * wt            # tongue tip (skeleton)
    (g.pen(xs, g.hh)
        .l(xs, g.asc - 200)
        .v(cx1, top - g.hh, k=0.6)
        .h(rx1, g.asc - 150 - g.grow * 0.15, k=0.6)
        .v(xw, yw, k=0.6, w=wt)
        .end())
    xr = bw - g.hw
    xe = g.W + 80 + g.grow * 0.5          # tail end: a constant gap from the stem
    xb = xe + (xr - xe) * 0.3             # bottom extreme (run > 0 in every master)
    (g.pen(xw, yw, wt)
        .l(xw + 40, yw, w=wt)
        .to(xr, yw * 0.48, "r", "d", k=0.6, w=1.0)
        .to(xb, -g.ov + g.hh, "d", "l", k=0.6)
        .l(xe, -g.ov + g.hh)
        .end())


@glyph("eth", 0xF0, zone="lc")
def eth(g: G):
    """ð: a complete round bowl, with the ascender arching in from the top
    left and running down the bowl's right side until it merges, tangent, at
    the bowl's widest point (the d_six construction): the counter stays a
    true round, with a clean notch where the bowl leaves the ascender."""
    bw = g.wd(478, 476)
    yt = g.xh * 0.97 + g.ov                 # bowl top (ink)
    xr = bw - g.hw
    g.oval(0, -g.ov, bw, yt)
    cy = (yt - g.ov) / 2                    # bowl's widest point (skeleton y)
    ya = cy + (yt - g.hh - cy) * 0.5        # the ascender turns straight here
    top = (bw * 0.3, g.asc - g.hh)
    p = g.pen(*top).to(xr, ya, (0.9, -1), "d", k=0.6)
    seg = p.segs[-1].pts
    p.l(xr, cy).end()
    # cross stroke, centred on the ascender
    yc = g.asc * 0.83 + g.grow * 0.08
    xc = _x_at_y(seg, yc)
    h = 104 + g.grow * 0.3
    g.line(xc - h, yc - 36, xc + h, yc + 36, 0.86)


def _x_at_y(pts, y, n=64):
    """x on a cubic at height y (sampled; the curve is monotonic in y)."""
    from ..geometry import cubic_point
    best = None
    for i in range(n + 1):
        q = cubic_point(*pts, i / n)
        if best is None or abs(q[1] - y) < abs(best[1] - y):
            best = q
    return best[0]


@glyph("dcroat", 0x111, zone="lc")
def dcroat(g: G):
    g.include("d")
    bw = g.wd(474, 466)
    y = g.asc * 0.84 - g.grow * 0.1
    g.bar(bw - g.W - 120 - g.grow * 0.3, bw + 44 + g.grow * 0.2, y, w=0.9)
    g.anchor("top", bw / 2, g.xh)


@glyph("ij", 0x133, zone="lc")
def ij(g: G):
    dot_y = g.asc - g.W * 0.58 - 10
    if g.mono:
        bw = g.wd(0, 440)
        x1 = bw * 0.2
        g.vstem(x1, 0, g.xh)
        g.dot(x1, dot_y)
        xs = bw * 0.78
    else:
        g.stem(0, 0, g.xh)
        g.dot(g.hw, dot_y)
        xs = g.hw + 150 + g.grow * 0.6
    bot = g.desc - g.ov * 0.4
    (g.pen(xs, g.xh - g.hh).l(xs, -10)
        .v(xs - 100 - g.grow * 0.3, bot + g.hh, k=0.6)
        .l(xs - 150 - g.grow * 0.3, bot + g.hh)
        .end())
    g.dot(xs, dot_y)


@glyph("kgreenlandic", 0x138, zone="lc")
def kgreenlandic(g: G):
    bw = g.wd(430, 456)
    g.stem(0, 0, g.xh)
    jx = g.W + 8
    jy = g.xh * 0.36
    g.line(jx, jy, bw - g.hw * 1.1, g.xh - g.hh, w0=0.9, w1=0.92)
    g.line(jx + 70 + g.grow * 0.2, jy + 70 * 0.95, bw - g.hw * 1.05, g.hh, w0=0.92, w1=0.92)


@glyph("longs", 0x17F, zone="lc")
def longs(g: G):
    bw = g.wd(260, 440, grow=0.7)
    if g.mono:
        xs = bw * 0.4
        g.bar(bw * 0.08, bw * 0.78, g.hh)
    else:
        xs = g.hw + 4
    top = g.asc + g.ov * 0.4
    (g.pen(xs, g.hh)
        .l(xs, g.asc - 150)
        .v(xs + 116 + g.grow * 0.3, top - g.hh, k=0.6)
        .l(bw - g.hw * 0.7, top - g.hh)
        .end())


@glyph("florin", 0x192, zone="lc")
def florin(g: G):
    bw = g.wd(400, 440, grow=0.7)
    xs = bw * 0.5
    top = g.asc + g.ov * 0.4
    bot = g.desc - g.ov * 0.4
    (g.pen(g.hw * 0.7, bot + g.hh)
        .l(xs - 110 - g.grow * 0.3, bot + g.hh)
        .h(xs, g.desc + 150, k=0.6)
        .l(xs, g.asc - 150)
        .v(xs + 110 + g.grow * 0.3, top - g.hh, k=0.6)
        .l(bw - g.hw * 0.7, top - g.hh)
        .end())
    g.bar(xs - 130 - g.grow * 0.2, xs + 130 + g.grow * 0.2, g.xh - g.hh)


@glyph("l.ss08", zone="lc")
def l_ss08(g: G):
    if g.mono:
        g.include("l")
        return
    bw = g.wd(220, grow=0.7)
    xs = g.hw
    (g.pen(xs, g.asc - g.hh)
        .l(xs, 140)
        .v(xs + 104 + g.grow * 0.3, g.hh - g.ov * 0.3, k=0.6)
        .l(bw - g.hw * 0.7, g.hh - g.ov * 0.3)
        .end())
    g.anchor("top", xs, g.asc)
