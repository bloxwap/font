"""Latin extended letters: African orthographies (Pan-Nigerian, Ewe, Hausa,
Fula, ...), IPA, Americanist letters, and modifier (superscript) letters.

Construction notes
------------------
* Hooks that replace a stem top (ɓ ɗ ƙ ɦ ɠ ƥ ...) continue the stem's own
  centre-line into a quarter curve, f-style, so they read as one stroke.
* Descender hooks: `hook_down` (left, j-like) and `retro` (retroflex, curling
  right).  Curls (ɕ ʑ ȵ ȶ) roll into a small loop that crosses the stroke.
* Capital hooks on the top-left (Ɓ Ɗ Ƥ Ƭ) are a `crook`: the top line runs
  past the stem and turns down.
* Capitals reuse `latin_upper` widths / helpers (and include its glyphs for
  simple overlays), so they share proportions with A-Z.
* Small capitals and superscripts are skeleton transforms (`derive`), so the
  weight is re-applied and they keep the family colour.
"""
from __future__ import annotations

import math

from ..skeleton import glyph, derive, G, mirror_x, mirror_y, shift, scale_about
from . import latin_lower as LL       # noqa: F401  (ensures lowercase is registered)
from . import latin_upper as LU       # noqa: F401
from .latin_lower import JOIN, LEAD, arch, bowl_left, rot180  # noqa: F401

DIAG = 0.92
KR = 0.6


def _unit(v):
    m = math.hypot(*v)
    return (v[0] / m, v[1] / m)


def _compose(*fns):
    def f(p):
        for fn in fns:
            p = fn(p)
        return p
    return f


# ---------------------------------------------------------------------------
# shared constructions
# ---------------------------------------------------------------------------

def hook_up(p, g: G, xs, top, d=1, rx=None, tail=30, ry=150):
    """Continue path `p` (travelling up along x=xs) into an f-like hook that
    curls horizontally in direction d (+1 right, -1 left); ink top = top."""
    rx = (104 + g.grow * 0.3) if rx is None else rx
    p.l(xs, top - ry).v(xs + d * rx, top - g.hh, k=0.6)
    if tail:
        p.l(xs + d * (rx + tail), top - g.hh)
    return p


def hooked_stem(g: G, xs, y0, top, d=1, rx=None, tail=30):
    """Stem (skeleton x=xs) from skeleton y0 up to a hooked top."""
    hook_up(g.pen(xs, y0), g, xs, top, d, rx, tail).end()


def hook_down(p, g: G, xs, bot=None, d=-1, rx=None, tail=0, y0=-10):
    """Continue path `p` (travelling down along x=xs) into a j-like
    descender hook curling in direction d; ink bottom = bot."""
    bot = g.desc - g.ov * 0.4 if bot is None else bot
    rx = (100 + g.grow * 0.3) if rx is None else rx
    p.l(xs, y0).v(xs + d * rx, bot + g.hh, k=0.6)
    if tail:
        p.l(xs + d * (rx + tail), bot + g.hh)
    return p


def tuck(g: G, side, amount):
    """Let an overhanging hook tuck into the neighbour's space."""
    g.sb[side] = g.sb.get(side, 0) - amount


def retro_over(g: G):
    return 80 + g.grow * 0.3 + 26


def retro(p, g: G, xs, tail=26, bot=None):
    """Retroflex hook: the stroke runs below the baseline and curls right."""
    bot = g.desc + 34 if bot is None else bot
    rx = 80 + g.grow * 0.3
    p.l(xs, -24).v(xs + rx, bot + g.hh, k=0.6)
    if tail:
        p.l(xs + rx + tail, bot + g.hh)
    return p


def crook(g: G, x_from, x_turn, y, rx=None, ry=None):
    """Horizontal stroke (skeleton y) running left from x_from to x_turn and
    turning down: the top-left hook of Ɓ Ɗ Ƥ Ƭ."""
    rx = (84 + g.grow * 0.4) if rx is None else rx
    ry = (150 + g.grow * 0.3) if ry is None else ry
    g.pen(x_from, y).l(x_turn, y).h(x_turn - rx, y - ry, k=0.6).end()


def arm_hook_pts(g: G, base, tip, top, w=DIAG):
    """For a diagonal rising from `base` towards `tip`: the point where the
    hook leaves it, the hook apex and the downturned terminal (ink top=top)."""
    u = _unit((tip[0] - base[0], tip[1] - base[1]))
    ay = top - g.hh * w
    hy = ay - 96 - g.grow * 0.15
    t = (hy - base[1]) / u[1]
    hs = (base[0] + u[0] * t, base[1] + u[1] * t)
    ax = hs[0] + (ay - hs[1]) * u[0] / u[1] * 0.9 + 26
    r = 44 + g.grow * 0.25
    return u, hs, (ax, ay), (ax + r, ay - r * 1.15)


def curl_right(p, x, y, a, w=None):
    """Path travelling right at (x, y): roll up into a loop of size ~2a and
    cross back down through the stroke."""
    w = CURL_W if w is None else w
    p.l(x, y)
    p.h(x + a, y + a, k=0.6, w=w).v(x, y + 2 * a, k=0.6, w=w)
    p.to(x - a * 1.3, y - a * 0.95, "l", (-0.3, -1), k=0.62, w=w)
    return p


CURL_W = 0.86


def curl_size(g: G):
    """Loop radius: keeps a readable counter at every weight."""
    return (62 - g.grow * 0.12 + g.W * CURL_W) / 2


def rhotic(g: G, x, y):
    """Rhotic hook (ɚ ɝ): leaves the letter rightwards, rises, curls back."""
    a = 62 + g.grow * 0.3
    g.pen(x, y).h(x + a, y + a * 1.15, k=0.6).v(x + a * 0.3, y + a * 2.2, k=0.6).end()


def belt(g: G, xs, yb):
    """Lateral-fricative belt (ɬ Ɬ): bar from the right, loop round the left
    of the stem, back to the stem."""
    d = 50 + g.grow * 0.5
    r = d * 1.05
    ext = 92 + g.grow * 0.3
    (g.pen(xs + ext, yb - d)
        .l(xs - 30, yb - d)
        .h(xs - 30 - r, yb, k=0.6)
        .v(xs - 30, yb + d, k=0.6)
        .l(xs, yb + d)
        .end())


def open_e(g: G, bw, y0, y1, yw, t_up=0.44, t_lo=0.40, ind=None, xw=None):
    """ɛ: two stacked bowls opening right.  y0/y1: ink bottom/top (incl.
    overshoot); yw: waist (skeleton)."""
    cx = bw / 2
    ind = bw * 0.06 if ind is None else ind
    left_u = g.hw + ind
    left_l = g.hw
    xw = bw * 0.5 + g.grow * 0.15 if xw is None else xw
    hu = y1 - yw
    hl = yw - y0
    (g.pen(bw - g.hw - 12, y1 - hu * t_up)
        .to(cx + 2, y1 - g.hh, (-0.42, 1), "l", k=0.62)
        .h(left_u, (y1 - g.hh + yw) / 2, k=0.58)
        .v(xw, yw, k=0.58)
        .end())
    (g.pen(xw, yw)
        .h(left_l, (yw + y0 + g.hh) / 2, k=0.58)
        .v(cx + 6, y0 + g.hh, k=0.58)
        .to(bw - g.hw - 4, y0 + hl * t_lo, "r", (0.38, 1), k=0.62)
        .end())


def gamma(g: G, bw, top, yc, ybot, curved=False):
    """ɣ-family: two arms meeting at (bw/2, yc) on top of a small round loop
    whose ink bottom is ybot.  The loop is a closed oval (its counter stays
    open and round at every weight); the arms are separate strokes whose round
    caps sit on the loop's top.  `curved`: ram's-horn arms (ɤ)."""
    r = g.hw * DIAG
    TL = (r, top - g.hh * DIAG)
    TR = (bw - r, top - g.hh * DIAG)
    cx = bw / 2
    C = (cx, yc)
    a = r + 30 + g.grow * 0.1              # loop half-width (skeleton)
    g.ovalc(cx - a, ybot + g.hh * DIAG, cx + a, yc, k=0.6, w=DIAG)
    if curved:
        dL = _unit((C[0] - TL[0], C[1] - TL[1]))
        dR = _unit((TR[0] - C[0], TR[1] - C[1]))
        g.pen(*TL, DIAG).to(*C, (0.12, -1), dL, k=0.6).end()
        g.pen(*C, DIAG).to(*TR, dR, (-0.12, 1), k=0.6).end()
    else:
        g.line(*TL, *C, DIAG)
        g.line(*C, *TR, DIAG)


def glottal(g: G, bw, h):
    """ʔ: question-mark hook on a straight stem; h = height."""
    top = h + g.ov
    cx = bw / 2
    xs = cx - 6
    (g.pen(g.hw + 6, h * 0.735)
        .to(cx, top - g.hh, (0.32, 1), "r", k=0.62)
        .h(bw - g.hw, h * 0.705, k=0.6)
        .to(xs, h * 0.30, "d", "d", k=0.6)
        .l(xs, g.hh)
        .end())
    return xs


def esh(g: G, xs, top, bot, r, tail):
    """ʃ: hooked top (right) + j-like bottom (left) on one stem."""
    (g.pen(xs - r - tail, bot + g.hh)
        .l(xs - r, bot + g.hh)
        .h(xs, -10, k=0.6)
        .l(xs, top - 150)
        .v(xs + r, top - g.hh, k=0.6)
        .l(xs + r + tail, top - g.hh)
        .end())


def ezh(g: G, bw, top, yj, bot, xj=None, t_bot=0.24, bar_x0=10):
    """ʒ: top bar, diagonal down-left to (xj, yj), round bowl to ink bottom
    `bot` ending in a left terminal."""
    g.bar(bar_x0, bw - 10, top - g.hh)
    r = g.hw * 1.1
    xj = bw * 0.36 if xj is None else xj
    g.line(bw - 10 - r, top - g.hh, xj, yj, DIAG)
    cx = bw / 2
    yb = bot + g.hh
    (g.pen(xj, yj)
        .l(cx - 16, yj)
        .h(bw - g.hw, (yj + yb) / 2 - 6, k=0.58)
        .v(cx - 8, yb, k=0.6)
        .to(g.hw + 6, bot + (yj - bot) * t_bot, "l", (-0.4, 1), k=0.62)
        .end())


def upsilon(g: G, bw, h):
    """ʊ: horseshoe whose top terminals flare outward."""
    cx = bw / 2
    ind = 62 + g.grow * 0.2
    xl, xr = g.hw + ind, bw - g.hw - ind
    ym = h * 0.6
    yj = h * 0.36
    yt = h - g.hh
    (g.pen(g.hw * 0.9, yt)
        .h(xl, ym, k=0.62)
        .l(xl, yj)
        .v(cx, -g.ov + g.hh, k=KR)
        .h(xr, yj, k=KR)
        .l(xr, ym)
        .v(bw - g.hw * 0.9, yt, k=0.62)
        .end())


def v_hook(g: G, bw, h):
    """ʋ: straight left side, round bottom, right side hooking left."""
    cx = bw / 2
    yt = h - g.hh
    yj = h * 0.42
    rx = 96 + g.grow * 0.3
    (g.pen(g.hw, yt)
        .l(g.hw, yj)
        .v(cx, -g.ov + g.hh, k=KR)
        .h(bw - g.hw, yj, k=KR)
        .l(bw - g.hw, h * 0.66)
        .v(bw - g.hw - rx, yt + g.ov * 0.4, k=0.62)
        .end())


def ou(g: G, bw, h, yw):
    """Ȣ: closed bowl below, open cup above; waist at skeleton y=yw."""
    g.ovalc(g.hw, -g.ov + g.hh, bw - g.hw, yw, k=KR)
    ind = bw * 0.07
    xl, xr = g.hw + ind, bw - g.hw - ind
    cx = bw / 2
    r = (xr - xl) / 2 * 0.95
    (g.pen(xl, h - g.hh)
        .l(xl, yw + r)
        .v(cx, yw, k=KR)
        .h(xr, yw + r, k=KR)
        .l(xr, h - g.hh)
        .end())


def _rev(c):
    return (c[3], c[2], c[1], c[0])


def hook_top(g: G, xe, yt, xt, ye, tail=0):
    """Top of ƈ Ƈ Ɠ: the bowl's top curve carries on up and out into a short
    round hook -- one smooth rise (no flat run, no S-step) from the bowl's top
    extreme (xe, yt) to a round-capped tip at skeleton (xt, ye), arriving
    nearly upright.  Returns the pen, travelling left at (xe, yt).
    `tail` is accepted for compatibility and ignored."""
    return g.pen(xt, ye).to(xe, yt, (-0.2, -1), "l", k=0.62, k2=0.5)


def c_hook(g: G, x0, x1, y0, y1, hook_h, t_bot=0.24, k=None, arc=False):
    """C / c whose top curve rises up and out into a short round hook (`hook_top`).
    arc=True: the bottom terminal is cut from the oval (as `latin_upper.c_open`
    / C); otherwise it is the lowercase c's (`latin_lower.c_shape`)."""
    cx = (x0 + x1) / 2
    left = x0 + g.hw
    cy = (y0 + y1) / 2
    h = y1 - y0
    yt, yb = y1 - g.hh, y0 + g.hh
    xt = x1 - g.hw - 10
    ye = y1 + hook_h - g.hh
    p = hook_top(g, cx + 8, yt, xt, ye).h(left, cy, k=k)
    if arc:
        kk = KR if k is None else k
        cb, bot = LU.round_terminal(left, cy, yb, x1 - g.hw - 2, y0 + h * t_bot, kk)
        bot = _rev(bot)
        p.v(cb, yb, k=kk).c(bot[1], bot[2], bot[3])
    else:
        (p.v(cx + 6, yb, k=k)
            .to(x1 - g.hw - 2, y0 + h * t_bot, "r", (0.34, 1), k=0.62))
    p.end()


def arch_tail(g: G, xl, xr, top, kind, join_y=None, apex=0.54, lead=None, w=1.0):
    """n-style arch whose right leg ends in a tail: 'left' (j-like hook),
    'retro' (retroflex), 'long' (straight to the descender), 'curl'.
    Like `latin_lower.arch`, the stroke rides up the stem's centre-line for a
    short run (`lead`, width LEAD) before peeling off: no lobe or dent.
    w: stroke width factor (the stem's, e.g. 0.84 in a condensed Mono ɱ)."""
    join_y = g.xh * 0.56 if join_y is None else join_y
    ty = top - g.hh * w
    ax = xl + (xr - xl) * apex
    lead = (top - join_y) * 0.24 if lead is None else lead
    p = (g.pen(xl, join_y - lead, LEAD * w)
         .l(xl, join_y)
         .v(ax, ty, k=0.62, w=w, k2=0.56)
         .h(xr, top - (top - join_y) * 0.62, k=0.62))
    if kind == "left":
        hook_down(p, g, xr, d=-1, tail=6)
    elif kind == "retro":
        retro(p, g, xr)
    elif kind == "long":
        p.l(xr, g.desc + g.hh)
    elif kind == "curl":
        a = curl_size(g)
        p.l(xr, g.hh + a).v(xr + a, g.hh, k=0.6, w=CURL_W)
        p.h(xr + 2 * a, g.hh + a, k=0.6).v(xr + a, g.hh + 2 * a, k=0.6)
        p.l(xr - a * 0.9, g.hh + 2 * a)
    p.end()


def r_arm(g: G, xs, bw):
    """The arm of sans r (from stem centre-line xs): rides the stem for a short
    run, then peels off (as `latin_lower.r`)."""
    jy = g.xh * 0.52
    (g.pen(xs, jy - 56, LEAD)
        .l(xs, jy)
        .v(xs + 140 + g.grow * 0.3, g.xh + g.ov * 0.4 - g.hh, k=0.62, w=1.0)
        .l(bw - g.hw, g.xh + g.ov * 0.4 - g.hh - 4)
        .end())


def w_r(g):
    return g.wd(0, 400) if g.mono else g.wd(290, grow=0.75)


def lig(g: G, parts, mono_w=500):
    """Digraph ligature: parts = [(glyph name, dx), ...] in sans units; the
    total sans ink width is squeezed into the Mono cell."""
    total = parts[-1][1] + parts[-1][2]
    s = 1.0
    if g.mono:
        s = (mono_w + g.grow * 0.25) / total
    for name, dx, _w in parts:
        n0 = len(g.strokes)
        g.include(name, _compose(shift(dx), scale_about(s, 1.0)))
        if g.mono:
            for st in g.strokes[n0:]:
                st.scale *= 0.74
    return s


# ---------------------------------------------------------------------------
# lowercase: hooks on stems (implosives & co.)
# ---------------------------------------------------------------------------

def _b_bowl(g: G, bw):
    g.transform(mirror_x(bw / 2))
    bowl_left(g, bw - g.hw, 0, -g.ov, g.xh + g.ov)
    g.transform(None)


@glyph("uni0253", 0x253, zone="lc")          # ɓ
def b_hook(g: G):
    bw = g.wd(474, 466)
    _b_bowl(g, bw)
    hooked_stem(g, g.hw, g.hh, g.asc + g.ov * 0.4, 1, tail=40)


@glyph("uni0257", 0x257, zone="lc")          # ɗ
def d_hook(g: G):
    bw = g.wd(474, 400)
    xs = bw - g.hw
    bowl_left(g, xs, 0, -g.ov, g.xh + g.ov)
    hooked_stem(g, xs, g.hh, g.asc + g.ov * 0.4, 1, rx=94 + g.grow * 0.3, tail=14)
    tuck(g, "r", (94 + g.grow * 0.3 + 14) * 0.55)


@glyph("uni0256", 0x256, zone="lc")          # ɖ
def d_tail(g: G):
    bw = g.wd(474, 410)
    xs = bw - g.hw
    bowl_left(g, xs, 0, -g.ov, g.xh + g.ov)
    retro(g.pen(xs, g.asc - g.hh), g, xs).end()
    tuck(g, "r", retro_over(g) * 0.5)


@glyph("uni0199", 0x199, zone="lc")          # ƙ
def k_hook(g: G):
    bw = g.wd(430, 456)
    hooked_stem(g, g.hw, g.hh, g.asc + g.ov * 0.4, 1, tail=26)
    jx = g.W + 8
    jy = g.xh * 0.36
    g.line(jx, jy, bw - g.hw * 1.1, g.xh - g.hh, w0=0.9, w1=0.92)
    g.line(jx + 70 + g.grow * 0.2, jy + 70 * 0.95, bw - g.hw * 1.05, g.hh, w0=0.92, w1=0.92)


@glyph("uni0266", 0x266, zone="lc")          # ɦ
def h_hook(g: G):
    bw = g.wd(436, 456)
    hooked_stem(g, g.hw, g.hh, g.asc + g.ov * 0.4, 1, tail=30)
    arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, 0)


@glyph("uni0267", 0x267, zone="lc")          # ɧ
def heng_hook(g: G):
    bw = g.wd(436, 456)
    hooked_stem(g, g.hw, g.hh, g.asc + g.ov * 0.4, 1, tail=30)
    arch_tail(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, "left")


@glyph("uni0260", 0x260, zone="lc")          # ɠ
def g_hook(g: G):
    bw = g.wd(474, 440)
    xs = bw - g.hw
    bowl_left(g, xs, 0, -g.ov + 4, g.xh + g.ov)
    bot = g.desc - g.ov
    cx = bw / 2
    top = g.asc - 10
    rx = 90 + g.grow * 0.3
    (g.pen(xs + rx + 16, top - g.hh)
        .l(xs + rx, top - g.hh)
        .h(xs, top - 150, k=0.6)
        .l(xs, 0)
        .v(cx, bot + g.hh, k=0.6)
        .to(g.hw + 18, g.desc * 0.42, "l", (-0.36, 1), k=0.62)
        .end())
    tuck(g, "r", (rx + 16) * 0.55)


@glyph("uni02A0", 0x2A0, zone="lc")          # ʠ
def q_hook(g: G):
    bw = g.wd(474, 440)
    xs = bw - g.hw
    bowl_left(g, xs, 0, -g.ov, g.xh + g.ov)
    hooked_stem(g, xs, g.desc + g.hh, g.asc - 10, 1, rx=90 + g.grow * 0.3, tail=16)
    tuck(g, "r", (106 + g.grow * 0.3) * 0.55)


@glyph("uni024B", 0x24B, zone="lc")          # ɋ
def q_tail(g: G):
    bw = g.wd(474, 420)
    xs = bw - g.hw
    bowl_left(g, xs, 0, -g.ov, g.xh + g.ov)
    retro(g.pen(xs, g.xh - g.hh), g, xs, bot=g.desc - g.ov * 0.4).end()
    tuck(g, "r", retro_over(g) * 0.5)


@glyph("uni01A5", 0x1A5, zone="lc")          # ƥ
def p_hook(g: G):
    bw = g.wd(474, 466)
    _b_bowl(g, bw)
    hooked_stem(g, g.hw, g.desc + g.hh, g.asc + g.ov * 0.4, 1, tail=40)


@glyph("uni01AD", 0x1AD, zone="lc")          # ƭ
def t_hook(g: G):
    bw = g.wd(320, 430, grow=0.7)
    xs = bw * 0.36 if g.mono else 74 + g.hw + g.grow * 0.2
    top = g.asc + g.ov * 0.4
    rx = 96 + g.grow * 0.3
    yb = g.hh - g.ov * 0.3
    (g.pen(bw - g.hw * 0.7, yb)
        .l(xs + 120 + g.grow * 0.3, yb)
        .h(xs, 130, k=0.6)
        .l(xs, top - 150)
        .v(xs + rx, top - g.hh, k=0.6)
        .l(xs + rx + 24, top - g.hh)
        .end())
    g.bar(0, bw - (0 if g.mono else 10), g.xh - g.hh)


@glyph("uni0188", 0x188, zone="lc")          # ƈ
def c_hook_lc(g: G):
    bw = g.wd(446, 440)
    c_hook(g, 0, bw, -g.ov, g.xh + g.ov, 150 + g.grow * 0.2)


@glyph("uni0272", 0x272, zone="lc")          # ɲ
def n_lefthook(g: G):
    bw = g.wd(436, 440)
    hook_down(g.pen(g.hw, g.xh - g.hh), g, g.hw, d=-1, tail=14).end()
    arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, 0)
    tuck(g, "l", (114 + g.grow * 0.3) * 0.4)


@glyph("uni0273", 0x273, zone="lc")          # ɳ
def n_retro(g: G):
    bw = g.wd(436, 420)
    g.stem(0, 0, g.xh)
    arch_tail(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, "retro")
    tuck(g, "r", retro_over(g) * 0.5)


@glyph("uni019E", 0x19E, zone="lc")          # ƞ
def n_long(g: G):
    bw = g.wd(436, 456)
    g.stem(0, 0, g.xh)
    arch_tail(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, "long")


@glyph("uni0235", 0x235, zone="lc")          # ȵ
def n_curl(g: G):
    bw = g.wd(436, 400)
    g.stem(0, 0, g.xh)
    arch_tail(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, "curl")


@glyph("uni0271", 0x271, zone="lc")          # ɱ
def m_hook(g: G):
    top = g.xh + g.ov * 0.4
    if g.mono:
        bw = g.wd(0, 500)
        g.stem(0, 0, g.xh, w=0.84)
        x1 = bw / 2
        a = g.hw * 0.84
        arch(g, a, x1, top, 0, apex=0.5, w=0.84)
        arch_tail(g, x1, bw - a, top, "left", apex=0.5, w=0.84)
        return
    bw = g.wd(720, grow=1.0)
    g.stem(0, 0, g.xh)
    x1 = bw / 2
    arch(g, g.hw, x1, top, 0, apex=0.52)
    arch_tail(g, x1, bw - g.hw, top, "left", apex=0.52)


@glyph("uni027D", 0x27D, zone="lc")          # ɽ
def r_tail(g: G):
    if g.mono:
        bw = g.wd(0, 430)
        x = bw * 0.26
        g.bar(bw * 0.05, x + g.W, g.xh - g.hh)
        retro(g.pen(x + g.hw, g.xh - g.hh), g, x + g.hw).end()
        jy = g.xh * 0.5
        (g.pen(x + g.hw, jy - 56, LEAD).l(x + g.hw, jy).v(x + g.hw + 150, g.xh + g.ov * 0.4 - g.hh, k=0.62, w=1.0)
            .l(bw - g.hw * 0.7, g.xh + g.ov * 0.4 - g.hh).end())
        return
    bw = g.wd(290, grow=0.75)
    retro(g.pen(g.hw, g.xh - g.hh), g, g.hw).end()
    r_arm(g, g.hw, bw)


@glyph("uni0288", 0x288, zone="lc")          # ʈ
def t_retro(g: G):
    bw = g.wd(300, 430, grow=0.7)
    xs = bw * 0.38 if g.mono else 74 + g.hw + g.grow * 0.2
    retro(g.pen(xs, g.cap * 0.92 - g.hh), g, xs).end()
    g.bar(0, bw - (0 if g.mono else 10), g.xh - g.hh)


@glyph("uni0236", 0x236, zone="lc")          # ȶ
def t_curl(g: G):
    bw = g.wd(300, 430, grow=0.7)
    xs = bw * 0.34 if g.mono else 74 + g.hw + g.grow * 0.2
    a = curl_size(g)
    (g.pen(xs, g.cap * 0.92 - g.hh)
        .l(xs, g.hh + a)
        .v(xs + a, g.hh, k=0.6, w=CURL_W)
        .h(xs + 2 * a, g.hh + a, k=0.6)
        .v(xs + a, g.hh + 2 * a, k=0.6)
        .l(xs - a * 0.9, g.hh + 2 * a)
        .end())
    g.bar(0, bw - (0 if g.mono else 10), g.xh - g.hh)


@glyph("uni026D", 0x26D, zone="lc")          # ɭ
def l_retro(g: G):
    if g.mono:
        bw = g.wd(0, 420)
        x = bw * 0.42 - g.hw
        g.bar(bw * 0.06, x + g.W, g.asc - g.hh)
        retro(g.pen(x + g.hw, g.asc - g.hh), g, x + g.hw, tail=60).end()
        return
    retro(g.pen(g.hw, g.asc - g.hh), g, g.hw).end()
    tuck(g, "r", retro_over(g) * 0.5)


@glyph("uni0282", 0x282, zone="lc")          # ʂ
def s_hook(g: G):
    bw = g.wd(418, 436)
    top = g.xh + g.ov
    bot = -g.ov
    cx = bw / 2
    lx = g.hw + 6
    rx = bw - g.hw
    tx = 74 + g.grow * 0.3
    (g.pen(bw - g.hw - 12, g.xh * 0.79)
        .to(cx, top - g.hh, (-0.4, 1), "l", k=0.62)
        .h(lx, g.xh * 0.73 + g.hh * 0.1, k=0.6)
        .v(cx, g.xh * 0.5 + g.hh * 0.05, k=0.56)
        .h(rx, g.xh * 0.26 - g.hh * 0.1, k=0.56)
        .v(cx - 6, bot + g.hh, k=0.6)
        .l(lx + 70, bot + g.hh)
        .h(lx, -70, k=0.6)
        .v(lx + tx, g.desc + 34 + g.hh, k=0.6)
        .l(lx + tx + 26, g.desc + 34 + g.hh)
        .end())


def _z_top(g: G, bw):
    g.bar(10, bw - 10, g.xh - g.hh)
    g.line(bw - 10 - g.hw * 1.1, g.xh - g.hh, g.hw * 1.1, g.hh, 0.92)


@glyph("uni0290", 0x290, zone="lc")          # ʐ
def z_retro(g: G):
    bw = g.wd(410, 420)
    _z_top(g, bw)
    r = 64 + g.grow * 0.25
    xe = bw - g.hw
    tx = 74 + g.grow * 0.3
    (g.pen(g.hw, g.hh)
        .l(xe - r, g.hh)
        .h(xe, g.hh - r, k=0.6)
        .l(xe, -40)
        .v(xe + tx, g.desc + 34 + g.hh, k=0.6)
        .l(xe + tx + 20, g.desc + 34 + g.hh)
        .end())
    tuck(g, "r", (tx + 20) * 0.5)


@glyph("uni0291", 0x291, zone="lc")          # ʑ
def z_curl(g: G):
    bw = g.wd(410, 420)
    _z_top(g, bw)
    a = curl_size(g)
    curl_right(g.pen(g.hw, g.hh), bw * 0.62, g.hh, a).end()


@glyph("uni0255", 0x255, zone="lc")          # ɕ
def c_curl(g: G):
    bw = g.wd(446, 456)
    y0, y1 = -g.ov, g.xh + g.ov
    cx = bw / 2
    h = y1 - y0
    a = curl_size(g)
    p = (g.pen(bw - g.hw - 4, y0 + h * 0.74)
         .to(cx + 6, y1 - g.hh, (-0.36, 1), "l", k=0.62)
         .h(g.hw, (y0 + y1) / 2)
         .v(cx + 6, y0 + g.hh))
    curl_right(p, cx + 40 + g.grow * 0.2, y0 + g.hh, a).end()


@glyph("uni01B4", 0x1B4, zone="lc")          # ƴ
def y_hook(g: G):
    """ƴ: the y (straight descender to a round cap, as `latin_lower.y`) whose
    right arm turns over into a hook at the top."""
    bw = g.wd(456, 450)
    hw = g.hw * 0.94
    vx = bw / 2 - 6
    vy = g.hh - 6
    g.line(hw, g.xh - g.hh, vx, vy, 0.92)
    x1, y1 = bw - hw - 40, g.xh - g.hh
    dx, dy = vx - x1, vy - y1
    u, hs, ap, te = arm_hook_pts(g, (vx, vy), (x1, y1), g.xh + 20)
    bot = g.desc + g.hh + 6
    tb = (bot - y1) / dy
    (g.pen(*te, 0.92)
        .v(*ap, k=0.6)
        .to(*hs, "l", (-u[0], -u[1]), k=0.6)
        .l(x1 + dx * tb, bot)
        .end())


# ---------------------------------------------------------------------------
# lowercase: turned / reversed forms
# ---------------------------------------------------------------------------

@glyph("schwa", 0x259, zone="lc")            # ə
def schwa(g: G):
    bw = g.wd(468, 466)
    g.include("e", rot180(bw / 2, g.xh / 2))


@glyph("uni01DD", 0x1DD, zone="lc")          # ǝ
def e_turned(g: G):
    g.include("schwa")


@glyph("uni0258", 0x258, zone="lc")          # ɘ
def e_rev(g: G):
    bw = g.wd(468, 466)
    g.include("e", mirror_x(bw / 2))


@glyph("uni0250", 0x250, zone="lc")          # ɐ
def a_turned(g: G):
    bw = g.wd(432, 440)
    g.include("a", rot180(bw / 2, g.xh / 2))


@glyph("uni0251", 0x251, zone="lc")          # ɑ
def alpha_lat(g: G):
    g.include("a.ss01")


@glyph("uni0252", 0x252, zone="lc")          # ɒ
def alpha_turned(g: G):
    bw = g.wd(474, 466)
    g.include("a.ss01", rot180(bw / 2, g.xh / 2))


@glyph("uni028C", 0x28C, zone="lc")          # ʌ
def v_turned(g: G):
    bw = g.wd(452, 470)
    g.include("v", rot180(bw / 2, g.xh / 2))


@glyph("uni028D", 0x28D, zone="lc")          # ʍ
def w_turned(g: G):
    bw = g.wd(700, 500, grow=1.2)
    g.include("w", rot180(bw / 2, g.xh / 2))


@glyph("uni028E", 0x28E, zone="lc")          # ʎ
def y_turned(g: G):
    bw = g.wd(456, 470)
    g.include("y", rot180(bw / 2, g.xh / 2))


@glyph("uni0265", 0x265, zone="lc")          # ɥ
def h_turned(g: G):
    bw = g.wd(436, 456)
    g.include("h", rot180(bw / 2, g.xh / 2))


@glyph("uni029E", 0x29E, zone="lc")          # ʞ
def k_turned(g: G):
    bw = g.wd(430, 456)
    g.include("k", rot180(bw / 2, g.xh / 2))


def _w_m(g):
    return g.wd(0, 500) if g.mono else g.wd(720, grow=1.0)


@glyph("uni026F", 0x26F, zone="lc")          # ɯ
def m_turned(g: G):
    bw = _w_m(g)
    g.include("m", rot180(bw / 2, g.xh / 2))


@glyph("uni0270", 0x270, zone="lc")          # ɰ
def m_turned_long(g: G):
    bw = _w_m(g)
    g.include("m", rot180(bw / 2, g.xh / 2))
    s = 0.84 if g.mono else 1.0
    g.stem(bw - g.W * s, g.desc, g.xh, w=s)


@glyph("uni0279", 0x279, zone="lc")          # ɹ
def r_turned(g: G):
    bw = g.wd(0, 430) if g.mono else g.wd(290, grow=0.75)
    g.include("r", rot180(bw / 2, g.xh / 2))


def _r_turned_arm(g: G, bw):
    g.transform(rot180(bw / 2, g.xh / 2))
    r_arm(g, g.hw, bw)
    g.transform(None)


@glyph("uni027A", 0x27A, zone="lc")          # ɺ
def r_turned_long(g: G):
    bw = w_r(g)
    _r_turned_arm(g, bw)
    g.stem(bw - g.W, 0, g.asc)
    if g.mono:
        g.bar(bw - g.W - 60, bw + 50, g.hh)


@glyph("uni027B", 0x27B, zone="lc")          # ɻ
def r_turned_hook(g: G):
    bw = w_r(g)
    _r_turned_arm(g, bw)
    xs = bw - g.hw
    retro(g.pen(xs, g.xh - g.hh), g, xs).end()
    tuck(g, "r", retro_over(g) * 0.5)


@glyph("uni025C", 0x25C, zone="lc")          # ɜ
def open_e_rev(g: G):
    bw = g.wd(430, 440)
    g.transform(mirror_x(bw / 2))
    open_e(g, bw, -g.ov, g.xh + g.ov, g.xh * 0.54)
    g.transform(None)


@glyph("uni025D", 0x25D, zone="lc")          # ɝ
def open_e_rev_hook(g: G):
    bw = g.wd(430, 400)
    open_e_rev(g)
    xr = bw - g.hw - bw * 0.06
    rhotic(g, xr - 10, g.xh * 0.70)


@glyph("uni025A", 0x25A, zone="lc")          # ɚ
def schwa_hook(g: G):
    bw = g.wd(468, 400)
    g.include("e", rot180(bw / 2, g.xh / 2))
    rhotic(g, bw - g.hw - 10, g.xh * 0.6)


@glyph("uni025E", 0x25E, zone="lc")          # ɞ
def open_e_closed_rev(g: G):
    bw = g.wd(470, 466)
    y0, y1 = -g.ov, g.xh + g.ov
    cx = bw / 2
    yw = g.xh * 0.54
    xw = bw * 0.5 - g.grow * 0.15
    ru = bw - g.hw - bw * 0.06
    rl = bw - g.hw
    (g.pen(xw, yw)
        .h(ru, (y1 - g.hh + yw) / 2, k=0.58)
        .v(cx - 2, y1 - g.hh, k=0.58)
        .h(g.hw, (y0 + y1) / 2, k=KR)
        .v(cx - 6, y0 + g.hh, k=KR)
        .h(rl, (yw + y0 + g.hh) / 2, k=0.58)
        .v(xw, yw, k=0.58)
        .end())


# ---------------------------------------------------------------------------
# lowercase: other shapes
# ---------------------------------------------------------------------------

@glyph("uni025B", 0x25B, zone="lc")          # ɛ
def open_e_lc(g: G):
    bw = g.wd(430, 440)
    open_e(g, bw, -g.ov, g.xh + g.ov, g.xh * 0.54)


@glyph("uni0263", 0x263, zone="lc")          # ɣ
def gamma_lc(g: G):
    bw = g.wd(452, 470)
    gamma(g, bw, g.xh, 30, g.desc - g.ov + 4 - g.grow * 0.1)


@glyph("uni0264", 0x264, zone="lc")          # ɤ
def ramshorn(g: G):
    bw = g.wd(456, 466)
    gamma(g, bw, g.xh, 196 + g.grow * 0.55, -g.ov, curved=True)


@glyph("uni0269", 0x269, zone="lc")          # ɩ
def iota_lat(g: G):
    yb = g.hh - g.ov * 0.3
    if g.mono:
        bw = g.wd(0, 420)
        x = bw * 0.36
        g.bar(bw * 0.04, x + g.hw, g.xh - g.hh)
        (g.pen(x, g.xh - g.hh).l(x, 130).v(x + 120 + g.grow * 0.3, yb, k=0.6)
            .l(bw - g.hw * 0.7, yb).end())
        return
    bw = g.wd(230, grow=0.7)
    (g.pen(g.hw, g.xh - g.hh).l(g.hw, 130).v(g.hw + 110 + g.grow * 0.3, yb, k=0.6)
        .l(bw - g.hw * 0.7, yb).end())


@glyph("uni0268", 0x268, zone="lc")          # ɨ
def i_bar(g: G):
    g.include("i")
    yb = g.xh * 0.5
    e = 80 + g.grow * 0.25
    if g.mono:
        bw = g.wd(0, 440)
        x = bw * 0.5 - g.hw
        g.bar(x - e - 10, x + g.W + e + 10, yb)
        g.anchor("top", x + g.hw, g.xh)
        return
    g.bar(-e, g.W + e, yb)
    g.anchor("top", g.hw, g.xh)


@glyph("uni0289", 0x289, zone="lc")          # ʉ
def u_bar(g: G):
    bw = g.wd(436, 456)
    g.include("u")
    e = 54 + g.grow * 0.2
    if g.mono:
        e = 26
    g.bar(-e, bw + e, g.xh * 0.46)


@glyph("obarred", 0x275, zone="lc")          # ɵ
def obarred_lc(g: G):
    bw = g.wd(478, 476)
    g.include("o")
    g.bar(g.hw * 0.5, bw - g.hw * 0.5, g.xh / 2)



@glyph("uni0254", 0x254, zone="lc")          # ɔ
def open_o(g: G):
    bw = g.wd(446, 456)
    g.include("c", mirror_x(bw / 2))


@glyph("uni028A", 0x28A, zone="lc")          # ʊ
def upsilon_lc(g: G):
    upsilon(g, g.wd(500, 470), g.xh)


@glyph("uni028B", 0x28B, zone="lc")          # ʋ
def vhook_lc(g: G):
    v_hook(g, g.wd(448, 450), g.xh)


@glyph("uni0292", 0x292, zone="lc")          # ʒ
def ezh_lc(g: G):
    bw = g.wd(430, 440)
    ezh(g, bw, g.xh, g.xh * 0.38, g.desc - g.ov)


@glyph("uni021D", 0x21D, zone="lc")          # ȝ
def yogh_lc(g: G):
    bw = g.wd(430, 440)
    g.transform(mirror_x(bw / 2))
    open_e(g, bw, g.desc - g.ov, g.xh + g.ov, g.xh * 0.4, t_up=0.42, t_lo=0.3,
           ind=bw * 0.12, xw=bw * 0.42)
    g.transform(None)


def _w_esh(g):
    r = (124 if g.mono else 100) + g.grow * 0.3
    tail = 46 if g.mono else 26
    return r, tail


@glyph("uni0283", 0x283, zone="lc")          # ʃ
def esh_lc(g: G):
    r, tail = _w_esh(g)
    xs = g.hw + r + tail
    esh(g, xs, g.asc + g.ov * 0.4, g.desc - g.ov * 0.4, r, tail)


@glyph("uni0284", 0x284, zone="lc")          # ʄ
def j_bar_hook(g: G):
    r, tail = _w_esh(g)
    xs = g.hw + r + tail
    esh(g, xs, g.asc + g.ov * 0.4, g.desc - g.ov * 0.4, r, tail)
    e = 86 + g.grow * 0.3
    g.bar(xs - g.hw - e, xs + g.hw + e, g.xh * 0.46)


@glyph("uni025F", 0x25F, zone="lc")          # ɟ
def j_bar(g: G):
    g.include("dotlessj")
    if g.mono:
        bw = g.wd(0, 400)
        xs = bw * 0.66 - g.hw
    else:
        bw = g.wd(170, grow=0.6)
        xs = bw - g.hw
    e = 92 + g.grow * 0.3
    g.bar(xs - g.hw - e - 10, xs + g.hw + e, g.xh * 0.46)


@glyph("uni029D", 0x29D, zone="lc")          # ʝ
def j_crossed(g: G):
    if g.mono:
        bw = g.wd(0, 400)
        xs = bw * 0.62 - g.hw
        g.bar(bw * 0.10, xs + g.hw, g.xh - g.hh)
    else:
        bw = g.wd(200, grow=0.6)
        xs = bw - g.hw
    bot = g.desc - g.ov * 0.4
    a = curl_size(g)
    yl = bot + g.hh + 2 * a + 10
    (g.pen(xs, g.xh - g.hh)
        .l(xs, -10)
        .v(xs - a, bot + g.hh, k=0.6, w=CURL_W)
        .h(xs - 2 * a, (bot + g.hh + yl) / 2, k=0.6)
        .v(xs - a, yl, k=0.6)
        .l(xs + a + 30, yl)
        .end())
    g.dot(xs, g.asc - g.W * 0.58 - 10)
    g.anchor("top", xs, g.xh)


@glyph("uni0242", 0x242, zone="lc")          # ɂ
def glottal_lc(g: G):
    glottal(g, g.wd(370, 420), g.xh)


@glyph("uni0294", 0x294, zone="uc")          # ʔ
def glottal_ipa(g: G):
    glottal(g, g.wd(420, 440), g.cap)


@glyph("uni0295", 0x295, zone="uc")          # ʕ
def glottal_rev(g: G):
    bw = g.wd(420, 440)
    g.include("uni0294", mirror_x(bw / 2))


def _glottal_bar(g: G, bw, rev):
    xs = bw / 2 - 6
    if rev:
        xs = bw - xs
    e = 80 + g.grow * 0.3
    g.bar(xs - g.hw - e, xs + g.hw + e, g.cap * 0.2)


@glyph("uni02A1", 0x2A1, zone="uc")          # ʡ
def glottal_bar(g: G):
    g.include("uni0294")
    _glottal_bar(g, g.wd(420, 440), False)


@glyph("uni02A2", 0x2A2, zone="uc")          # ʢ
def glottal_rev_bar(g: G):
    g.include("uni0295")
    _glottal_bar(g, g.wd(420, 440), True)


@glyph("uni0261", 0x261, zone="lc")          # ɡ
def script_g(g: G):
    g.include("g")


@glyph("uni0278", 0x278, zone="lc")          # ɸ
def phi_lat(g: G):
    bw = g.wd(500, 470)
    g.oval(0, -g.ov, bw, g.xh + g.ov)
    g.vstem(bw / 2, g.desc, g.asc)


@glyph("uni027E", 0x27E, zone="lc")          # ɾ
def r_fishhook(g: G):
    top = g.xh + g.ov * 0.4
    if g.mono:
        bw = g.wd(0, 400)
        x = bw * 0.36
        g.bar(bw * 0.06, bw * 0.74, g.hh)
        hooked_stem(g, x, g.hh, top, 1, rx=120 + g.grow * 0.3, tail=60)
        return
    hooked_stem(g, g.hw, g.hh, top, 1, rx=100 + g.grow * 0.3, tail=36)


@glyph("uni026C", 0x26C, zone="lc")          # ɬ
def l_belt(g: G):
    g.include("l")
    xs = (g.wd(0, 440) * 0.48) if g.mono else g.hw
    belt(g, xs, g.xh * 0.86)


@glyph("uni026E", 0x26E, zone="lc")          # ɮ
def lezh(g: G):
    if g.mono:
        bw = g.wd(0, 460)
    else:
        bw = g.wd(500, grow=0.8)
    g.stem(0, 0, g.asc)
    ezh(g, bw, g.xh, g.xh * 0.36, g.desc - g.ov, xj=bw * 0.44, bar_x0=g.hw)


@glyph("uni019A", 0x19A, zone="lc")          # ƚ
def l_bar(g: G):
    g.include("l")
    e = 80 + g.grow * 0.25
    y = g.asc * 0.52
    if g.mono:
        bw = g.wd(0, 440)
        x = bw * 0.48 - g.hw
        g.bar(x - e, x + g.W + e, y)
        return
    g.bar(-e, g.W + e, y)


@glyph("uni0180", 0x180, zone="lc")          # ƀ
def b_bar(g: G):
    g.include("b")
    e = 80 + g.grow * 0.25
    g.bar(-e, g.W + e, g.xh + (g.asc - g.xh) * 0.5)


@glyph("uni024D", 0x24D, zone="lc")          # ɍ
def r_bar(g: G):
    g.include("r")
    e = 70 + g.grow * 0.25
    y = g.xh * 0.42
    x = w_r(g) * 0.26 if g.mono else 0
    if g.mono:
        x = g.wd(0, 430) * 0.26
    g.bar(x - e, x + g.W + e, y)


def _slash(g: G, cx, y0, y1, slope=0.32):
    h = y1 - y0
    g.line(cx - h * slope / 2, y0 + g.hh, cx + h * slope / 2, y1 - g.hh, 0.88)


@glyph("uni023C", 0x23C, zone="lc")          # ȼ
def c_stroke(g: G):
    bw = g.wd(446, 456)
    g.include("c")
    _slash(g, bw * 0.5, -90, g.xh + 90)


@glyph("uni0247", 0x247, zone="lc")          # ɇ
def e_stroke(g: G):
    bw = g.wd(468, 466)
    g.include("e")
    _slash(g, bw * 0.5, -90, g.xh + 90)


@glyph("uni0298", 0x298, zone="uc")          # ʘ
def click_bilabial(g: G):
    bw = LU.w_O(g)
    g.include("O")
    g.dot(bw / 2, g.cap / 2, g.W * 1.3 + 34)


def _click_h(g):
    return g.desc + 40, g.asc


@glyph("uni01C0", 0x1C0, zone="lc")          # ǀ
def click_dental(g: G):
    y0, y1 = _click_h(g)
    g.vstem(g.hw, y0, y1)


@glyph("uni01C1", 0x1C1, zone="lc")          # ǁ
def click_lateral(g: G):
    y0, y1 = _click_h(g)
    sp = (150 if g.mono else 136) + g.grow * 0.8
    g.vstem(g.hw, y0, y1)
    g.vstem(g.hw + sp, y0, y1)


@glyph("uni01C2", 0x1C2, zone="lc")          # ǂ
def click_alveolar(g: G):
    y0, y1 = _click_h(g)
    e = 110 + g.grow * 0.3
    cx = 0
    g.vstem(cx, y0, y1)
    g.bar(cx - e - g.hw, cx + e + g.hw, g.xh * 0.34)
    g.bar(cx - e - g.hw, cx + e + g.hw, g.xh * 0.70)


@glyph("uni01C3", 0x1C3, zone="lc")          # ǃ
def click_retro(g: G):
    d = g.W * 1.16 + 14
    g.vstem(0, d + 70 + g.grow * 0.2, g.asc)
    g.dot(0, d / 2 - 2, d)


@glyph("uniA78C", 0xA78C, zone="lc")         # ꞌ
def saltillo(g: G):
    g.vstem(0, g.xh * 0.5, g.xh + 30)


@glyph("uniA78B", 0xA78B, zone="uc")         # Ꞌ
def Saltillo(g: G):
    g.vstem(0, g.cap * 0.44, g.cap)


@glyph("uniA789", 0xA789, zone="lc")         # ꞉
def colon_mod(g: G):
    d = g.W * 1.12 + 12
    g.dot(0, g.xh * 0.18 + d / 2, d)
    g.dot(0, g.xh * 0.86 - d / 2, d)


@glyph("uni0223", 0x223, zone="lc")          # ȣ
def ou_lc(g: G):
    bw = g.wd(440, 440)
    h = g.xh + 110
    ou(g, bw, h, h * 0.46)


# --- digraph ligatures ---------------------------------------------------

def _w_d(g):
    return g.wd(474, 466)


def _w_t(g):
    return g.wd(300, 430, grow=0.7)


@glyph("uni02A3", 0x2A3, zone="lc")          # ʣ
def dz(g: G):
    wd_ = _w_d(g)
    dx = wd_ - g.hw - 10
    lig(g, [("d", 0, wd_), ("z", dx, g.wd(410, 440))])


@glyph("uni02A4", 0x2A4, zone="lc")          # ʤ
def dezh(g: G):
    wd_ = _w_d(g)
    dx = wd_ - g.hw - 10
    lig(g, [("d", 0, wd_), ("uni0292", dx, g.wd(430, 440))])


@glyph("uni02A6", 0x2A6, zone="lc")          # ʦ
def ts(g: G):
    wt = _w_t(g)
    lig(g, [("t", 0, wt), ("s", wt - 34, g.wd(418, 436))])


@glyph("uni02A7", 0x2A7, zone="lc")          # ʧ
def tesh(g: G):
    wt = _w_t(g)
    r, tail = _w_esh(g)
    xs_e = g.hw + r + tail
    dx = wt + 10 - xs_e + g.hw
    s = lig(g, [("t", 0, wt), ("uni0283", dx, xs_e + r + tail + g.hw)])
    g.transform(scale_about(s, 1.0))
    g.bar(wt - 60, dx + xs_e + g.hw, g.xh - g.hh)
    g.transform(None)
    if g.mono:
        g.strokes[-1].scale *= 0.74


# ---------------------------------------------------------------------------
# capitals
# ---------------------------------------------------------------------------

@glyph("uni0181", 0x181, zone="uc")          # Ɓ
def B_hook(g: G):
    g.include("B")
    crook(g, g.hw + 10, g.hw - 50 - g.grow * 0.1, g.cap - g.hh)


@glyph("uni018A", 0x18A, zone="uc")          # Ɗ
def D_hook(g: G):
    g.include("D")
    crook(g, g.hw + 10, g.hw - 50 - g.grow * 0.1, g.cap - g.hh)


@glyph("uni01A4", 0x1A4, zone="uc")          # Ƥ
def P_hook(g: G):
    g.include("P")
    crook(g, g.hw + 10, g.hw - 50 - g.grow * 0.1, g.cap - g.hh)


@glyph("uni01AC", 0x1AC, zone="uc")          # Ƭ
def T_hook(g: G):
    bw = LU.w_T(g)
    rx = 78 + g.grow * 0.25
    crook(g, bw - g.hw, g.hw + rx, g.cap - g.hh, rx=rx)
    g.vstem(bw / 2, 0, g.cap)


@glyph("uni018E", 0x18E, zone="uc")          # Ǝ
def E_rev(g: G):
    g.include("E", mirror_x(LU.w_E(g) / 2))


@glyph("Schwa", 0x18F, zone="uc")            # Ə
def Schwa(g: G):
    bw = g.wd(600, 470, grow=0.6)
    y0, y1 = -g.ov, g.cap + g.ov
    cx = bw / 2
    yb = g.cap * 0.5 + g.hh * 0.2
    left, right = g.hw, bw - g.hw
    g.transform(rot180(bw / 2, g.cap / 2))
    (g.pen(right, yb)
        .v(cx, y1 - g.hh, k=KR)
        .h(left, (y0 + y1) / 2, k=KR)
        .v(cx + 8, y0 + g.hh, k=KR)
        .to(bw - g.hw - 6, (y1 - y0) * 0.21 + y0, "r", (0.38, 1), k=0.62)
        .end())
    g.line(left, yb, right, yb)
    g.transform(None)


@glyph("uni0190", 0x190, zone="uc")          # Ɛ
def Open_E(g: G):
    bw = g.wd(480, 446, grow=0.6)
    open_e(g, bw, -g.ov, g.cap + g.ov, g.cap * 0.535, ind=bw * 0.05)


@glyph("uni0194", 0x194, zone="uc")          # Ɣ
def Gamma_lat(g: G):
    bw = g.wd(570, 480, grow=0.8)
    gamma(g, bw, g.cap, g.cap * 0.32 + g.grow * 0.4, -g.ov)


@glyph("uni0196", 0x196, zone="uc")          # Ɩ
def Iota_lat(g: G):
    yb = g.hh - g.ov * 0.3
    if g.mono:
        bw = g.wd(0, 400)
        x = bw * 0.38
        g.bar(bw * 0.1, x + g.hw + 40, g.cap - g.hh)
        (g.pen(x, g.cap - g.hh).l(x, 150).v(x + 120 + g.grow * 0.3, yb, k=0.6)
            .l(bw - g.hw * 0.7, yb).end())
        return
    bw = g.wd(250, grow=0.7)
    (g.pen(g.hw, g.cap - g.hh).l(g.hw, 150).v(g.hw + 116 + g.grow * 0.3, yb, k=0.6)
        .l(bw - g.hw * 0.7, yb).end())


@glyph("uni0197", 0x197, zone="uc")          # Ɨ
def I_bar(g: G):
    g.include("I")
    e = 90 + g.grow * 0.25
    y = LU.bar_y(g)
    if g.mono:
        cx = g.wd(0, 380) / 2
        g.bar(cx - g.hw - e - 10, cx + g.hw + e + 10, y)
        return
    g.bar(-e, g.W + e, y)


@glyph("uni0198", 0x198, zone="uc")          # Ƙ
def K_hook(g: G):
    bw = LU.w_K(g)
    g.stem(0, 0, g.cap)
    r, rh = g.hw * DIAG, g.hh * DIAG
    j0 = (g.W + 6, g.cap * 0.29)
    j1 = (bw - r * 1.06 - 30, g.cap - rh)
    u, hs, ap, te = arm_hook_pts(g, j0, j1, g.cap + 10)
    (g.pen(*j0, 0.9).l(*hs, DIAG).to(*ap, u, "r", k=0.6).h(*te, k=0.6).end())
    t = 0.3 + g.grow * 0.0006
    s = (j0[0] + (j1[0] - j0[0]) * t, j0[1] + (j1[1] - j0[1]) * t)
    g.line(*s, bw - r, rh, DIAG)


@glyph("uni019D", 0x19D, zone="uc")          # Ɲ
def N_hook(g: G):
    bw = LU.w_N(g)
    hook_down(g.pen(g.hw, g.cap - g.hh), g, g.hw, d=-1, tail=14).end()
    tuck(g, "l", (114 + g.grow * 0.3) * 0.4)
    g.stem(bw - g.W, 0, g.cap)
    g.line(g.hw, g.cap - g.hh, bw - g.hw, g.hh, DIAG)


@glyph("Obarred", 0x19F, zone="uc")          # Ɵ
def Obarred(g: G):
    bw = LU.w_O(g)
    g.include("O")
    g.bar(g.hw * 0.5, bw - g.hw * 0.5, g.cap / 2)


@glyph("uni0186", 0x186, zone="uc")          # Ɔ
def Open_O(g: G):
    g.include("C", mirror_x(LU.w_C(g) / 2))


@glyph("uni01B1", 0x1B1, zone="uc")          # Ʊ
def Upsilon_lat(g: G):
    upsilon(g, g.wd(600, 470, grow=0.7), g.cap)


@glyph("uni01B2", 0x1B2, zone="uc")          # Ʋ
def Vhook(g: G):
    v_hook(g, g.wd(540, 450, grow=0.7), g.cap)


@glyph("uni01B3", 0x1B3, zone="uc")          # Ƴ
def Y_hook(g: G):
    bw = LU.w_Y(g)
    r, rh = g.hw * DIAG, g.hh * DIAG
    cx = bw / 2
    ym = g.cap * 0.42
    g.line(r, g.cap - rh, cx, ym, DIAG)
    TR = (bw - r - 50, g.cap - rh)
    u, hs, ap, te = arm_hook_pts(g, (cx, ym), TR, g.cap + 10)
    (g.pen(cx, ym, DIAG).l(*hs).to(*ap, u, "r", k=0.6).h(*te, k=0.6).end())
    g.line(cx, g.hh, cx, ym)


@glyph("uni01B7", 0x1B7, zone="uc")          # Ʒ
def Ezh(g: G):
    bw = g.wd(500, 446, grow=0.6)
    ezh(g, bw, g.cap, g.cap * 0.56, -g.ov, xj=bw * 0.38)


@glyph("uni021C", 0x21C, zone="uc")          # Ȝ
def Yogh(g: G):
    bw = g.wd(480, 446, grow=0.6)
    g.transform(mirror_x(bw / 2))
    open_e(g, bw, g.desc * 0.5 - g.ov, g.cap + g.ov, g.cap * 0.5, t_up=0.42, t_lo=0.3,
           ind=bw * 0.1, xw=bw * 0.42)
    g.transform(None)


@glyph("uni01A9", 0x1A9, zone="uc")          # Ʃ
def Esh(g: G):
    bw = g.wd(500, 440, grow=0.5)
    g.bar(0, bw - 8, g.cap - g.hh)
    g.bar(0, bw, g.hh)
    r = g.hw * 1.1
    vx = bw * 0.52
    g.line(r, g.cap - g.hh, vx, g.cap * 0.5, DIAG)
    g.line(vx, g.cap * 0.5, r, g.hh, DIAG)


@glyph("uni0241", 0x241, zone="uc")          # Ɂ
def Glottal(g: G):
    g.include("uni0294")


@glyph("uni0245", 0x245, zone="uc")          # Ʌ
def V_turned(g: G):
    g.include("V", rot180(LU.w_V(g) / 2, g.cap / 2))


@glyph("uni2C6F", 0x2C6F, zone="uc")         # Ɐ
def A_turned(g: G):
    g.include("A", rot180(LU.w_A(g) / 2, g.cap / 2))


@glyph("uniA7B0", 0xA7B0, zone="uc")         # Ʞ
def K_turned(g: G):
    g.include("K", rot180(LU.w_K(g) / 2, g.cap / 2))


@glyph("uni2C6D", 0x2C6D, zone="uc")         # Ɑ
def Alpha_lat(g: G):
    bw = g.wd(610, 466, grow=0.6)
    xs = bw - g.hw
    g.stem(bw - g.W, 0, g.cap)
    bowl_left(g, xs, 0, -g.ov, g.cap + g.ov)


@glyph("uni0244", 0x244, zone="uc")          # Ʉ
def U_bar(g: G):
    bw = LU.w_U(g)
    g.include("U")
    e = 60 + g.grow * 0.2
    if g.mono:
        e = 30
    g.bar(-e, bw + e, g.cap * 0.42)


@glyph("uni0243", 0x243, zone="uc")          # Ƀ
def B_bar(g: G):
    g.include("B")
    e = 86 + g.grow * 0.25
    g.bar(-e, g.W + 30, g.cap * 0.535)


@glyph("uni023D", 0x23D, zone="uc")          # Ƚ
def L_bar(g: G):
    g.include("L")
    e = 86 + g.grow * 0.25
    g.bar(-e, g.W + e + 20, g.cap * 0.46)


@glyph("uni024C", 0x24C, zone="uc")          # Ɍ
def R_bar(g: G):
    g.include("R")
    e = 86 + g.grow * 0.25
    g.bar(-e, g.W + e, g.cap * 0.26)


@glyph("uni023B", 0x23B, zone="uc")          # Ȼ
def C_stroke(g: G):
    bw = LU.w_C(g)
    g.include("C")
    _slash(g, bw * 0.52, -90, g.cap + 90, slope=0.3)


@glyph("uni0246", 0x246, zone="uc")          # Ɇ
def E_stroke(g: G):
    bw = LU.w_E(g)
    g.include("E")
    _slash(g, bw * 0.5, -90, g.cap + 90, slope=0.3)


@glyph("uni0187", 0x187, zone="uc")          # Ƈ
def C_hook(g: G):
    bw = LU.w_C(g)
    c_hook(g, 0, bw, -g.ov, g.cap + g.ov, 125 + g.grow * 0.2, t_bot=1 - LU.C_TOP, k=KR, arc=True)


@glyph("uni0193", 0x193, zone="uc")          # Ɠ
def G_hook(g: G):
    """Ɠ: the G (`latin_upper.g_round`: round bottom turning up into the
    straight right side, bottom extreme where both quarters have equal
    curvature) with the Ƈ hook on top."""
    bw = LU.w_G(g)
    y0, y1 = -g.ov, g.cap + g.ov
    cx = bw / 2
    left, xr = g.hw, bw - g.hw
    yt, ybt = y1 - g.hh, y0 + g.hh
    cy = (y0 + y1) / 2
    yb = g.cap * 0.45 - g.grow * 0.05          # bar centre
    yj = g.cap * 0.27                          # right side turns into the bottom
    q = ((yj - ybt) / (cy - ybt)) ** 0.5
    cb = left + (xr - left) / (1 + q)
    xt = bw - g.hw - 10
    ye = y1 + 125 + g.grow * 0.2 - g.hh
    (hook_top(g, cx + 8, yt, xt, ye)
        .h(left, cy, k=KR)
        .v(cb, ybt, k=KR)
        .h(xr, yj, k=KR)
        .l(xr, yb)
        .end())
    g.bar(cx + 14, bw, yb)


@glyph("uni0191", 0x191, zone="uc")          # Ƒ
def F_hook(g: G):
    bw = LU.w_F(g)
    hook_down(g.pen(g.hw, g.cap - g.hh), g, g.hw, d=-1, tail=10).end()
    tuck(g, "l", (110 + g.grow * 0.3) * 0.4)
    LU.e_bars(g, 0, bw, bottom=False, mid_y=LU.bar_y(g) - 14)


@glyph("uni024A", 0x24A, zone="uc")          # Ɋ
def Q_tail(g: G):
    bw = g.wd(580, 450, grow=0.6)
    xs = bw - g.hw
    bowl_left(g, xs, 0, -g.ov, g.cap + g.ov)
    retro(g.pen(xs, g.cap - g.hh), g, xs, bot=g.desc - g.ov * 0.4).end()
    tuck(g, "r", retro_over(g) * 0.5)


@glyph("uni0222", 0x222, zone="uc")          # Ȣ
def OU(g: G):
    bw = g.wd(520, 446, grow=0.6)
    ou(g, bw, g.cap, g.cap * 0.47)


@glyph("uni0220", 0x220, zone="uc")          # Ƞ
def N_long(g: G):
    bw = g.wd(540, 446, grow=0.7)
    g.stem(0, 0, g.cap)
    arch_tail(g, g.hw, bw - g.hw, g.cap + g.ov * 0.4, "long", join_y=g.cap * 0.62)


@glyph("uniA7AD", 0xA7AD, zone="uc")         # Ɬ
def L_belt(g: G):
    g.include("L")
    belt(g, g.hw, g.cap * 0.5)


# ---------------------------------------------------------------------------
# small capitals (skeleton transforms of the capitals)
# ---------------------------------------------------------------------------

def small_cap(name, cp, src, src_w, sans, mono, grow=0.6, turned=False):
    def sy(g):
        return (g.xh - g.H) / (g.cap - g.H)

    def sx(g):
        sw = src_w(g)
        tw = g.wd(sans, mono, grow=grow)
        return (tw - g.W) / (sw - g.W)

    def dx(g):
        return g.hw * (1 - sx(g))

    if turned:
        derive(name, cp, src=src, sx=sx, sy=lambda g: -sy(g), dx=dx,
               dy=lambda g: g.xh - g.hh * (1 - sy(g)), zone="lc")
    else:
        derive(name, cp, src=src, sx=sx, sy=sy, dx=dx,
               dy=lambda g: g.hh * (1 - sy(g)), zone="lc")


def _w_Iss08(g):
    return g.wd(320, 380, grow=0.8)


small_cap("uni026A", 0x26A, "I.ss08", _w_Iss08, 250, 370)              # ɪ
small_cap("uni028F", 0x28F, "Y", LU.w_Y, 480, 470)                     # ʏ
small_cap("uni0280", 0x280, "R", LU.w_R, 430, 440)                     # ʀ
small_cap("uni0281", 0x281, "R", LU.w_R, 430, 440, turned=True)        # ʁ
small_cap("uni029C", 0x29C, "H", LU.w_H, 450, 430)                     # ʜ
small_cap("uni029F", 0x29F, "L", LU.w_L, 340, 400)                     # ʟ
small_cap("uni0262", 0x262, "G", LU.w_G, 490, 446)                     # ɢ
small_cap("uni0274", 0x274, "N", LU.w_N, 470, 430)                     # ɴ
small_cap("uni0299", 0x299, "B", LU.w_B, 420, 430)                     # ʙ
small_cap("uni029B", 0x29B, "uni0193", LU.w_G, 490, 446)               # ʛ


# ---------------------------------------------------------------------------
# modifier letters (superscripts)
# ---------------------------------------------------------------------------

SUP_S = 0.62
SUP_W = 0.82
SUP_DY = 395

_SUPS = [
    # lowercase / IPA sources
    (0x2B0, "h"), (0x2B1, "uni0266"), (0x2B2, "j"), (0x2B3, "r"), (0x2B4, "uni0279"),
    (0x2B5, "uni027B"), (0x2B6, "uni0281"), (0x2B7, "w"), (0x2B8, "y"),
    (0x2E0, "uni0263"), (0x2E1, "l"), (0x2E2, "s"), (0x2E3, "x"), (0x2E4, "uni0295"),
    (0x2C0, "uni0294"), (0x2C1, "uni0295"),
    (0x1D43, "a"), (0x1D44, "uni0250"), (0x1D45, "uni0251"), (0x1D47, "b"), (0x1D48, "d"),
    (0x1D49, "e"), (0x1D4A, "schwa"), (0x1D4B, "uni025B"), (0x1D4D, "g"), (0x1D4F, "k"),
    (0x1D50, "m"), (0x1D52, "o"), (0x1D53, "uni0254"), (0x1D56, "p"), (0x1D57, "t"),
    (0x1D58, "u"), (0x1D5A, "uni026F"), (0x1D5B, "v"),
    (0x1D9B, "uni0252"), (0x1D9C, "c"), (0x1D9D, "uni0255"), (0x1D9F, "uni025C"),
    (0x1DA0, "f"), (0x1DA1, "uni025F"), (0x1DA2, "uni0261"), (0x1DA3, "uni0265"),
    (0x1DA4, "uni0268"), (0x1DA5, "uni0269"), (0x1DA6, "uni026A"), (0x1DA9, "uni026D"),
    (0x1DAB, "uni029F"), (0x1DAC, "uni0271"), (0x1DAD, "uni0270"), (0x1DAE, "uni0272"),
    (0x1DAF, "uni0273"), (0x1DB0, "uni0274"), (0x1DB1, "obarred"), (0x1DB2, "uni0278"),
    (0x1DB4, "uni0283"), (0x1DB6, "uni0289"), (0x1DB7, "uni028A"), (0x1DB9, "uni028B"),
    (0x1DBA, "uni028C"), (0x1DBB, "z"), (0x1DBC, "uni0290"), (0x1DBD, "uni0291"),
    (0x1DBE, "uni0292"),
    (0x207F, "n"), (0x2071, "i"),
    # capitals
    (0x1D2C, "A"), (0x1D2E, "B"), (0x1D30, "D"), (0x1D31, "E"), (0x1D32, "uni018E"),
    (0x1D33, "G"), (0x1D34, "H"), (0x1D35, "I"), (0x1D36, "J"), (0x1D37, "K"),
    (0x1D38, "L"), (0x1D39, "M"), (0x1D3A, "N"), (0x1D3C, "O"), (0x1D3D, "uni0222"),
    (0x1D3E, "P"), (0x1D3F, "R"), (0x1D40, "T"), (0x1D41, "U"), (0x1D42, "W"),
]

for _cp, _src in _SUPS:
    derive(f"uni{_cp:04X}", _cp, src=_src, sx=SUP_S, dy=SUP_DY, wscale=SUP_W)
