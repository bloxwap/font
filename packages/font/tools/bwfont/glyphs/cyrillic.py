"""Cyrillic skeletons.

Covers Russian, Ukrainian, Belarusian, Bulgarian, Serbian, Macedonian and the
extended Cyrillic letters of Kazakh, Uzbek, Tatar, Bashkir, Kyrgyz, Mongolian,
Chuvash, Tajik, Abkhaz, Khanty, Khakas ...

Look-alikes of Latin letters (А В Е К М Н О Р С Т Х Ѕ І Ј Ү а е о р с у х ...)
are aliases (composites.py) and are *not* drawn here; accented letters
(Й Ё Ї Ў Ѓ Ќ Ӂ Ӝ Ӟ Ӣ Ӥ Ӯ Ӵ Ӹ ...) are composed automatically from NFD.

Construction follows latin_upper / latin_lower:

* stems, bars and diagonals are separate strokes; their round caps make the
  rounded corners;
* bowls of Б Ь Ъ Ы Љ Њ Ѣ (and в ь ъ ы љ њ ѣ) are one smooth stroke that leaves
  the stem centre-line horizontally (`bowl_r`);
* arches and hooks ride up the stem centre-line, then peel off tangentially
  (`arch`, `arch_hook`), so counters stay round;
* descender tails (Ц Щ Џ Д Җ Қ Ң Ҭ Ҳ Ҷ ...) are short round-capped stems that
  hang from the base bar to `tail_depth`, a little right of the last stem;
* lowercase в г д ж з и к л м н п т ц ч ш щ ъ ы ь are small-cap-like forms.
"""
from __future__ import annotations

from ..skeleton import glyph, G, mirror_x, shift
from .latin_lower import arch, c_shape, rot180, EPS, LEAD
from .latin_upper import (bowl_r, c_open, bar_y, DIAG, KR,
                          w_C, w_H, w_K, w_M, w_N, w_R, w_T, w_X, w_Y)
from .marks import _base, _h, _top, MW


def U(cp):
    return f"uni{cp:04X}"


def both(cu, cl):
    """Register fn(g, lc) for a capital and/or a lowercase codepoint."""
    def deco(fn):
        if cu:
            glyph(U(cu), cu, zone="uc")(lambda g, fn=fn: fn(g, False))
        if cl:
            glyph(U(cl), cl, zone="lc")(lambda g, fn=fn: fn(g, True))
        return fn
    return deco


def top_of(g, lc):
    return g.xh if lc else g.cap


def wd(g, lc, uc_spec, lc_spec):
    """Body width from (sans, mono, grow) specs for capital / lowercase."""
    return g.wd(*(lc_spec if lc else uc_spec))


# ---------------------------------------------------------------------------
# shared constructions
# ---------------------------------------------------------------------------

def tail_depth(g):
    """Ink bottom of descender tails."""
    return -140 - g.grow * 0.15


def tail_c(g, xs, s=1.0):
    """Centre x of a tail hanging just right of a stem centred on xs."""
    return xs + g.W * s * 0.5 + 30 + g.grow * 0.1


def tail(g, tc, s=1.0):
    g.vstem(tc, tail_depth(g), g.H * s, w=s)


def foot_tail(g, xs, s=1.0):
    """Base-bar stub from a stem / leg end at skeleton x `xs` plus a tail."""
    tc = tail_c(g, xs, s)
    g.bar(xs - g.hw * s, tc + g.hw * s, g.hh * s, w=s)
    tail(g, tc, s)
    return tc


def curl_tail(g, xs, s=1.0):
    """'with tail' (Ӆ Ӊ Ӎ): a stub from the stem and a tail curling left."""
    tc = tail_c(g, xs, s) + 10
    g.bar(xs - g.hw * s, tc + g.hw * s, g.hh * s, w=s)
    d = tail_depth(g) - 6
    (g.pen(tc, g.hh * s, s)
        .l(tc, -24)
        .v(tc - 70 - g.grow * 0.35, d + g.hh * s, k=0.6)
        .end())
    return tc


def hook_down(p, g, xs):
    """Continue a downward path at skeleton x `xs` into a hook that turns
    left below the baseline (Ђ ђ Ӈ Ҕ ...)."""
    bot = g.desc + 30
    (p.l(xs, -10)
        .v(xs - 96 - g.grow * 0.3, bot + g.hh, k=0.6)
        .l(xs - 150 - g.grow * 0.5, bot + g.hh))
    return p


def arch_hook(g, xl, xr, top, join_y, apex=0.54):
    """n-style shoulder from a stem at xl whose right leg (xr) runs below the
    baseline into a hook.  Like `arch()`, the stroke first rides up the stem's
    centre-line (width LEAD) and peels off tangentially, so the counter has no
    lobe or dent where the shoulder leaves the stem."""
    ty = top - g.hh
    ax = xl + (xr - xl) * apex
    lead = (top - join_y) * 0.24
    p = (g.pen(xl, join_y - lead, LEAD)
         .l(xl, join_y)
         .v(ax, ty, k=0.62, w=1.0, k2=0.56)
         .h(xr, top - (top - join_y) * 0.62, k=0.62, w=1.0))
    hook_down(p, g, xr)
    p.end()


def mid_hook(g, xs, lc):
    """Middle hook hanging off a stem centred on xs (Ҕ Ҧ Ԡ Ԣ ...).
    Returns the skeleton x of the hook's leg."""
    top = g.xh * 0.62 if lc else g.cap * 0.58
    xr = xs + (250 if lc else 300) + g.grow * 0.5
    arch_hook(g, xs, xr, top, top * 0.55)
    return xr


def karms(g, xa, xb, top, jy, d=DIAG, t=None):
    """K-style arm + leg to the right of a stem whose right ink edge is xa.
    Returns the skeleton x of the leg's foot."""
    r, rh = g.hw * d, g.hh * d
    j0 = (xa + 6, top * jy)
    j1 = (xb - r * 1.06, top - rh)
    g.line(*j0, *j1, w0=d * 0.98, w1=d)
    t = 0.3 + g.grow * 0.0006 if t is None else t
    sx = j0[0] + (j1[0] - j0[0]) * t
    sy = j0[1] + (j1[1] - j0[1]) * t
    g.line(sx, sy, xb - r, rh, d)
    return xb - r


def ze_shape(g, x0, x1, y0, y1, ym, xm=None, t_top=0.78, t_bot=0.21, narrow=24):
    """З: an upper and a lower bowl meeting at a short middle bar.
    y0/y1: ink bottom / top (with overshoot); ym: centre of the middle bar;
    xm: left ink end of the middle bar."""
    hh, hw = g.hh, g.hw
    bw = x1 - x0
    cx = x0 + bw * 0.5
    xm = x0 + bw * 0.30 if xm is None else xm
    ru = x1 - hw - narrow - g.grow * 0.1
    rl = x1 - hw
    h = y1 - y0
    (g.pen(x0 + hw + 6, y0 + h * t_top)
        .to(cx - 6, y1 - hh, (0.36, 1), "r", k=0.62)
        .h(ru, (y1 - hh + ym) / 2, k=0.6)
        .v(cx - 14, ym, k=0.6)
        .l(xm + hw, ym)
        .end())
    (g.pen(xm + hw, ym)
        .l(cx - 4, ym)
        .h(rl, (ym + y0 + hh) / 2, k=0.6)
        .v(cx - 6, y0 + hh, k=0.6)
        .to(x0 + hw + 4, y0 + h * t_bot, "l", (-0.34, 1), k=0.62)
        .end())


def e_shape(g, bw, top, spur=0.0):
    """Latin-e construction scaled to `top` (Ҽ ҽ).  `spur` extends the bar to
    the left beyond the bowl."""
    y0, y1 = -g.ov, top + g.ov
    cx = bw / 2
    yb = top * 0.5 + g.hh * 0.2
    left, right = g.hw, bw - g.hw
    (g.pen(right, yb)
        .v(cx, y1 - g.hh, k=0.6)
        .h(left, (y0 + y1) / 2)
        .v(cx + 6, y0 + g.hh)
        .to(bw - g.hw - 6, (y1 - y0) * 0.2 + y0, "r", (0.38, 1), k=0.62)
        .end())
    g.line(left - spur, yb, right, yb)


def ch_bowl(g, bw, top, ybot, xs=None):
    """Ч: left leg from the top, round bottom at ink `ybot`, merging into the
    right stem (skeleton x = bw - hw): an upside-down `arch()`, so it runs along
    the stem's centre-line before it merges (round counter, no taper)."""
    yj = ybot + (top - ybot) * 0.45
    g.transform(rot180(bw / 2, top / 2))
    arch(g, g.hw, bw - g.hw, top - ybot, 0, top - yj)
    g.transform(None)


def round_loop(g, l, b, r, t, k=None, w=1.0, lrun=0.0, rrun=0.0):
    """Closed round loop on a skeleton box l..r, b..t whose left / right sides
    run straight for lrun / rrun units around the middle (0 = a plain oval
    side).  Narrow Mono bowls get short straight sides so their top and bottom
    stay round instead of pinching the counter into a lens.  Runs must be > 0
    in every master or 0 in all."""
    cy = (b + t) / 2
    cx = (l + r) / 2
    p = g.pen(r, cy + rrun / 2, w).v(cx, t, k=k).h(l, cy + lrun / 2, k=k)
    if lrun:
        p.l(l, cy - lrun / 2)
    p.v(cx, b, k=k).h(r, cy - rrun / 2, k=k).close()


def mono_run(g, b, t):
    """Straight side length for a narrow Mono loop (0 in Sans).  Grows with
    weight (linearly in W, > 0 in every master) so that the top and bottom
    curves keep a radius above the pen's at Black."""
    return (t - b) * (0.05 + (g.W - 22) * 0.0029) if g.mono else 0.0


# ---------------------------------------------------------------------------
# Б Г Ґ Ғ Ҕ
# ---------------------------------------------------------------------------

@both(0x411, None)
def Be(g, lc):
    bw = g.wd(500, 440, grow=0.6)
    g.stem(0, 0, g.cap)
    g.bar(0, bw - 16, g.cap - g.hh)
    jm = g.cap * 0.56
    bowl_r(g, g.hw, bw, 0, jm + g.hh, sv=0.06)


def ghe_w(g, lc):
    return wd(g, lc, (420, 410, 0.5), (320, 400, 0.5))


def ghe(g, lc, x0=0.0):
    top = top_of(g, lc)
    bw = ghe_w(g, lc) + x0
    if g.mono and lc:
        x0 = bw * 0.2
    g.stem(x0, 0, top)
    g.bar(x0, bw, top - g.hh)
    return bw, x0


@both(0x413, 0x433)
def Ghe(g, lc):
    ghe(g, lc)


@both(0x490, 0x491)
def GheUp(g, lc):
    top = top_of(g, lc)
    bw, x0 = ghe(g, lc)
    g.stem(bw - g.W, top - g.H, top + (150 if not lc else 130) + g.grow * 0.2)
    g.anchor("top", (x0 + bw) / 2, top)


@both(0x492, 0x493)
def GheStroke(g, lc):
    top = top_of(g, lc)
    dx = (70 if lc else 90) + g.grow * 0.35
    if g.mono:
        dx = 64 + g.grow * 0.3
    bw = ghe_w(g, lc) + dx
    if g.mono and lc:
        bw = ghe_w(g, lc)
    g.stem(dx, 0, top)
    g.bar(dx, bw, top - g.hh)
    g.bar(0, dx + g.W + (110 if lc else 140), top * 0.47)


@both(0x494, 0x495)
def GheHook(g, lc):
    top = top_of(g, lc)
    bw = ghe_w(g, lc)
    g.stem(0, 0, top)
    g.bar(0, bw, top - g.hh)
    mid_hook(g, g.hw, lc)


# ---------------------------------------------------------------------------
# Д Л Љ Ӆ Ԓ Ԡ
# ---------------------------------------------------------------------------

def de(g, lc):
    top = top_of(g, lc)
    bw = wd(g, lc, (640, 490, 0.7), (520, 480, 0.7))
    td = tail_depth(g)
    g.stem(bw - g.W, td, top)                  # right stem runs into the tail
    g.stem(0, td, g.H)                         # left tail
    g.bar(0, bw, g.hh)                         # base
    xt = bw * (0.22 if not lc else 0.2) + g.hw + g.grow * 0.15
    xb = g.hw + g.W * 0.3 + 22
    g.line(xt, top - g.hh, xb, g.H, DIAG)
    g.bar(xt - g.hw, bw, top - g.hh)
    g.anchor("top", bw / 2 + 10, top)


@both(0x414, 0x434)
def De(g, lc):
    de(g, lc)


def el_w(g, lc):
    return wd(g, lc, (570, 460, 0.7), (460, 456, 0.7))


def el(g, lc, bw, right="stem"):
    """Л with a curved left leg.  right: 'stem' | 'hook' | 'none'."""
    top = top_of(g, lc)
    xs = bw - g.hw
    if right == "stem":
        g.stem(bw - g.W, 0, top)
    elif right == "hook":
        p = g.pen(xs, top - g.hh)
        hook_down(p, g, xs)
        p.end()
    xt = (150 if not lc else 124) + g.grow * 0.55
    if g.mono:
        xt = (120 if not lc else 104) + g.grow * 0.4
    g.bar(xt - g.hw, bw, top - g.hh)
    xe = g.hw * 0.9 + 2
    yk = g.hh + (xt - xe) * (1.5 if not lc else 1.25)
    (g.pen(xt, top - g.hh)
        .l(xt, yk)
        .v(xe, g.hh, k=0.6)
        .end())
    return xs


@both(0x41B, 0x43B)
def El(g, lc):
    el(g, lc, el_w(g, lc))


@both(0x4C5, 0x4C6)
def ElTail(g, lc):
    xs = el(g, lc, el_w(g, lc))
    curl_tail(g, xs)
    g.anchor("top", el_w(g, lc) / 2, top_of(g, lc))


@both(0x512, 0x513)
def ElHook(g, lc):
    el(g, lc, el_w(g, lc), right="hook")


@both(0x520, 0x521)
def ElMidHook(g, lc):
    bw = wd(g, lc, (520, 400, 0.7), (420, 380, 0.7))
    xs = el(g, lc, bw)
    mid_hook(g, xs, lc)


@both(0x409, 0x459)
def Lje(g, lc):
    top = top_of(g, lc)
    lw = wd(g, lc, (470, 300, 0.6), (390, 290, 0.6))
    bb = wd(g, lc, (330, 200, 0.4), (290, 196, 0.4))
    xs = el(g, lc, lw)
    jm = top * (0.56 if not lc else 0.58)
    bowl_r(g, xs, lw + bb, 0, jm + g.hh, sv=0.06)


# ---------------------------------------------------------------------------
# Ж Җ
# ---------------------------------------------------------------------------

def zhe(g, lc):
    top = top_of(g, lc)
    bw = wd(g, lc, (820, 540, 1.1), (680, 520, 1.0))
    s = 0.84 if g.mono else 1.0
    d = 0.8 if g.mono else DIAG
    cx = bw / 2
    g.vstem(cx, 0, top, w=s)
    jy = 0.36 if lc else 0.33
    xa = cx + g.hw * s
    xe = karms(g, xa, bw, top, jy, d)
    g.transform(mirror_x(cx))
    karms(g, xa, bw, top, jy, d)
    g.transform(None)
    g.anchor("top", cx, top)
    return bw, xe, s


@both(0x416, 0x436)
def Zhe(g, lc):
    zhe(g, lc)


@both(0x496, 0x497)
def ZheTail(g, lc):
    bw, xe, s = zhe(g, lc)
    foot_tail(g, xe, s)


# ---------------------------------------------------------------------------
# З Ҙ Ԑ Ӡ
# ---------------------------------------------------------------------------

def ze_w(g, lc):
    return wd(g, lc, (520, 446, 0.6), (420, 436, 0.6))


def ze(g, lc):
    top = top_of(g, lc)
    bw = ze_w(g, lc)
    ze_shape(g, 0, bw, -g.ov, top + g.ov, top * 0.54 + g.hh * 0.1)
    return bw


@both(0x417, 0x437)
def Ze(g, lc):
    ze(g, lc)


@both(0x498, 0x499)
def ZeTail(g, lc):
    bw = ze(g, lc)
    g.vstem(bw / 2 - 6, tail_depth(g), -g.ov + g.H)


@both(0x510, 0x511)
def ReversedZe(g, lc):
    bw = ze_w(g, lc)
    g.transform(mirror_x(bw / 2))
    ze(g, lc)
    g.transform(None)


@both(0x4E0, 0x4E1)
def Dze(g, lc):
    """Abkhazian Dze (ezh-like): flat top, diagonal, round lower bowl.  The
    lowercase drops into the descender."""
    bw = wd(g, lc, (500, 446, 0.6), (430, 436, 0.6))
    if lc:
        y1, y0 = g.xh, g.desc - g.ov
        ym = g.xh * 0.32
    else:
        y1, y0 = g.cap, -g.ov
        ym = g.cap * 0.56
    r = g.hw * 1.1
    g.bar(8, bw - 6, y1 - g.hh)
    xd = bw * 0.36
    g.line(bw - 6 - r, y1 - g.hh, xd, ym, DIAG)
    cx = bw / 2
    h = y1 - y0
    (g.pen(xd, ym)
        .l(cx - 6, ym)
        .h(bw - g.hw, (ym + y0 + g.hh) / 2, k=0.6)
        .v(cx - 6, y0 + g.hh, k=0.6)
        .to(g.hw + 4, y0 + h * (0.14 if lc else 0.2), "l", (-0.34, 1), k=0.62)
        .end())


# ---------------------------------------------------------------------------
# И
# ---------------------------------------------------------------------------

def ii(g, lc):
    if not lc:
        bw = w_N(g)
        g.include("N", mirror_x(bw / 2))
        return bw
    bw = g.wd(456, 456, grow=0.7)
    g.stem(0, 0, g.xh)
    g.stem(bw - g.W, 0, g.xh)
    g.line(g.hw, g.hh, bw - g.hw, g.xh - g.hh, DIAG)
    return bw


@both(0x418, 0x438)
def Ii(g, lc):
    ii(g, lc)


# ---------------------------------------------------------------------------
# К-family: к Қ Ҝ Ҟ Ҡ Ӄ
# ---------------------------------------------------------------------------

def ka_lc(g):
    bw = g.wd(430, 456, grow=0.6)
    g.stem(0, 0, g.xh)
    xe = karms(g, g.W, bw, g.xh, 0.36)
    return bw, xe


@both(None, 0x43A)
def ka(g, lc):
    ka_lc(g)


def ka_any(g, lc, dx=0.0):
    """K (capital: the Latin K) shifted by dx.  Returns (bw, leg foot x)."""
    if lc:
        if dx:
            g.transform(shift(dx, 0))
        bw, xe = ka_lc(g)
        g.transform(None)
        return bw + dx, xe + dx
    bw = w_K(g)
    g.include("K", shift(dx, 0) if dx else None)
    return bw + dx, bw - g.hw * DIAG + dx


@both(0x49A, 0x49B)
def KaTail(g, lc):
    bw, xe = ka_any(g, lc)
    foot_tail(g, xe)
    g.anchor("top", bw / 2, top_of(g, lc))


@both(0x49C, 0x49D)
def KaVStroke(g, lc):
    top = top_of(g, lc)
    bw, xe = ka_any(g, lc)
    # crosses the upper arm, clear of the leg
    jy = 0.36 if lc else 0.29
    r, rh = g.hw * DIAG, g.hh * DIAG
    x0, y0 = g.W + 6, top * jy
    x1, y1 = bw - r * 1.06, top - rh
    t = 0.5
    xv, yv = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    g.vstem(xv, yv - top * 0.2, min(yv + top * 0.2, top), w=0.9)


@both(0x49E, 0x49F)
def KaStroke(g, lc):
    top = top_of(g, lc)
    dx = 74 + g.grow * 0.35
    if lc:
        # lowercase: ascender stem with a stroke through it (ħ-like)
        g.transform(shift(dx, 0))
        bw = g.wd(430, 456, grow=0.6)
        g.stem(0, 0, g.asc)
        karms(g, g.W, bw, g.xh, 0.36)
        g.transform(None)
        g.bar(0, dx + g.W + 110, (g.xh + g.asc) / 2 + 12)
        return
    bw, xe = ka_any(g, lc, dx)
    g.bar(0, dx + g.W + 130, top * 0.77)


@both(0x4A0, 0x4A1)
def Bashkir_Qa(g, lc):
    top = top_of(g, lc)
    dx = (110 if lc else 140) + g.grow * 0.4
    if g.mono:
        dx = 86 + g.grow * 0.3
    bw, xe = ka_any(g, lc, dx)
    g.bar(0, dx + g.W, top - g.hh)


@both(0x4C3, 0x4C4)
def KaHook(g, lc):
    top = top_of(g, lc)
    bw = wd(g, lc, (520, 456, 0.6), (430, 446, 0.6))
    g.stem(0, 0, top)
    yj = top * 0.44
    r, rh = g.hw * DIAG, g.hh * DIAG
    g.line(g.W + 4, yj, bw - r * 1.06, top - rh, w0=0.9, w1=DIAG)
    xr = bw - g.hw - 12
    rad = min(120 + g.grow * 0.3, (yj - 40) * 0.6)
    p = (g.pen(g.hw, yj)
         .l(xr - rad, yj)
         .h(xr, yj - rad, k=0.6))
    hook_down(p, g, xr)
    p.end()


# ---------------------------------------------------------------------------
# Н-family: н Ң Ҥ Ӈ Ӊ Ԣ Њ
# ---------------------------------------------------------------------------

def en_w(g, lc):
    return wd(g, lc, None, (440, 456, 0.7)) if lc else w_H(g)


def en(g, lc, right="stem", bw=None):
    top = top_of(g, lc)
    bw = en_w(g, lc) if bw is None else bw
    if not lc and right == "stem" and bw == w_H(g):
        g.include("H")
        return bw
    g.stem(0, 0, top)
    xs = bw - g.hw
    if right == "stem":
        g.stem(bw - g.W, 0, top)
    elif right == "hook":
        p = g.pen(xs, top - g.hh)
        hook_down(p, g, xs)
        p.end()
    yb = bar_y(g) if not lc else g.xh * 0.5 + 2
    g.bar(g.hw, bw - g.hw, yb)
    return bw


@both(None, 0x43D)
def en_lc(g, lc):
    en(g, lc)


@both(0x4A2, 0x4A3)
def EnTail(g, lc):
    bw = en(g, lc)
    foot_tail(g, bw - g.hw)
    g.anchor("top", bw / 2, top_of(g, lc))


@both(0x4A4, 0x4A5)
def EnGhe(g, lc):
    top = top_of(g, lc)
    bw = wd(g, lc, (500, 330, 0.6), (420, 320, 0.6))
    ext = wd(g, lc, (190, 150, 0.3), (160, 140, 0.3))
    en(g, lc, bw=bw)
    g.bar(bw - g.W, bw + ext, top - g.hh)


@both(0x4C7, 0x4C8)
def EnHook(g, lc):
    en(g, lc, right="hook")


@both(0x4C9, 0x4CA)
def EnTailCurl(g, lc):
    bw = en(g, lc)
    curl_tail(g, bw - g.hw)
    g.anchor("top", bw / 2, top_of(g, lc))


@both(0x522, 0x523)
def EnMidHook(g, lc):
    bw = wd(g, lc, (500, 330, 0.6), (420, 320, 0.6))
    en(g, lc, bw=bw)
    mid_hook(g, bw - g.hw, lc)


@both(0x40A, 0x45A)
def Nje(g, lc):
    top = top_of(g, lc)
    nw = wd(g, lc, (440, 290, 0.6), (380, 280, 0.6))
    bb = wd(g, lc, (330, 200, 0.4), (290, 196, 0.4))
    g.stem(0, 0, top)
    g.stem(nw - g.W, 0, top)
    jm = top * (0.56 if not lc else 0.58)
    # crossbar and bowl top are one stroke from the left stem
    bowl_r(g, g.hw, nw + bb, 0, jm + g.hh, rx=(jm - g.H) / 2 * 1.0, sv=0.06)


# ---------------------------------------------------------------------------
# П-family: п Ҧ Ԥ Џ
# ---------------------------------------------------------------------------

def pe(g, lc, bw=None):
    top = top_of(g, lc)
    bw = (w_H(g) if not lc else g.wd(440, 456, grow=0.7)) if bw is None else bw
    g.stem(0, 0, top)
    g.stem(bw - g.W, 0, top)
    g.bar(0, bw, top - g.hh)
    return bw


@both(0x41F, 0x43F)
def Pe(g, lc):
    pe(g, lc)


@both(0x4A6, 0x4A7)
def PeMidHook(g, lc):
    bw = pe(g, lc, wd(g, lc, (500, 330, 0.6), (420, 320, 0.6)))
    mid_hook(g, bw - g.hw, lc)


@both(0x524, 0x525)
def PeTail(g, lc):
    bw = pe(g, lc)
    foot_tail(g, bw - g.hw)
    g.anchor("top", bw / 2, top_of(g, lc))


@both(0x40F, 0x45F)
def Dzhe(g, lc):
    top = top_of(g, lc)
    bw = w_H(g) if not lc else g.wd(440, 456, grow=0.7)
    g.stem(0, 0, top)
    g.stem(bw - g.W, 0, top)
    g.bar(0, bw, g.hh)
    g.vstem(bw / 2, tail_depth(g), g.H)


# ---------------------------------------------------------------------------
# У ү Ұ ұ
# ---------------------------------------------------------------------------

@both(0x423, None)
def U_(g, lc):
    """У: a long straight diagonal from the top right to the baseline (like the
    straight Latin y descender: no curled foot), and a short left arm that meets
    it a little below the middle."""
    bw = g.wd(570, 490, grow=0.8)
    top = g.cap
    r, rh = g.hw * DIAG, g.hh * DIAG
    tr = (bw - r, top - rh)
    ft = (bw * 0.2 + g.grow * 0.1, rh)
    yv = top * 0.36
    vx = tr[0] + (ft[0] - tr[0]) * (yv - tr[1]) / (ft[1] - tr[1])
    g.line(*tr, *ft, DIAG)
    g.line(r, top - rh, vx, yv, DIAG)
    g.anchor("top", bw / 2, top)


def ue(g, lc):
    """Straight u (ү): v-shaped arms meeting at the baseline + descender stem;
    the capital is the Latin Y."""
    if not lc:
        bw = w_Y(g)
        g.include("Y")
        return bw, g.cap * 0.42
    bw = g.wd(456, 470, grow=0.7)
    r, rh = g.hw * DIAG, g.hh * DIAG
    cx = bw / 2
    vy = 4
    g.line(r, g.xh - rh, cx, vy, DIAG)
    g.line(bw - r, g.xh - rh, cx, vy, DIAG)
    g.vstem(cx, g.desc, vy + g.hh)
    return bw, vy


@both(None, 0x4AF)
def ue_lc(g, lc):
    ue(g, lc)


@both(0x4B0, 0x4B1)
def UeStroke(g, lc):
    bw, vy = ue(g, lc)
    cx = bw / 2
    hw = wd(g, lc, (150, 140, 0.5), (130, 130, 0.5))
    y = g.cap * 0.28 if not lc else -70 - g.grow * 0.1
    g.bar(cx - hw, cx + hw, y)


# ---------------------------------------------------------------------------
# Ф ф Ѳ ѳ
# ---------------------------------------------------------------------------

@both(0x424, None)
def Ef(g, lc):
    bw = g.wd(700, 500, grow=0.8)
    s = 0.88 if g.mono else 1.0
    g.vstem(bw / 2, 0, g.cap)
    g.oval(0, g.cap * 0.12 - g.ov, bw, g.cap * 0.88 + g.ov, k=KR, w=s)


def ef_bowl(g, cx, s):
    """Left bowl of ф: a closed round loop whose right side runs straight along
    the stem's centre-line (EPS inside it), so the stem overlaps it and the
    counter is a clean round (as `bowl_left()`, with the stem's width factor)."""
    l, r = g.hw * s, cx - EPS
    b, t = -g.ov + g.hh * s, g.xh + g.ov - g.hh * s
    run = mono_run(g, b, t) if g.mono else 10 + (g.W - 22) * 0.6
    round_loop(g, l, b, r, t, w=s, lrun=mono_run(g, b, t), rrun=run)


def ef_lc(g, y0, y1):
    bw = g.wd(680, 500, grow=1.0)
    if g.mono:                     # three verticals in the cell: widen when heavy
        bw += g.grow * 0.45
    cx = bw / 2
    s = 0.84 if g.mono else 1.0
    g.vstem(cx, y0, y1, w=s)
    ef_bowl(g, cx, s)
    g.transform(mirror_x(cx))
    ef_bowl(g, cx, s)
    g.transform(None)
    g.anchor("top", cx, g.asc)


@both(None, 0x444)
def ef(g, lc):
    ef_lc(g, g.desc, g.asc)


@both(0x472, 0x473)
def Fita(g, lc):
    top = top_of(g, lc)
    if lc:
        bw = g.wd(478, 476)
        g.oval(0, -g.ov, bw, top + g.ov)
    else:
        bw = g.wd(640, 470, grow=0.6)
        g.oval(0, -g.ov, bw, top + g.ov, k=KR)
    g.bar(g.hw, bw - g.hw, top / 2 + 2)


# ---------------------------------------------------------------------------
# Ц Ҵ Ш Щ
# ---------------------------------------------------------------------------

def tse(g, lc, dx=0.0):
    top = top_of(g, lc)
    bw = wd(g, lc, (540, 380, 0.7), (440, 370, 0.7))
    g.stem(dx, 0, top)
    g.stem(dx + bw - g.W, 0, top)
    tc = tail_c(g, dx + bw - g.hw)
    g.bar(dx, tc + g.hw, g.hh)
    tail(g, tc)
    g.anchor("top", dx + bw / 2, top)
    return bw + dx


@both(0x426, 0x446)
def Tse(g, lc):
    tse(g, lc)


@both(0x4B4, 0x4B5)
def TeTse(g, lc):
    top = top_of(g, lc)
    dx = wd(g, lc, (150, 90, 0.4), (130, 84, 0.4))
    tse(g, lc, dx)
    g.bar(0, dx + g.W, top - g.hh)


def sha(g, lc, with_tail=False):
    top = top_of(g, lc)
    s = 0.84 if g.mono else 1.0
    bw = wd(g, lc, (780, 500, 1.0), (660, 490, 1.0))
    if with_tail and g.mono:
        bw -= 60
    sw = g.W * s
    g.stem(0, 0, top, w=s)
    g.stem((bw - sw) / 2, 0, top, w=s)
    g.stem(bw - sw, 0, top, w=s)
    xe = bw
    if with_tail:
        tc = tail_c(g, bw - sw / 2, s)
        tail(g, tc, s)
        xe = tc + g.hw * s
    g.bar(0, xe, g.hh * s, w=s)
    g.anchor("top", bw / 2, top)


@both(0x428, 0x448)
def Sha(g, lc):
    sha(g, lc)


@both(0x429, 0x449)
def Shcha(g, lc):
    sha(g, lc, True)


# ---------------------------------------------------------------------------
# Ч Ҷ Ҹ Ӌ Һ
# ---------------------------------------------------------------------------

def che(g, lc):
    top = top_of(g, lc)
    bw = wd(g, lc, (510, 440, 0.6), (420, 440, 0.6))
    g.stem(bw - g.W, 0, top)
    ybot = top * (0.33 if not lc else 0.34)
    ch_bowl(g, bw, top, ybot)
    return bw, ybot


@both(0x427, 0x447)
def Che(g, lc):
    che(g, lc)


@both(0x4B6, 0x4B7)
def CheTail(g, lc):
    bw, _ = che(g, lc)
    foot_tail(g, bw - g.hw)
    g.anchor("top", bw / 2, top_of(g, lc))


@both(0x4B8, 0x4B9)
def CheVStroke(g, lc):
    top = top_of(g, lc)
    bw, ybot = che(g, lc)
    xv = bw * 0.46
    g.vstem(xv, ybot - (90 if not lc else 70), ybot + (190 if not lc else 150), w=0.9)


@both(0x4CB, 0x4CC)
def KhakassianChe(g, lc):
    top = top_of(g, lc)
    bw, _ = che(g, lc)
    xs = bw - g.hw
    tc = xs - g.W * 0.5 - 30 - g.grow * 0.1
    g.bar(tc - g.hw, xs + g.hw, g.hh)
    tail(g, tc)
    g.anchor("top", bw / 2, top)


@both(0x4BA, None)
def Shha(g, lc):
    bw = g.wd(510, 440, grow=0.6)
    g.stem(0, 0, g.cap)
    t = g.cap * 0.64
    arch(g, g.hw, bw - g.hw, t, 0, join_y=t - t * 0.45)


# ---------------------------------------------------------------------------
# Ъ Ы Ь Ѣ
# ---------------------------------------------------------------------------

def soft_w(g, lc):
    return wd(g, lc, (490, 440, 0.6), (410, 430, 0.6))


def soft(g, lc, x0=0.0, bw=None, top=None):
    """Stem (left ink x0) + lower bowl to x0 + bw."""
    top = top_of(g, lc) if top is None else top
    bw = soft_w(g, lc) if bw is None else bw
    jm = top_of(g, lc) * (0.56 if not lc else 0.58)
    g.stem(x0, 0, top)
    bowl_r(g, x0 + g.hw, x0 + bw, 0, jm + g.hh, sv=0.06)
    return x0 + bw


@both(0x42C, 0x44C)
def SoftSign(g, lc):
    soft(g, lc)


@both(0x42A, 0x44A)
def HardSign(g, lc):
    top = top_of(g, lc)
    dx = wd(g, lc, (140, 90, 0.4), (110, 80, 0.4))
    bw = wd(g, lc, (470, 360, 0.6), (400, 360, 0.6))
    soft(g, lc, dx, bw)
    g.bar(0, dx + g.W, top - g.hh)


@both(0x42B, 0x44B)
def Yeru(g, lc):
    top = top_of(g, lc)
    bw = wd(g, lc, (680, 500, 1.0), (580, 490, 1.0))
    bb = wd(g, lc, (450, 320, 0.6), (380, 310, 0.6))
    soft(g, lc, 0, bb)
    g.stem(bw - g.W, 0, top)


@both(0x462, 0x463)
def Yat(g, lc):
    dx = (80 if lc else 100) + g.grow * 0.35
    if g.mono:
        dx = 70 + g.grow * 0.3
    bw = wd(g, lc, (470, 380, 0.6), (390, 370, 0.6))
    if lc:
        soft(g, lc, dx, bw, top=g.asc)
        g.bar(0, dx + g.W + 120, g.xh - g.hh)
    else:
        soft(g, lc, dx, bw)
        g.bar(0, dx + g.W + 150, g.cap * 0.79)


# ---------------------------------------------------------------------------
# Э Є Ҫ Ҽ Ҿ
# ---------------------------------------------------------------------------

def round_open(g, lc, mirror=False):
    top = top_of(g, lc)
    if lc:
        bw = g.wd(446, 456)
        fn = c_shape
    else:
        bw = w_C(g)
        fn = c_open
    if mirror:
        g.transform(mirror_x(bw / 2))
    fn(g, 0, bw, -g.ov, top + g.ov)
    g.transform(None)
    return bw


@both(0x42D, 0x44D)
def E_rev(g, lc):
    top = top_of(g, lc)
    bw = round_open(g, lc, mirror=True)
    y = bar_y(g) if not lc else top * 0.5 + g.hh * 0.2
    g.bar(bw * 0.3, bw - g.hw, y)


@both(0x404, 0x454)
def Ie_ukr(g, lc):
    top = top_of(g, lc)
    bw = round_open(g, lc)
    y = bar_y(g) if not lc else top * 0.5 + g.hh * 0.2
    g.bar(g.hw, bw * 0.7, y)


@both(0x4AA, 0x4AB)
def EsTail(g, lc):
    if lc:
        bw = g.wd(446, 456)
        g.include("c")
    else:
        bw = w_C(g)
        g.include("C")
    g.vstem(bw / 2 + 6, tail_depth(g), -g.ov + g.H)


def abk_che(g, lc):
    top = top_of(g, lc)
    spur = wd(g, lc, (110, 70, 0.4), (90, 60, 0.4))
    bw = wd(g, lc, (560, 400, 0.6), (468, 400, 0.6))
    g.transform(shift(spur, 0))
    e_shape(g, bw, top, spur=spur)
    g.transform(None)
    return bw + spur, spur


@both(0x4BC, 0x4BD)
def AbkhazianChe(g, lc):
    abk_che(g, lc)


@both(0x4BE, 0x4BF)
def AbkhazianCheTail(g, lc):
    bw, spur = abk_che(g, lc)
    g.vstem(spur + (bw - spur) / 2 + 4, tail_depth(g), -g.ov + g.H)


# ---------------------------------------------------------------------------
# Ю Я
# ---------------------------------------------------------------------------

def yu(g, lc, stem_top=None):
    top = top_of(g, lc)
    s = 0.84 if g.mono else 1.0     # as Ш: the 600 cell is tight
    ow = wd(g, lc, (590, 340, 0.6), (470, 330, 0.5))
    gap = wd(g, lc, (84, 40, 0.3), (64, 36, 0.3))
    if g.mono:
        # Tight cell: the heavy round keeps most of its extra room, but both
        # the round and the bar give back a little with weight (linear in W,
        # nil at Light) so the slanted Black still fits the 600 cell.
        ow += g.grow * 0.25 - (g.W - 22) * 0.08
        gap -= g.grow * 0.25 + (g.W - 22) * 0.05
    g.stem(0, 0, top if stem_top is None else stem_top, w=s)
    ox = g.W * s + gap
    hx, hy = g.hw * s, g.hh * s
    b, t = -g.ov + hy, top + g.ov - hy
    run = mono_run(g, b, t)
    round_loop(g, ox + hx, b, ox + ow - hx, t, k=None if lc else KR, w=s, lrun=run, rrun=run)
    y = bar_y(g) if not lc else top * 0.5
    g.bar(g.hw * s, ox + g.hw * s, y, w=s)


@both(0x42E, 0x44E)
def Yu(g, lc):
    yu(g, lc)


@both(0x42F, 0x44F)
def Ya(g, lc):
    if not lc:
        g.include("R", mirror_x(w_R(g) / 2))
        return
    bw = g.wd(420, 440, grow=0.6)
    g.transform(mirror_x(bw / 2))
    g.stem(0, 0, g.xh)
    jb = g.xh * 0.42
    ry = (g.xh - jb) / 2
    bowl_r(g, g.hw, bw - 8 - g.grow * 0.1, jb - g.hh, g.xh, rx=ry * 0.98, sv=0.06)
    r, rh = g.hw * DIAG, g.hh * DIAG
    x0 = bw * 0.5 - 16 + g.grow * 0.1
    g.line(x0, jb, bw - r, rh, w0=DIAG)
    g.transform(None)


# ---------------------------------------------------------------------------
# Ђ ђ Ћ ћ
# ---------------------------------------------------------------------------

def tshe_cap(g, hook):
    bt = g.wd(440, 400, grow=0.5)              # top bar
    xs = (120 if not g.mono else 96) + g.grow * 0.35
    xc = xs + g.hw
    span = (370 if not g.mono else 300) + g.grow * 0.5
    xr = xc + span
    g.bar(0, bt, g.cap - g.hh)
    g.stem(xs, 0, g.cap)
    t = g.cap * 0.6
    j = t - t * 0.45
    if hook:
        arch_hook(g, xc, xr, t, j)
    else:
        arch(g, xc, xr, t, 0, join_y=j)


def tshe_lc(g, hook):
    dx = 76 + g.grow * 0.35
    if g.mono:
        dx = 60 + g.grow * 0.3
    bw = g.wd(436, 400)
    g.transform(shift(dx, 0))
    g.stem(0, 0, g.asc)
    if hook:
        arch_hook(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, g.xh * 0.56)
    else:
        arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, 0)
    g.transform(None)
    g.bar(0, dx + g.W + 118, (g.xh + g.asc) / 2 + 14)


@both(0x402, 0x452)
def Dje(g, lc):
    (tshe_lc if lc else tshe_cap)(g, True)


@both(0x40B, 0x45B)
def Tshe(g, lc):
    (tshe_lc if lc else tshe_cap)(g, False)


# ---------------------------------------------------------------------------
# б в м т Ѵ Ҳ Ҭ
# ---------------------------------------------------------------------------

def be_bowl(g):
    bw = g.wd(478, 466)
    yt = g.xh + 24
    g.oval(0, -g.ov, bw, yt + g.ov)
    return bw, (yt - g.ov) / 2, yt


@both(None, 0x431)
def be(g, lc):
    """б: a round o-bowl; the neck rides up the bowl's left side (tangent at its
    widest point, so the counter stays a true round), then sweeps round in one
    wide curve into a gently rising flag that ends at the ascender."""
    bw, cy, yt = be_bowl(g)
    xl = g.hw
    xe = bw - g.hw - 8                      # flag end
    sl = 0.22
    ye = g.asc - g.hh                       # flag end on the ascender
    xm = xl + 170 + g.grow * 0.4            # where the sweep turns into the flag
    ym = ye - (xe - xm) * sl
    ya = cy + (yt - cy) * 0.35              # straight neck turns into the sweep here
    (g.pen(xl, cy)
        .l(xl, ya)
        .to(xm, ym, "u", (1, sl), k=0.6)
        .l(xe, ye)
        .end())


@glyph("uni0431.loclSRB", zone="lc")
def be_srb(g):
    """Serbian / Macedonian б: the neck rises from the right of the bowl and
    curls back to the left (δ-like)."""
    bw, cy, yt = be_bowl(g)
    xr = bw - g.hw
    (g.pen(xr, cy)
        .l(xr, yt + 10)
        .to(g.hw + 30, g.asc - g.hh, "u", (-1, 0.32), k=0.62)
        .end())


@both(None, 0x432)
def ve(g, lc):
    bw = g.wd(430, 440, grow=0.6)
    g.stem(0, 0, g.xh)
    jm = g.xh * 0.53 - g.grow * 0.08
    m = 0.88                       # lighter middle bar keeps heavy counters open (as B)
    bowl_r(g, g.hw, bw - 24 - g.grow * 0.1, jm - g.hh * m, g.xh, sv=0.04, wb=m)
    bowl_r(g, g.hw, bw, 0, jm + g.hh * m, sv=0.06, wt=m)


def em_lc(g):
    bw = g.wd(560, 480, grow=0.9)
    s = 0.86 if g.mono else 1.0
    d = 0.8 if g.mono else DIAG
    g.stem(0, 0, g.xh, w=s)
    g.stem(bw - g.W * s, 0, g.xh, w=s)
    cx = bw / 2
    vy = g.xh * 0.2 if g.mono else g.hh * d
    a = g.hw * s
    g.line(a, g.xh - g.hh * s, cx, vy, d)
    g.line(bw - a, g.xh - g.hh * s, cx, vy, d)
    return bw, s


@both(None, 0x43C)
def em(g, lc):
    em_lc(g)


@both(0x4CD, 0x4CE)
def EmTail(g, lc):
    if lc:
        bw, s = em_lc(g)
    else:
        bw = w_M(g)
        s = 0.86 if g.mono else 1.0
        g.include("M")
    curl_tail(g, bw - g.hw * s, s)
    g.anchor("top", bw / 2, top_of(g, lc))


def te(g, lc):
    top = top_of(g, lc)
    if not lc:
        bw = w_T(g)
        g.include("T")
        return bw
    bw = g.wd(470, 466, grow=0.5)
    g.bar(0, bw, top - g.hh)
    g.vstem(bw / 2, 0, top)
    return bw


@both(None, 0x442)
def te_lc(g, lc):
    te(g, lc)


@both(0x4AC, 0x4AD)
def TeTail(g, lc):
    bw = te(g, lc)
    foot_tail(g, bw / 2)
    g.anchor("top", bw / 2, top_of(g, lc))


@both(0x4B2, 0x4B3)
def HaTail(g, lc):
    if lc:
        bw = g.wd(446, 466)
        g.include("x")
        xe = bw - g.hw * 0.92
    else:
        bw = w_X(g)
        g.include("X")
        xe = bw - g.hw * DIAG
    foot_tail(g, xe)
    g.anchor("top", bw / 2, top_of(g, lc))


@both(0x474, 0x475)
def Izhitsa(g, lc):
    top = top_of(g, lc)
    bw = wd(g, lc, (600, 490, 0.8), (480, 470, 0.7))
    r, rh = g.hw * DIAG, g.hh * DIAG
    vx = bw * 0.4
    g.line(r, top - rh, vx, rh, DIAG)
    xt = bw * 0.64
    yt = top * 0.64
    dx, dy = xt - vx, yt - rh
    (g.pen(vx, rh, DIAG)
        .l(xt, yt)
        .to(xt + (bw - g.hw * 0.6 - xt) * 0.55, top - rh, (dx, dy), "r", k=0.6)
        .l(bw - g.hw * 0.6, top - rh)
        .end())


# ---------------------------------------------------------------------------
# Cyrillic breve (Й й Ў ў Ӂ ӂ Ӑ ӑ Ӗ ӗ): rounder and deeper than Latin
# ---------------------------------------------------------------------------

def breve_cy(g: G, case):
    y0 = _base(g, case) - (4 if case else 6)
    h = _h(g, case) * (0.84 if case else 0.92)
    wdt = 104 + g.grow * 0.45
    r = g.hh * MW
    xa = wdt - g.hw * MW
    (g.pen(-xa, y0 + h - r, MW)
        .to(0, y0 + r, (0.05, -1), "r", k=0.6)
        .to(xa, y0 + h - r, "r", (0.05, 1), k=0.6)
        .end())
    _top(g, case, y0 + h)


glyph("brevecomb.cy", kind="mark")(lambda g: breve_cy(g, False))
glyph("brevecomb.cy.case", kind="mark")(lambda g: breve_cy(g, True))


# ---------------------------------------------------------------------------
# Bulgarian forms (locl BGR)
# ---------------------------------------------------------------------------

@glyph("uni0434.loclBGR", zone="lc")
def de_bgr(g):
    g.include("g")


@glyph("uni043B.loclBGR", zone="lc")
def el_bgr(g):
    bw = g.wd(456, 466, grow=0.7)
    r, rh = g.hw * DIAG, g.hh * DIAG
    g.line(r, rh, bw / 2, g.xh - rh, DIAG)
    g.line(bw - r, rh, bw / 2, g.xh - rh, DIAG)


@glyph("uni0444.loclBGR", zone="lc")
def ef_bgr(g):
    ef_lc(g, 0, g.asc)


@glyph("uni0436.loclBGR", zone="lc")
def zhe_bgr(g):
    bw = g.wd(680, 520, grow=1.0)
    s = 0.84 if g.mono else 1.0
    d = 0.8 if g.mono else DIAG
    cx = bw / 2
    g.vstem(cx, 0, g.asc, w=s)
    xa = cx + g.hw * s
    karms(g, xa, bw, g.xh, 0.36, d)
    g.transform(mirror_x(cx))
    karms(g, xa, bw, g.xh, 0.36, d)
    g.transform(None)


@glyph("uni0437.loclBGR", zone="lc")
def ze_bgr(g):
    bw = g.wd(420, 436, grow=0.6)
    ze_shape(g, 0, bw, g.desc - g.ov, g.xh + g.ov, g.xh * 0.3, t_top=0.84, t_bot=0.14, narrow=30)


@glyph("uni043A.loclBGR", zone="lc")
def ka_bgr(g):
    g.include("k")


def m_turned(g):
    bw = g.wd(720, grow=1.0) if not g.mono else g.wd(0, 500)
    g.include("m", rot180(bw / 2, g.xh / 2))
    return bw


@glyph("uni0448.loclBGR", zone="lc")
def sha_bgr(g):
    m_turned(g)


@glyph("uni0449.loclBGR", zone="lc")
def shcha_bgr(g):
    bw = m_turned(g)
    s = 0.84 if g.mono else 1.0
    foot_tail(g, bw - g.hw * s, s)
    g.anchor("top", bw / 2, g.xh)


@glyph("uni044E.loclBGR", zone="lc")
def yu_bgr(g):
    yu(g, True, stem_top=g.asc)


@glyph("uni0446.loclBGR", zone="lc")
def tse_bgr(g):
    bw = g.wd(436, 456)
    g.include("u")
    foot_tail(g, bw - g.hw)
    g.anchor("top", bw / 2, g.xh)


@glyph("uni0438.loclBGR", zone="lc")
def ii_bgr(g):
    g.include("u")


@glyph("uni0439.loclBGR", zone="lc")
def iishort_bgr(g):
    bw = g.wd(436, 456)
    g.include("u")
    g.include("brevecomb.cy", shift(bw / 2, 0))
