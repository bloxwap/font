"""Hebrew script for Bloxwap Sans Hebrew / Bloxwap Mono Hebrew (pack 'hebrew').

Contemporary rounded sans Hebrew drawn from skeletons like the Latin.
Hebrew is unicase; letters sit on the baseline with height HT (between the
Latin x-height and cap height), ק and the final forms descend to HD, ל rises
to HA.  Horizontal strokes are the dominant ones in Hebrew, so they are drawn
with width factor HB (≈ stem weight) instead of the thinner Latin bar.

Niqqud are zero-width marks positioned by anchors (ufo2ft builds mark/mkmk):

    bottom / _bottom      vowels below (sheva, hataf-*, hiriq, tsere, segol,
                          patah, qamats, qubuts, qamats qatan), meteg, lower dot
    top / _top            rafe, upper dot
    dagesh / _dagesh      dagesh / mappiq / shuruq: dot *inside* the letter
    holam / _holam        holam: upper-left of the letter (centred on ו = holam male)
    holamhaser / _...     holam haser for vav (upper-left of ו)
    shindot, sindot       ש dots (upper right / upper left)

Bottom marks carry a stacking `bottom` anchor to their *left* so meteg
sits beside the vowel.

Presentation forms FB1D-FB4F are composites (base + marks by anchor) added to
composites.RECIPES; the wide letters FB21-FB28 are horizontal skeleton
stretches (weight re-applied); ﭏ is drawn.
"""
from __future__ import annotations

import unicodedata

from ..skeleton import G, glyph, derive, mirror_x, shift, scale_about, GLYPHS, _transform_stroke
from ..features import FEATURE_HOOKS
from .. import composites as _comp

PACK = "hebrew"
FAMS = ("sans", "mono")

HT = 610          # letter height (ink top)
HD = -210         # descender
HA = 760          # lamed ascender
HB = 1.14         # width factor of horizontal strokes
DIAG = 0.94       # diagonals


def heb(name, *cps, kind="base"):
    return glyph(name, *cps, kind=kind, families=FAMS, pack=PACK)


def u(cp):
    return f"uni{cp:04X}"


# ---------------------------------------------------------------------------
# metrics helpers
# ---------------------------------------------------------------------------

def hb(g):
    """Half thickness of a horizontal stroke."""
    return g.hh * HB


def yt(g):
    """Skeleton y of the top bar."""
    return HT - hb(g)


def yb(g):
    """Skeleton y of a base bar."""
    return hb(g)


def rad(g, r, k=0.45):
    return r + g.grow * k


def gapv(g):
    """Ink gap between the top bar and a detached leg (ה ק)."""
    return 74 + g.grow * 0.12


# niqqud geometry
def dn(g):
    return 0.86 * g.W + 20


def gap_below(g):
    return 50 + g.grow * 0.14


def gap_above(g):
    return 54 + g.grow * 0.14


def dot_step(g):
    """Centre distance of neighbouring niqqud dots."""
    return dn(g) + 34 + g.grow * 0.1


def mwf(g):
    return 0.92 - 0.0012 * g.grow


def set_anchors(g, bw, bottom=None, top=None, dagesh=None, holam=None, haser=None, extra=None):
    cx = bw / 2
    g.anchor("bottom", *(bottom if bottom is not None else (cx, 0)))
    g.anchor("top", *(top if top is not None else (cx, HT)))
    g.anchor("dagesh", *(dagesh if dagesh is not None else (cx, HT * 0.46)))
    hol = holam if holam is not None else (g.hw * 0.3, HT)
    g.anchor("holam", *hol)
    g.anchor("holamhaser", *(haser if haser is not None else hol))
    for k, v in (extra or {}).items():
        g.anchor(k, *v)


# ---------------------------------------------------------------------------
# shared constructions
# ---------------------------------------------------------------------------

def top_corner(g, x0, xr, y_end, R, w0=HB):
    """Top bar from skeleton x0 rightwards, rounding (radius R) into a
    vertical at skeleton xr that runs down to skeleton y_end."""
    t = yt(g)
    g.pen(x0, t, w0).l(xr - R, t, w0).h(xr, t - R, w=1.0).l(xr, y_end).end()


def flag(g, x0, xs, y_end, k=0.95):
    """ו-style head: a quarter curve from the top-left (skeleton x0) into a
    stem at xs running down to y_end."""
    t = yt(g)
    rr = (xs - x0) * k
    g.pen(x0, t, HB).h(xs, t - rr, w=1.0).l(xs, y_end).end()


def kaf_body(g, x_top, xr, x_base, R, Rb=None, hook=None):
    """כ-like: top bar, round right side, base bar going left.
    hook = (rh, y_end): start with a פ tongue hanging from the top-left."""
    t, b = yt(g), yb(g)
    Rb = R if Rb is None else Rb
    if hook is not None:
        rh, y_end = hook
        p = g.pen(x_top, y_end, 1.0).l(x_top, t - rh).v(x_top + rh, t, w=HB)
    else:
        p = g.pen(x_top, t, HB)
    p.l(xr - R, t, HB).h(xr, t - R, w=1.0).l(xr, b + Rb, 1.0).v(xr - Rb, b, w=HB).l(x_base, b, HB).end()


# ---------------------------------------------------------------------------
# letters
# ---------------------------------------------------------------------------

@heb("uni05D0", 0x05D0)
def alef(g: G):
    bw = g.wd(530, 476, 0.7)
    xl, xr = g.hw, bw - g.hw
    ax, ay = xl + 4, HT - g.hh * DIAG
    bx, by = xr, g.hh * DIAG
    g.line(ax, ay, bx, by, DIAG)

    def P(t):
        return (ax + (bx - ax) * t, ay + (by - ay) * t)
    jx, jy = P(0.46)
    (g.pen(xr - 8, HT - g.hh * DIAG, DIAG)
        .to(jx, jy, (0, -1), (-0.62, -1), k=0.55).end())
    lx, ly = P(0.54)
    (g.pen(lx, ly, DIAG)
        .to(xl + 6, g.hh * DIAG, (-0.62, -1), (0, -1), k=0.55).end())
    set_anchors(g, bw, bottom=(bw * 0.5, 0), dagesh=(bw * 0.24, HT * 0.62),
                holam=(-10, HT))


@heb("uni05D1", 0x05D1)
def bet(g: G):
    bw = g.wd(500, 470, 0.6)
    tail = 56 + g.grow * 0.25
    R = rad(g, 128)
    xs = bw - tail - g.hw
    top_corner(g, 12 + g.hw * HB, xs, yb(g), R)
    g.bar(0, bw, yb(g), w=HB)
    set_anchors(g, bw, bottom=((xs + g.hw) / 2, 0), top=(xs / 2, HT),
                dagesh=((xs - g.hw) / 2 + 12, HT * 0.5))


@heb("uni05D2", 0x05D2)
def gimel(g: G):
    bw = g.wd(330, 360, 0.75)
    xs = bw - g.hw
    flag(g, bw * 0.32 + g.hw * 0.4, xs, g.hh)
    g.line(xs, HT * 0.42, g.hw + 2, g.hh * DIAG, DIAG)
    set_anchors(g, bw, bottom=(bw * 0.5, 0), top=(xs - g.hw, HT),
                dagesh=(xs - g.hw - dn(g) / 2 - 12, HT * 0.66 - g.grow * 0.25),
                holam=(bw * 0.25, HT))


@heb("uni05D3", 0x05D3)
def dalet(g: G):
    bw = g.wd(480, 460, 0.6)
    over = 62 + g.grow * 0.25
    g.bar(0, bw, yt(g), w=HB)
    g.stem(bw - over - g.W, 0, HT)
    xs = bw - over - g.hw
    set_anchors(g, bw, bottom=(xs * 0.56, 0), top=(bw * 0.5, HT),
                dagesh=((xs - g.hw) / 2, HT * 0.46 - g.grow * 0.2))


@heb("uni05D4", 0x05D4)
def he(g: G):
    bw = g.wd(500, 470, 0.6)
    over = 58 + g.grow * 0.25
    g.bar(0, bw, yt(g), w=HB)
    g.stem(bw - over - g.W, 0, HT)
    g.stem(0, 0, HT - 2 * hb(g) - gapv(g))
    xs = bw - over - g.hw
    set_anchors(g, bw, bottom=((xs + g.hw) / 2, 0), top=(bw * 0.5, HT),
                dagesh=((xs + g.hw) / 2, HT * 0.44 - g.grow * 0.2))


@heb("uni05D5", 0x05D5)
def vav(g: G):
    bw = g.wd(176, 230, 0.9)
    xs = bw - g.hw
    flag(g, g.hw * HB, xs, g.hh)
    set_anchors(g, bw, bottom=(xs, 0), top=(xs, HT),
                dagesh=(xs - g.hw - dn(g) / 2 - 26 - g.grow * 0.1, HT * 0.46),
                holam=(xs, HT), haser=(xs - g.hw - dn(g) / 2 - 30, HT))


@heb("uni05D6", 0x05D6)
def zayin(g: G):
    bw = g.wd(270, 310, 0.8)
    g.bar(0, bw, yt(g), w=HB)
    xs = bw * 0.56
    g.vstem(xs, 0, HT)
    set_anchors(g, bw, bottom=(xs, 0), top=(xs, HT),
                dagesh=(xs - g.hw - dn(g) / 2 - 22 - g.grow * 0.1, HT * 0.44),
                holam=(g.hw * 0.4, HT))


@heb("uni05D7", 0x05D7)
def het(g: G):
    bw = g.wd(500, 470, 0.6)
    g.bar(0, bw, yt(g), w=HB)
    g.stem(0, 0, HT)
    g.stem(bw - g.W, 0, HT)
    set_anchors(g, bw, dagesh=(bw / 2, HT * 0.44 - g.grow * 0.2))


@heb("uni05D8", 0x05D8)
def tet(g: G):
    bw = g.wd(510, 470, 0.6)
    xl, xr = g.hw, bw - g.hw
    t, b = yt(g), yb(g) - g.ov
    Rb = rad(g, 150)
    r2 = rad(g, 70, 0.4)
    r3 = rad(g, 64, 0.35)
    xh = xl + r2 + r3 + 34 + g.grow * 0.3
    (g.pen(xr, HT - g.hh)
        .l(xr, b + Rb)
        .v(xr - Rb, b, w=HB)
        .l(xl + Rb, b, HB)
        .h(xl, b + Rb, w=1.0)
        .l(xl, t - r2)
        .v(xl + r2, t, w=HB)
        .l(xh - r3, t, HB)
        .h(xh, t - r3, w=1.0)
        .l(xh, HT * 0.56)
        .end())
    set_anchors(g, bw, dagesh=((xh + xr) / 2 + 10, HT * 0.46 - g.grow * 0.1))


@heb("uni05D9", 0x05D9)
def yod(g: G):
    bw = g.wd(176, 230, 0.9)
    xs = bw - g.hw
    flag(g, g.hw * HB, xs, HT - 262 + g.hh)
    set_anchors(g, bw, bottom=(bw * 0.5, 0), top=(xs - g.hw * 0.5, HT),
                dagesh=(bw * 0.5, HT - 262 - dn(g) / 2 - 40),
                holam=(-6, HT))


@heb("uni05DA", 0x05DA)
def kaf_final(g: G):
    bw = g.wd(430, 440, 0.6)
    xr = bw - g.hw
    R = rad(g, 128)
    top_corner(g, g.hw * HB, xr, HD + g.hh, R)
    cx = (xr - g.hw) / 2
    set_anchors(g, bw, bottom=(cx, HT * 0.46 + gap_below(g) + dn(g) * 0.9),
                dagesh=(cx, HT * 0.46), top=(bw * 0.5, HT))


@heb("uni05DB", 0x05DB)
def kaf(g: G):
    bw = g.wd(456, 446, 0.6)
    xr = bw - g.hw
    R = rad(g, 150)
    kaf_body(g, 10 + g.hw * HB, xr, g.hw * HB, R)
    set_anchors(g, bw, bottom=(bw * 0.5, 0),
                dagesh=((xr - g.hw) / 2 + 10, HT * 0.5))


@heb("uni05DC", 0x05DC)
def lamed(g: G):
    bw = g.wd(460, 446, 0.6)
    xl, xr = g.hw, bw - g.hw
    R = rad(g, 128)
    t = yt(g)
    g.line(xl, t, xl, HA - g.hh)
    xe = bw * 0.36
    (g.pen(xl, t, HB)
        .l(xr - R, t, HB)
        .h(xr, t - R, w=1.0)
        .l(xr, HT * 0.36)
        .to(xe, g.hh * 1.1, "d", (-1, -0.42), k=0.62)
        .end())
    set_anchors(g, bw, bottom=(bw * 0.52, 0), top=(xl, HA),
                dagesh=((xl + xr) / 2 - 10, HT * 0.52 - g.grow * 0.15),
                holam=(-dn(g) / 2 - 34, HT))


@heb("uni05DD", 0x05DD)
def mem_final(g: G):
    bw = g.wd(486, 460, 0.6)
    xl, xr = g.hw, bw - g.hw
    t, b = yt(g), yb(g)
    Rm = rad(g, 112, 0.4)     # round corners, in step with ס and the כ family
    cx = bw / 2
    (g.pen(cx, t, HB)
        .l(xr - Rm, t, HB).h(xr, t - Rm, w=1.0)
        .l(xr, b + Rm, 1.0).v(xr - Rm, b, w=HB)
        .l(xl + Rm, b, HB).h(xl, b + Rm, w=1.0)
        .l(xl, t - Rm, 1.0).v(xl + Rm, t, w=HB)
        .close())
    set_anchors(g, bw, dagesh=(cx, HT * 0.5))


@heb("uni05DE", 0x05DE)
def mem(g: G):
    bw = g.wd(530, 476, 1.0 if not g.mono else 0.6)
    xl, xr = g.hw, bw - g.hw
    R = rad(g, 130)
    lean = 34 if not g.mono else 24
    gap = 84 if not g.mono else 58
    t, b = yt(g), yb(g)
    g.line(xl + lean, g.hh, xl, t)
    xg = g.W + lean + gap + g.hw * HB
    Rh = (xr - xg) * 0.62
    (g.pen(xl, t, HB)
        .l(xr - R, t, HB).h(xr, t - R, w=1.0)
        .l(xr, b + R * 0.9, 1.0).v(xr - Rh, b, w=HB)
        .l(xg, b, HB)
        .end())
    set_anchors(g, bw, bottom=(bw * 0.52, 0),
                dagesh=((xl + lean * 0.5 + xr) / 2 + 6, HT * 0.5))


@heb("uni05DF", 0x05DF)
def nun_final(g: G):
    bw = g.wd(176, 230, 0.9)
    xs = bw - g.hw
    flag(g, g.hw * HB, xs, HD + g.hh)
    set_anchors(g, bw, bottom=(xs, HD), top=(xs, HT),
                dagesh=(xs - g.hw - dn(g) / 2 - 26 - g.grow * 0.1, HT * 0.46),
                holam=(-6, HT))


@heb("uni05E0", 0x05E0)
def nun(g: G):
    bw = g.wd(300, 330, 0.85)
    xr = bw - g.hw
    R = rad(g, 104, 0.4)
    kaf_body(g, 24 + g.hw * HB, xr, g.hw * HB, R, Rb=rad(g, 96, 0.4))
    set_anchors(g, bw, bottom=(bw * 0.5, 0),
                dagesh=((xr - g.hw) / 2 + 6, HT * 0.5))


@heb("uni05E1", 0x05E1)
def samekh(g: G):
    bw = g.wd(506, 466, 0.6)
    over = 34 + g.grow * 0.1
    xl, xr = over + g.hw, bw - g.hw
    cx = (xl + xr) / 2
    t = yt(g)
    b = yb(g) - g.ov
    Rt = rad(g, 80, 0.4)
    ym = HT * 0.5
    (g.pen(cx, t, HB)
        .l(xr - Rt, t, HB).h(xr, t - Rt, w=1.0)
        .l(xr, ym, 1.0).v(cx, b, w=HB, k=0.57)
        .h(xl, ym, w=1.0, k=0.57).l(xl, t - Rt, 1.0)
        .v(xl + Rt, t, w=HB)
        .close())
    g.bar(0, xl + Rt, t, w=HB)
    set_anchors(g, bw, bottom=(cx, 0), top=(cx, HT), dagesh=(cx, HT * 0.46))


@heb("uni05E2", 0x05E2)
def ayin(g: G):
    bw = g.wd(510, 476, 0.6)
    xr = bw - g.hw
    R = rad(g, 140)
    b = yb(g)
    (g.pen(xr, HT - g.hh)
        .l(xr, b + R)
        .v(xr - R, b, w=HB)
        .l(g.hw * HB, b, HB)
        .end())
    jx, jy = xr - R * 0.3, b + R * 0.3
    g.line(g.hw + 18, HT - g.hh * DIAG, jx, jy, DIAG)
    set_anchors(g, bw, bottom=(bw * 0.5, 0), top=(bw * 0.5, HT),
                dagesh=(bw * 0.66, HT * 0.62 - g.grow * 0.1))


@heb("uni05E3", 0x05E3)
def pe_final(g: G):
    bw = g.wd(436, 440, 0.6)
    xr = bw - g.hw
    R = rad(g, 128)
    rh = rad(g, 70, 0.4)
    t = yt(g)
    (g.pen(g.hw, HT * 0.5 + g.hh)
        .l(g.hw, t - rh)
        .v(g.hw + rh, t, w=HB)
        .l(xr - R, t, HB)
        .h(xr, t - R, w=1.0)
        .l(xr, HD + g.hh)
        .end())
    set_anchors(g, bw, bottom=(xr, HD), top=(bw * 0.5, HT),
                dagesh=((g.W + xr - g.hw) / 2 + 4, HT * 0.5 - g.grow * 0.15))


@heb("uni05E4", 0x05E4)
def pe(g: G):
    bw = g.wd(470, 450, 0.6)
    xr = bw - g.hw
    R = rad(g, 140)
    rh = rad(g, 70, 0.4)
    kaf_body(g, g.hw, xr, g.hw * HB, R, hook=(rh, HT * 0.5 + g.hh))
    set_anchors(g, bw, bottom=(bw * 0.5, 0),
                dagesh=((g.W + xr - g.hw) / 2 + 6, HT * 0.5 - g.grow * 0.15))


@heb("uni05E5", 0x05E5)
def tsadi_final(g: G):
    bw = g.wd(400, 420, 0.7)
    xl = g.hw + 8
    g.line(xl, HT - g.hh, xl, HD + g.hh)
    (g.pen(bw - g.hw - 4, HT - g.hh * DIAG, DIAG)
        .to(xl, HT * 0.36, (-0.12, -1), (-1, -0.75), k=0.6).end())
    set_anchors(g, bw, bottom=(xl, HD), top=(bw * 0.5, HT),
                dagesh=(bw * 0.56, HT * 0.24 - g.grow * 0.1),
                holam=(-6, HT))


@heb("uni05E6", 0x05E6)
def tsadi(g: G):
    bw = g.wd(480, 460, 0.6)
    xl = g.hw
    R = rad(g, 130)
    b = yb(g)
    lean = 30
    (g.pen(xl, HT - g.hh)
        .l(xl + lean * 0.35, b + R)
        .to(xl + lean * 0.35 + R, b, (lean * 0.35, -(HT - g.hh - b - R)), "r", k=0.6, w=HB)
        .l(bw - g.hw * HB, b, HB)
        .end())
    (g.pen(bw - g.hw - 6, HT - g.hh * DIAG, DIAG)
        .to(xl + 6, HT * 0.38, (-0.12, -1), (-1, -0.75), k=0.6).end())
    set_anchors(g, bw, bottom=(bw * 0.52, 0), top=(bw * 0.5, HT),
                dagesh=(bw * 0.6, HT * 0.24 - g.grow * 0.05))


@heb("uni05E7", 0x05E7)
def qof(g: G):
    bw = g.wd(486, 466, 0.6)
    xr = bw - g.hw
    R = rad(g, 130)
    top_corner(g, g.hw * HB, xr, g.hh, R)
    g.stem(0, HD, HT - 2 * hb(g) - gapv(g))
    set_anchors(g, bw, bottom=((g.W + xr) / 2 + 20, 0), top=(bw * 0.5, HT),
                dagesh=((g.W + xr) / 2 + 4, HT * 0.44 - g.grow * 0.2))


@heb("uni05E8", 0x05E8)
def resh(g: G):
    bw = g.wd(446, 446, 0.6)
    xr = bw - g.hw
    R = rad(g, 140)
    top_corner(g, g.hw * HB, xr, g.hh, R)
    set_anchors(g, bw, bottom=(bw * 0.56, 0),
                dagesh=((xr - g.hw) / 2, HT * 0.46 - g.grow * 0.2))


@heb("uni05E9", 0x05E9)
def shin(g: G):
    bw = g.wd(590, 496, 0.8)
    xl, xr = g.hw, bw - g.hw
    Rs = rad(g, 150)
    b = yb(g) - g.ov * 0.5
    lean = 26
    (g.pen(xl, HT - g.hh)
        .l(xl + lean, b + Rs)
        .to(xl + lean + Rs, b, (lean, -(HT - g.hh - b - Rs)), "r", k=0.6, w=HB)
        .l(xr - Rs, b, HB)
        .h(xr, b + Rs, w=1.0)
        .l(xr, HT - g.hh)
        .end())
    mx = bw * 0.53
    jx, jy = xl + lean + Rs * 0.34, b + Rs * 0.34
    g.line(mx, HT - g.hh * DIAG, jx, jy, DIAG)
    set_anchors(g, bw, bottom=(bw * 0.5, 0), top=(bw * 0.5, HT),
                dagesh=((mx + xr) / 2 + 4, HT * 0.5 - g.grow * 0.1),
                holam=(xl - dn(g) * 0.9 - 10, HT),
                extra={"shindot": (xr + 4, HT), "sindot": (xl - 4, HT)})


@heb("uni05EA", 0x05EA)
def tav(g: G):
    bw = g.wd(526, 476, 0.6)
    xr = bw - g.hw
    R = rad(g, 130)
    xg = 72 + g.hw + g.grow * 0.35
    top_corner(g, xg, xr, g.hh, R)
    rf = rad(g, 46, 0.2)
    b = yb(g)
    (g.pen(xg, yt(g), 1.0)
        .l(xg, b + rf)
        .v(xg - rf, b, w=HB)
        .l(g.hw * HB, b, HB)
        .end())
    set_anchors(g, bw, bottom=((xg + xr) / 2, 0), top=((xg + xr) / 2, HT),
                dagesh=((xg + xr) / 2, HT * 0.44 - g.grow * 0.2),
                holam=(xg - g.hw, HT))


# --- Yiddish digraphs, yod triangle -------------------------------------------

def _pair(g, left, right, gap):
    """Draw glyph `left` then `right` beside it (skeleton includes)."""
    g.include(left)
    lw = _ink_right(g, left)
    g.include(right, shift(lw + gap))
    return lw


def _ink_right(g, name):
    """Skeleton right edge of a letter's ink (its body width)."""
    return {"uni05D5": g.wd(176, 230, 0.9), "uni05D9": g.wd(176, 230, 0.9)}[name]


def _digraph(name, cp, left, right, mono_sx):
    def f(g: G):
        gap = 70 + g.grow * 0.3
        n0 = len(g.strokes)
        lw = _pair(g, left, right, gap)
        rw = _ink_right(g, right)
        if g.mono:
            for i in range(n0, len(g.strokes)):
                g.strokes[i] = _transform_stroke(g.strokes[i], scale_about(mono_sx, 1.0, 0, 0))
        k = mono_sx if g.mono else 1.0
        tw = (lw + gap + rw) * k
        g.anchor("bottom", tw / 2, 0)
        g.anchor("top", tw / 2, HT)
        g.anchor("holam", -6, HT)
        g.anchor("holamhaser", -6, HT)
        g.anchor("dagesh", tw / 2, HT * 0.46)
    heb(name, cp)(f)


_digraph("uni05F0", 0x05F0, "uni05D5", "uni05D5", 0.8)     # װ double vav
_digraph("uni05F1", 0x05F1, "uni05D9", "uni05D5", 0.8)     # ױ vav yod (yod on the left)
_digraph("uni05F2", 0x05F2, "uni05D9", "uni05D9", 0.8)     # ײ double yod


@heb("uni05EF", 0x05EF)
def yod_triangle(g: G):
    # three small yods in a triangle (abbreviation of the Tetragrammaton)
    s = 0.56
    yw = g.wd(176, 230, 0.9) * s
    sp = 50 + g.grow * 0.25
    for dx, dy in ((0, HT * 0.04), (yw + sp, HT * 0.04), ((yw + sp) / 2, HT * 0.48)):
        n0 = len(g.strokes)
        g.include("uni05D9", lambda p, dx=dx, dy=dy: (p[0] * s + dx, (p[1] - HT * 0.54) * s * 1.3 + HT * 0.54 * s + dy))
        for i in range(n0, len(g.strokes)):
            g.strokes[i].scale *= 0.8
    tw = yw * 2 + sp
    set_anchors(g, tw)


# --- punctuation ----------------------------------------------------------------

@heb("uni05BE", 0x05BE)
def maqaf(g: G):
    w = g.wd(300, 380, 0.5)
    g.bar(0, w, yt(g) - 6, w=HB)


@heb("uni05C0", 0x05C0)
def paseq(g: G):
    g.vstem(0, -60, HT + 70)


@heb("uni05C3", 0x05C3)
def sof_pasuq(g: G):
    d = g.W * 1.16 + 10
    g.dot(0, d / 2, d)
    g.dot(0, HT * 0.62 - d / 2, d)


def _geresh(g, x):
    L = 214 + g.grow * 0.2
    dx = 72 + g.grow * 0.1
    g.line(x + dx, HT - g.hh, x, HT - L + g.hh, 0.98, 0.84)


@heb("uni05F3", 0x05F3)
def geresh(g: G):
    _geresh(g, 0)


@heb("uni05F4", 0x05F4)
def gershayim(g: G):
    _geresh(g, 0)
    _geresh(g, 116 + g.grow * 0.85)


@heb("uni05C6", 0x05C6)
def nun_hafukha(g: G):
    bw = g.wd(300, 330, 0.85)
    g.transform(mirror_x(bw / 2))
    xr = bw - g.hw
    R = rad(g, 104, 0.4)
    kaf_body(g, 24 + g.hw * HB, xr, g.hw * HB, R, Rb=rad(g, 96, 0.4))
    g.transform(None)


# ---------------------------------------------------------------------------
# niqqud (combining marks)
# ---------------------------------------------------------------------------

def below_y(g):
    """Centre y of the first row of dots below the baseline."""
    return -gap_below(g) - dn(g) / 2


def above_y(g):
    return HT + gap_above(g) + dn(g) / 2


def _bottom_mark(g, x0, x1, y_ink_bottom):
    """Anchors for a mark below: attaches at its top centre; stacking anchor
    to the left so meteg / accents below sit beside the vowel."""
    g.anchor("_bottom", 0, 0)
    g.anchor("bottom", x0 - 30 - g.hw * mwf(g) - g.grow * 0.1, 0)


def _top_mark(g, y_ink_top):
    """Attach at HT; a further mark stacks ~26 units above this one's ink."""
    g.anchor("_top", 0, HT)
    g.anchor("top", 0, y_ink_top + 26 - gap_above(g))


def bmark(name, cp):
    def deco(fn):
        def f(g: G):
            x0, x1, y0 = fn(g)
            _bottom_mark(g, x0, x1, y0)
        heb(name, cp, kind="mark")(f)
        return fn
    return deco


def _dots(g, pts, d=None):
    d = dn(g) if d is None else d
    for x, y in pts:
        g.dot(x, y, d)


# each pattern returns (xmin, xmax, ymin) of its ink, drawn centred at x=0

def p_sheva(g, cx=0.0):
    d = dn(g)
    y1 = below_y(g)
    y2 = y1 - d - 22 - g.grow * 0.1
    _dots(g, [(cx, y1), (cx, y2)])
    return cx - d / 2, cx + d / 2, y2 - d / 2


def p_hiriq(g, cx=0.0):
    d = dn(g)
    _dots(g, [(cx, below_y(g))])
    return cx - d / 2, cx + d / 2, below_y(g) - d / 2


def p_tsere(g, cx=0.0):
    d, s = dn(g), dot_step(g) / 2
    y = below_y(g)
    _dots(g, [(cx - s, y), (cx + s, y)])
    return cx - s - d / 2, cx + s + d / 2, y - d / 2


def p_segol(g, cx=0.0):
    d, s = dn(g), dot_step(g) / 2
    y1 = below_y(g)
    y2 = y1 - dot_step(g) * 0.84
    _dots(g, [(cx - s, y1), (cx + s, y1), (cx, y2)])
    return cx - s - d / 2, cx + s + d / 2, y2 - d / 2


def _pw(g):
    return 104 + g.grow * 0.36


def p_patah(g, cx=0.0):
    w = mwf(g)
    pw = _pw(g)
    y = -gap_below(g) - g.hh * w
    g.bar(cx - pw, cx + pw, y, w=w)
    return cx - pw, cx + pw, y - g.hh * w


def p_qamats(g, cx=0.0, long=False):
    w = mwf(g)
    pw = _pw(g)
    y = -gap_below(g) - g.hh * w
    g.bar(cx - pw, cx + pw, y, w=w)
    L = (118 if not long else 196) + g.grow * 0.5
    y0 = y - g.hh * w - L
    g.vstem(cx, y0, y, w=w)
    return cx - pw, cx + pw, y0


def p_qubuts(g, cx=0.0):
    d = dn(g)
    s = dot_step(g) * 0.78
    y1 = below_y(g)
    dy = dot_step(g) * 0.62
    _dots(g, [(cx - s, y1), (cx, y1 - dy), (cx + s, y1 - 2 * dy)])
    return cx - s - d / 2, cx + s + d / 2, y1 - 2 * dy - d / 2


def _hataf(g, pattern):
    """Vowel with a sheva to its left, the pair centred on x=0."""
    d = dn(g)
    gap = 40 + g.grow * 0.2
    # measure the vowel (draw into a scratch builder)
    tmp = G(g.p, "tmp")
    vx0, vx1, _ = pattern(tmp)
    sx = vx0 - gap - d / 2
    total0, total1 = sx - d / 2, vx1
    off = -(total0 + total1) / 2
    a0, a1, ay = pattern(g, off)
    s0, s1, sy = p_sheva(g, sx + off)
    return s0, a1, min(ay, sy)


@bmark("uni05B0", 0x05B0)
def sheva(g):
    return p_sheva(g)


@bmark("uni05B1", 0x05B1)
def hataf_segol(g):
    return _hataf(g, p_segol)


@bmark("uni05B2", 0x05B2)
def hataf_patah(g):
    return _hataf(g, p_patah)


@bmark("uni05B3", 0x05B3)
def hataf_qamats(g):
    return _hataf(g, p_qamats)


@bmark("uni05B4", 0x05B4)
def hiriq(g):
    return p_hiriq(g)


@bmark("uni05B5", 0x05B5)
def tsere(g):
    return p_tsere(g)


@bmark("uni05B6", 0x05B6)
def segol(g):
    return p_segol(g)


@bmark("uni05B7", 0x05B7)
def patah(g):
    return p_patah(g)


@bmark("uni05B8", 0x05B8)
def qamats(g):
    return p_qamats(g)


@bmark("uni05BB", 0x05BB)
def qubuts(g):
    return p_qubuts(g)


@bmark("uni05C7", 0x05C7)
def qamats_qatan(g):
    return p_qamats(g, long=True)


@bmark("uni05BD", 0x05BD)
def meteg(g):
    w = mwf(g)
    L = 128 + g.grow * 0.4
    y1 = -gap_below(g)
    g.vstem(0, y1 - L, y1, w=w)
    return -g.hw * w, g.hw * w, y1 - L


@bmark("uni05C5", 0x05C5)
def lower_dot(g):
    return p_hiriq(g)


@heb("uni05B9", 0x05B9, kind="mark")
def holam(g: G):
    g.dot(0, above_y(g), dn(g))
    g.anchor("_holam", 0, HT)


@heb("uni05BA", 0x05BA, kind="mark")
def holam_haser(g: G):
    g.dot(0, above_y(g), dn(g))
    g.anchor("_holamhaser", 0, HT)


@heb("uni05BC", 0x05BC, kind="mark")
def dagesh(g: G):
    g.dot(0, HT * 0.46, dn(g) * 0.96)
    g.anchor("_dagesh", 0, HT * 0.46)


@heb("uni05C1", 0x05C1, kind="mark")
def shin_dot(g: G):
    g.dot(0, above_y(g), dn(g))
    g.anchor("_shindot", 0, HT)


@heb("uni05C2", 0x05C2, kind="mark")
def sin_dot(g: G):
    g.dot(0, above_y(g), dn(g))
    g.anchor("_sindot", 0, HT)


@heb("uni05BF", 0x05BF, kind="mark")
def rafe(g: G):
    w = mwf(g)
    pw = 88 + g.grow * 0.3
    y = HT + gap_above(g) + g.hh * w
    g.bar(-pw, pw, y, w=w)
    _top_mark(g, y + g.hh * w)


@heb("uni05C4", 0x05C4, kind="mark")
def upper_dot(g: G):
    g.dot(0, above_y(g), dn(g))
    _top_mark(g, above_y(g) + dn(g) / 2)


@heb("uniFB1E", 0xFB1E, kind="mark")
def varika(g: G):
    # Judeo-Spanish varika: a shallow arch above the letter
    w = mwf(g)
    pw = 96 + g.grow * 0.3
    y0 = HT + gap_above(g) + g.hh * w
    h = 54 + g.grow * 0.2
    (g.pen(-pw + g.hw * w, y0, w)
        .v(0, y0 + h, k=0.58)
        .h(pw - g.hw * w, y0, k=0.58)
        .end())
    _top_mark(g, y0 + h + g.hh * w)


# ---------------------------------------------------------------------------
# presentation forms FB1D-FB4F
# ---------------------------------------------------------------------------

# wide letters (FB21-FB28): horizontal stretch of the skeleton, weight re-applied
_WIDE = {0xFB21: 0x05D0, 0xFB22: 0x05D3, 0xFB23: 0x05D4, 0xFB24: 0x05DB, 0xFB25: 0x05DC,
         0xFB26: 0x05DD, 0xFB27: 0x05E8, 0xFB28: 0x05EA}
for _cp, _src in _WIDE.items():
    derive(u(_cp), _cp, src=u(_src), sx=lambda g: 1.1 if g.mono else 1.42, sy=1.0,
           families=FAMS, pack=PACK)


@heb("uniFB29", 0xFB29)
def alt_plus(g: G):
    # Hebrew alternative plus sign (drawn here so it stays in the Hebrew pack)
    g.include("plus")


@heb("uniFB4F", 0xFB4F)
def alef_lamed(g: G):
    # alef whose diagonal rises into the lamed ascender
    g.include("uni05D0")
    xl = g.hw
    ax, ay = xl + 4, HT - g.hh * DIAG
    g.line(ax, ay, ax, HA - g.hh)
    bw = g.wd(530, 476, 0.7)
    set_anchors(g, bw, top=(ax, HA))


# composites: base + marks attached by anchors
_MARK_ATTACH = {
    0x05B4: "bottom", 0x05B7: "bottom", 0x05B8: "bottom", 0x05B9: "holam",
    0x05BC: "dagesh", 0x05BF: "top", 0x05C1: "shindot", 0x05C2: "sindot",
}


def _register_presentation_forms():
    for cp in range(0xFB1D, 0xFB50):
        ch = chr(cp)
        if unicodedata.category(ch) == "Cn" or u(cp) in GLYPHS:
            continue
        dec = unicodedata.decomposition(ch)
        if not dec:
            continue
        if dec.startswith("<"):
            # <font> variants: alternative ayin, alternative plus sign
            tag, rest = dec.split(" ", 1)
            src = int(rest.split()[0], 16)
            if tag == "<font>" and len(rest.split()) == 1:
                _comp.ALIASES[cp] = u(src)
            continue
        nfd = unicodedata.normalize("NFD", ch)
        base = u(ord(nfd[0]))
        recipe = [(base, None)]
        for m in nfd[1:]:
            att = _MARK_ATTACH.get(ord(m))
            if att is None:
                recipe = None
                break
            recipe.append((u(ord(m)), att))
        if recipe:
            _comp.RECIPES[cp] = recipe
    # FB1F ײַ yiddish double yod + patah (no canonical decomposition)
    _comp.RECIPES[0xFB1F] = [("uni05F2", None), ("uni05B7", "bottom")]
    _comp.TARGET_RANGES.append((0xFB1D, 0xFB4F))


_register_presentation_forms()


# ---------------------------------------------------------------------------
# OpenType
# ---------------------------------------------------------------------------

def _features(family, outs):
    if family is None or PACK not in getattr(family, "packs", ()):
        return None
    return [("hebr", "dflt"), ("hebr", "IWR"), ("hebr", "YID"), ("hebr", "JII"), ("hebr", "LAD")], ""


FEATURE_HOOKS.append(_features)
