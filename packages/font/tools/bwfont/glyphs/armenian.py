"""Armenian companions, drawn with the same pen and heights as the Latin.

Original skeleton constructions; Latin look-alikes reuse our own drawings.
The 38 letter pairs, punctuation, dram, eternity signs and historical
ligatures are encoded. Mono ligatures occupy two cells, except alphabetic և.
"""
from __future__ import annotations

import math

from ..skeleton import G, glyph, derive, shift, soften
from ..features import FEATURE_HOOKS
from .latin_lower import arch, bowl_left, rot180, LEAD

PACK = "armenian"


def u(cp):
    return f"uni{cp:04X}"


def arm(cp, zone="lc"):
    return glyph(u(cp), cp, pack=PACK, zone=zone)


def cup(g, xl, xr, top, bottom=0, w=1):
    cx = (xl + xr) / 2
    mid = bottom + (top - bottom) * 0.42
    (g.pen(xl, top - g.hh * w, w).l(xl, mid)
        .v(cx, bottom + g.hh * w).h(xr, mid)
        .l(xr, top - g.hh * w).end())


def shoulder(g, xl, xr, top, bottom=0):
    arch(g, xl, xr, top, bottom, join_y=top * 0.54)


def stem_shoulder(g, xl, xr, top, bottom=0, y0=0, join_y=None, apex=0.54):
    """A short stem (ink bottom y0) that turns into an n-shoulder: one smooth
    stroke at full width, so the leg flows into the arch with no step where a
    stem end used to overlap the narrower arch lead."""
    join_y = top * 0.54 if join_y is None else join_y
    ty = top - g.hh
    end_y = top - (top - join_y) * 0.62
    (g.pen(xl, y0 + g.hh).l(xl, join_y)
        .v(xl + (xr - xl) * apex, ty, k=0.62, k2=0.56)
        .h(xr, end_y, k=0.62)
        .l(xr, bottom + g.hh).end())


def u_bowl(g, xl, xs, top, join=0.36):
    """Left bowl of a u-like form hanging off a stem centred on xs (skeleton);
    the left leg (skeleton xl) rises to the ink `top`.  Rides the stem like u."""
    g.transform(rot180((xl + xs) / 2, top / 2))
    arch(g, xl, xs, top + g.ov * 0.4, 0, join_y=top * (1 - join))
    g.transform(None)


# Points on the skeleton of an oval drawn with G.ovalc / G.oval, so strokes can
# leave a bowl tangentially (or start on its centre-line) instead of capping
# beside it.
def _cubic(p0, p1, p2, p3, t):
    m = 1 - t
    a, b, c, d = m * m * m, 3 * m * m * t, 3 * m * t * t, t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _cubic_d(p0, p1, p2, p3, t):
    m = 1 - t
    return (3 * m * m * (p1[0] - p0[0]) + 6 * m * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0]),
            3 * m * m * (p1[1] - p0[1]) + 6 * m * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1]))


def oval_skel(g, x0, y0, x1, y1, w=1.0):
    """Skeleton box of g.oval(x0, y0, x1, y1, w=w)."""
    return (x0 + g.hw * w, y0 + g.hh * w, x1 - g.hw * w, y1 - g.hh * w)


def oval_quarter(g, box, quad, k=None):
    """Control points of one quarter of G.ovalc(*box, k): 'tl' 'bl' 'br' 'tr'."""
    x0, y0, x1, y1 = box
    k = soften(g.k if k is None else k)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if quad == "tl":
        return ((cx, y1), (cx + (x0 - cx) * k, y1), (x0, cy + (y1 - cy) * k), (x0, cy))
    if quad == "bl":
        return ((x0, cy), (x0, cy + (y0 - cy) * k), (cx + (x0 - cx) * k, y0), (cx, y0))
    if quad == "br":
        return ((cx, y0), (cx + (x1 - cx) * k, y0), (x1, cy + (y0 - cy) * k), (x1, cy))
    return ((x1, cy), (x1, cy + (y1 - cy) * k), (cx + (x1 - cx) * k, y1), (cx, y1))


def _root(f, n=240):
    prev = f(0.0)
    for i in range(1, n + 1):
        t = i / n
        v = f(t)
        if (v > 0) != (prev > 0):
            lo, hi = t - 1.0 / n, t
            for _ in range(40):
                mid = (lo + hi) / 2
                if (f(mid) > 0) == (prev > 0):
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2
        prev = v
    return 0.5


def oval_touch(g, box, quad, T, k=None):
    """Point on the quarter where a straight line from T touches the oval."""
    q = oval_quarter(g, box, quad, k)

    def f(t):
        P, d = _cubic(*q, t), _cubic_d(*q, t)
        return (T[0] - P[0]) * d[1] - (T[1] - P[1]) * d[0]
    return _cubic(*q, _root(f))


def oval_cross(g, box, quad, A, B, k=None):
    """Point where the line A-B crosses the quarter's centre-line."""
    return cross(oval_quarter(g, box, quad, k), A, B)


def cross(q, A, B):
    """Point where the line A-B crosses the cubic q (a skeleton segment)."""
    dx, dy = B[0] - A[0], B[1] - A[1]

    def f(t):
        P = _cubic(*q, t)
        return (P[0] - A[0]) * dy - (P[1] - A[1]) * dx
    return _cubic(*q, _root(f))


def qv(g, P0, P1, k=None):
    """Control points of pen .v(P1) from P0 (also .to(P1, 'u'/'d', 'l'/'r'))."""
    k = soften(g.k if k is None else k)
    return (P0, (P0[0], P0[1] + (P1[1] - P0[1]) * k),
            (P1[0] + (P0[0] - P1[0]) * k, P1[1]), P1)


def lower_bowl(g, xs, xr, top, xl, yl, y_end=None):
    """Right-hand bowl under a stem's loop (Ֆ ֆ): springs from the stem centred
    on xs by riding it (like an n shoulder), so the counter has a round corner
    there; rounds down the right side (skeleton xr), passes under the stem on
    the baseline and turns up into a terminal at (xl, yl).  top: ink top."""
    ty = top - g.hh
    j = top * 0.56
    lead = (top - j) * 0.24
    ym = (ty + g.hh) / 2 if y_end is None else y_end
    (g.pen(xs, j - lead, LEAD).l(xs, j, 1.0)
        .v(xs + (xr - xs) * 0.5, ty, k=0.62, k2=0.56)
        .h(xr, ym, k=0.6).v(xs, g.hh, k=0.6)
        .h(xl, yl).end())


def hook(g, x, y0, y1, right, w=1):
    r = min(110 + g.grow * 0.2, (right - x) * 0.65)
    (g.pen(x, y1 - g.hh * w, w).l(x, y0 + g.hh * w + r)
        .v(x + r, y0 + g.hh * w).l(right, y0 + g.hh * w).end())


def _alias(cp, src, **kw):
    derive(u(cp), cp, src=src, pack=PACK,
           zone="uc" if cp < 0x0557 else "lc", **kw)


# Capitals. Armenian capitals share the 720-unit Latin cap height.
@arm(0x0531, "uc")
def ayb(g):
    bw = g.wd(620, 490, 0.75)
    xm = bw * 0.72
    # u-like bowl and the hook both ride a full middle stem (no arch springing
    # from the bowl's curve, which left a lobe under it)
    g.vstem(xm, 0, g.cap)
    u_bowl(g, g.hw, xm, g.cap)
    shoulder(g, xm, bw - g.hw, g.cap * 0.38)


@arm(0x0532, "uc")
def ben(g):
    bw = g.wd(500, 460)
    g.stem(0, 0, g.cap)
    shoulder(g, g.hw, bw - g.hw, g.cap, g.cap * 0.55)
    g.bar(0, bw, g.cap * 0.46)


@arm(0x0533, "uc")
def gim(g):
    bw = g.wd(550, 470)
    xr = bw - g.hw
    bowl_left(g, xr, 0, g.cap * 0.34, g.cap)
    g.vstem(xr, 0, g.cap * 0.7)
    g.bar(bw * 0.46, bw + 40, g.cap * 0.32)


@arm(0x0534, "uc")
def da(g):
    bw = g.wd(520, 470)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap)
    g.bar(bw * 0.53, bw + 45, g.cap * 0.32)


@arm(0x0535, "uc")
def ech(g):
    bw = g.wd(480, 450)
    cup(g, g.hw, bw - g.hw, g.cap * 0.56)
    g.stem(0, g.cap * 0.34, g.cap)
    g.bar(0, bw, g.cap * 0.63)


@arm(0x0536, "uc")
def za(g):
    bw = g.wd(520, 470)
    y0, y1 = g.cap * 0.32, g.cap + g.ov
    g.oval(0, y0, bw, y1)
    # the right side leaves the bowl at its widest point, tangent, and turns
    # round into the base stroke
    r = bw * 0.3
    (g.pen(bw - g.hw, (y0 + y1) / 2).l(bw - g.hw, g.hh + r)
        .v(bw - g.hw - r, g.hh).l(g.hw, g.hh).end())


@arm(0x0537, "uc")
def eh(g):
    bw = g.wd(440, 440)
    g.stem(0, 0, g.cap)
    g.bar(0, bw, g.cap * 0.66)
    shoulder(g, g.hw, bw - g.hw, g.cap * 0.42)


@arm(0x0538, "uc")
def et(g):
    bw = g.wd(500, 470)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap, g.cap * 0.6)
    g.bar(0, bw, g.hh)


@arm(0x0539, "uc")
def to(g):
    bw = g.wd(570, 480)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap, g.cap * 0.46)
    g.oval(bw * 0.32, g.cap * 0.17, bw * 0.88, g.cap * 0.67, w=0.88)
    g.bar(bw * 0.38, bw + 35, g.cap * 0.52)


@arm(0x053A, "uc")
def zhe(g):
    bw = g.wd(520, 470)
    g.oval(0, -g.ov, bw, g.cap * 0.58)
    g.vstem(bw - g.hw, g.cap * 0.28, g.cap)
    g.bar(bw * 0.55, bw + 45, g.cap * 0.63)


@arm(0x053B, "uc")
def ini(g):
    bw = g.wd(500, 470)
    g.stem(0, 0, g.cap)
    shoulder(g, g.hw, bw - g.hw, g.cap * 0.66, g.cap * 0.2)


_alias(0x053C, "L")


@arm(0x053D, "uc")
def xeh(g):
    bw = g.wd(650, 490, 0.8)
    g.stem(0, 0, g.cap)
    cup(g, bw * 0.35, bw - g.hw, g.cap * 0.72, g.cap * 0.32, w=0.9 if g.mono else 1)
    g.vstem(bw * 0.35, g.cap * 0.32, g.cap)


@arm(0x053E, "uc")
def ca(g):
    bw = g.wd(530, 470)
    g.oval(0, -g.ov, bw, g.cap * 0.72)
    (g.pen(g.hw, g.cap * 0.37).v(bw * 0.45, g.cap - g.hh)
        .to(bw - g.hw, g.cap * 0.86, "r", (0.6, -1)).end())


@arm(0x053F, "uc")
def ken(g):
    bw = g.wd(560, 480)
    cup(g, g.hw, bw - g.hw, g.cap * 0.72, g.cap * 0.25)
    g.stem(0, g.cap * 0.3, g.cap)
    g.vstem(bw - g.hw, 0, g.cap * 0.76)


@arm(0x0540, "uc")
def ho(g):
    bw = g.wd(460, 450)
    (g.pen(bw - g.hw, g.cap * 0.81).v(bw * 0.55, g.cap - g.hh)
        .h(g.hw, g.cap * 0.67).l(g.hw, g.cap * 0.32).end())
    g.bar(0, bw, g.cap * 0.32)
    # the shoulder's leg is full width and straight up to the bar, which hides
    # the turn: the left edge runs clean from the hook to the heel
    stem_shoulder(g, g.hw, bw - g.hw, g.cap * 0.44, y0=g.cap * 0.14,
                  join_y=g.cap * 0.32 - g.hh)


@arm(0x0541, "uc")
def ja(g):
    bw = g.wd(510, 460)
    y0, y1 = g.cap * 0.4, g.cap
    g.oval(0, y0, bw, y1)
    # leaves the bowl tangent at its widest point; the foot curls back in on
    # itself (no crossing knot to clot at heavy weights)
    yb = g.cap * 0.36 - g.hh * 0.3
    (g.pen(bw - g.hw, (y0 + y1) / 2).l(bw - g.hw, g.cap * 0.22)
        .v(bw * 0.5, g.hh).h(g.hw, g.cap * 0.18)
        .v(bw * 0.42, yb).end())


@arm(0x0542, "uc")
def ghad(g):
    bw = g.wd(520, 470)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap, y0=g.cap * 0.42)
    g.bar(bw * 0.56, bw + 48, g.hh)


@arm(0x0543, "uc")
def cheh(g):
    bw = g.wd(540, 470)
    box = oval_skel(g, 0, -g.ov, bw, g.cap * 0.7)
    g.ovalc(*box)
    P0, P1 = (g.hw, (box[1] + box[3]) / 2), (bw * 0.45, g.cap - g.hh)
    g.pen(*P0).v(*P1).h(bw - g.hw, g.cap * 0.8).end()
    # the diagonal runs from the arch's centre-line to the bowl's, so both its
    # round ends are buried in strokes (no knobs in the counters)
    A, B = (bw * 0.37, g.cap * 0.74), (bw - g.hw, g.hh)
    g.line(*cross(qv(g, P0, P1), A, B), *oval_cross(g, box, "br", A, B), 0.92)


_alias(0x0544, "U")
_alias(0x0545, "three.pnum")


@arm(0x0546, "uc")
def now(g):
    bw = g.wd(510, 470)
    cup(g, g.hw, bw - g.hw, g.cap * 0.63)
    (g.pen(g.hw, g.cap * 0.55).l(g.hw, g.cap * 0.8)
        .v(bw * 0.26, g.cap - g.hh).to(bw * 0.55, g.cap * 0.85, "r", "r").end())


@arm(0x0547, "uc")
def sha(g):
    bw = g.wd(530, 470)
    (g.pen(bw - g.hw, g.cap * 0.82).to(bw * 0.5, g.cap - g.hh, "l", "l")
        .h(g.hw, g.cap * 0.48).v(bw * 0.48, g.hh)
        .h(bw - g.hw, g.cap * 0.29).end())


@arm(0x0548, "uc")
def vo(g):
    bw = g.wd(530, 470)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap)


@arm(0x0549, "uc")
def cha(g):
    bw = g.wd(490, 460)
    (g.pen(g.hw, g.cap * 0.76).v(bw * 0.48, g.cap - g.hh)
        .h(bw - g.hw, g.cap * 0.66).v(bw * 0.65, g.cap * 0.35)
        .to(g.hw, g.hh, (-1, -1), "l").end())
    g.line(bw * 0.32, g.cap * 0.22, bw - g.hw, g.hh, 0.92)


@arm(0x054A, "uc")
def peh(g):
    vo(g)
    bw = g.wd(530, 470)
    g.vstem(bw * 0.5, g.cap * 0.24, g.cap)


@arm(0x054B, "uc")
def jheh(g):
    bw = g.wd(540, 470)
    box = oval_skel(g, 0, g.cap * 0.25, bw, g.cap)
    g.ovalc(*box)
    # the diagonal leaves the bowl tangentially (like a 2)
    T = (g.hw, g.hh)
    g.line(*oval_touch(g, box, "br", T), *T, 0.92)
    g.bar(0, bw, g.hh)
    g.vstem(bw - g.hw, 0, g.cap * 0.25)


@arm(0x054C, "uc")
def ra(g):
    vo(g)
    bw = g.wd(530, 470)
    stem_shoulder(g, bw * 0.62, bw - g.hw, g.cap * 0.46, y0=g.cap * 0.1,
                  join_y=g.cap * 0.25)


_alias(0x054D, "U")


@arm(0x054E, "uc")
def vew(g):
    bw = g.wd(560, 480)
    cup(g, g.hw, bw - g.hw, g.cap * 0.72, g.cap * 0.22)
    g.vstem(bw - g.hw, 0, g.cap)
    g.bar(bw * 0.56, bw + 45, g.hh)


_alias(0x054F, "S")


@arm(0x0550, "uc")
def reh(g):
    bw = g.wd(510, 470)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap, g.cap * 0.57)


@arm(0x0551, "uc")
def co(g):
    bw = g.wd(500, 460)
    g.include("three.pnum")
    g.bar(0, bw, g.cap * 0.29)


@arm(0x0552, "uc")
def yiwn(g):
    bw = g.wd(500, 460)
    g.stem(0, 0, g.cap)
    shoulder(g, g.hw, bw - g.hw, g.cap * 0.67, g.cap * 0.26)


@arm(0x0553, "uc")
def piwr(g):
    bw = g.wd(620, 490)
    g.oval(0, g.cap * 0.2, bw, g.cap * 0.82, w=0.9 if g.mono else 1)
    g.vstem(bw * 0.5, 0, g.cap)


@arm(0x0554, "uc")
def keh(g):
    bw = g.wd(490, 460)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap, g.cap * 0.55)
    g.bar(0, bw, g.cap * 0.36)
    g.bar(0, bw * 0.88, g.cap * 0.21)


_alias(0x0555, "O")


@arm(0x0556, "uc")
def feh(g):
    bw = g.wd(530, 470)
    g.vstem(bw * 0.5, 0, g.cap)
    bowl_left(g, bw * 0.5, 0, g.cap * 0.47, g.cap)
    lower_bowl(g, bw * 0.5, bw - g.hw, g.cap * 0.53 + g.hh, g.hw, g.cap * 0.17)


# Lowercase shares Latin x-height; ascenders/descenders use 760/-210.
@arm(0x0561)
def ayb_small(g):
    bw = g.wd(690, 490, 0.85)
    w = 0.88 if g.mono else 1
    cup(g, g.hw * w, bw * 0.5, g.xh, w=w)
    cup(g, bw * 0.5, bw - g.hw * w, g.xh, w=w)


@arm(0x0562)
def ben_small(g):
    bw = g.wd(430, 450)
    g.stem(0, g.desc, g.xh)
    shoulder(g, g.hw, bw - g.hw, g.xh, g.xh * 0.68)
    g.bar(0, bw, g.xh * 0.23)


_alias(0x0563, "q")


@arm(0x0564)
def da_small(g):
    bw = g.wd(436, 456)
    g.stem(0, 0, g.xh)
    shoulder(g, g.hw, bw - g.hw, g.xh, g.desc)
    g.bar(bw * 0.58, bw + 44, g.desc + g.hh)


@arm(0x0565)
def ech_small(g):
    bw = g.wd(440, 456)
    cup(g, g.hw, bw - g.hw, g.xh * 0.48)
    g.stem(0, g.xh * 0.3, g.asc)
    g.bar(0, bw, g.xh * 0.62)


@arm(0x0566)
def za_small(g):
    bw = g.wd(478, 476)
    g.include("q")
    g.bar(bw * 0.55, bw + 45, g.desc + g.hh)


@arm(0x0567)
def eh_small(g):
    bw = g.wd(370, 400)
    hook(g, g.hw, g.desc, g.asc, bw - g.hw)
    g.bar(0, bw, g.xh * 0.63)


@arm(0x0568)
def et_small(g):
    bw = g.wd(436, 456)
    g.stem(0, g.desc, g.xh)
    shoulder(g, g.hw, bw - g.hw, g.xh, g.xh * 0.35)
    g.bar(0, bw, g.desc + g.hh)


@arm(0x0569)
def to_small(g):
    bw = g.wd(480, 460)
    stem_shoulder(g, g.hw, bw - g.hw, g.xh, g.xh * 0.46, y0=g.desc)
    g.oval(bw * 0.28, g.xh * 0.13, bw * 0.86, g.xh * 0.67, w=0.88)
    g.bar(bw * 0.4, bw + 30, g.xh * 0.53)


@arm(0x056A)
def zhe_small(g):
    bw = g.wd(478, 476)
    g.include("d")
    g.bar(bw * 0.54, bw + 45, g.xh * 0.66)


@arm(0x056B)
def ini_small(g):
    bw = g.wd(436, 456)
    g.stem(0, g.desc, g.asc)
    shoulder(g, g.hw, bw - g.hw, g.xh, g.xh * 0.18)


@arm(0x056C)
def liwn_small(g):
    bw = g.wd(280, 350)
    hook(g, g.hw, g.desc, g.xh, bw - g.hw)


@arm(0x056D)
def xeh_small(g):
    bw = g.wd(650, 490, 0.8)
    g.stem(0, g.desc, g.asc)
    cup(g, bw * 0.35, bw - g.hw, g.xh, w=0.9 if g.mono else 1)
    g.vstem(bw * 0.35, 0, g.asc)


@arm(0x056E)
def ca_small(g):
    bw = g.wd(478, 476)
    box = oval_skel(g, 0, -g.ov, bw, g.xh + g.ov)
    g.ovalc(*box)
    # the ascender starts on the bowl's centre-line (no knob in the counter)
    A, T = (bw * 0.62, g.xh * 0.6), (g.hw, g.asc - g.hh)
    g.line(*oval_cross(g, box, "tl", A, T), *T, 0.92)


@arm(0x056F)
def ken_small(g):
    bw = g.wd(436, 456)
    cup(g, g.hw, bw - g.hw, g.xh)
    g.stem(0, g.xh * 0.42, g.asc)
    g.vstem(bw - g.hw, g.desc, g.xh)


_alias(0x0570, "h")


@arm(0x0571)
def ja_small(g):
    bw = g.wd(470, 460)
    box = oval_skel(g, 0, -g.ov, bw, g.xh * 0.78)
    g.ovalc(*box)
    P0, P1 = (g.hw, (box[1] + box[3]) / 2), (bw - g.hw, g.xh - g.hh)
    g.pen(*P0).v(*P1).end()
    A, B = (bw * 0.37, g.xh * 0.67), (bw - g.hw, g.hh)
    g.line(*cross(qv(g, P0, P1), A, B), *oval_cross(g, box, "br", A, B), 0.92)


@arm(0x0572)
def ghad_small(g):
    da_small(g)
    # The left stem stops above the baseline; distinguish ղ from դ.
    # Replace the first (vertical) stroke with an inset stem.
    g.strokes.pop(0)
    g.stem(0, g.xh * 0.2, g.xh)


@arm(0x0573)
def cheh_small(g):
    bw = g.wd(478, 476)
    g.oval(0, -g.ov, bw, g.xh + g.ov)
    (g.pen(g.hw, g.xh * 0.5).l(g.hw, g.asc * 0.8)
        .v(bw * 0.45, g.asc - g.hh).h(bw - g.hw, g.asc * 0.82).end())
    g.bar(0, bw, g.xh * 0.6)


@arm(0x0574)
def men_small(g):
    bw = g.wd(436, 456)
    cup(g, g.hw, bw - g.hw, g.xh)
    (g.pen(bw - g.hw, g.xh * 0.76).l(bw - g.hw, g.asc * 0.85)
        .v(bw * 0.66, g.asc - g.hh).h(bw * 0.5, g.asc * 0.83).end())


@arm(0x0575)
def yi_small(g):
    bw = g.wd(230, 320)
    (g.pen(bw - g.hw, g.xh - g.hh).l(bw - g.hw, g.desc * 0.35)
        .v(g.hw, g.desc + g.hh).end())


@arm(0x0576)
def now_small(g):
    bw = g.wd(436, 456)
    cup(g, g.hw, bw - g.hw, g.xh)
    (g.pen(g.hw, g.xh * 0.75).l(g.hw, g.asc * 0.82)
        .v(bw * 0.28, g.asc - g.hh).end())


_alias(0x0577, "two.pnum", sy=lambda g: (g.xh - g.H) / (g.cap - g.H),
       dy=lambda g: g.hh * (1 - (g.xh - g.H) / (g.cap - g.H)))
_alias(0x0578, "n")


@arm(0x0579)
def cha_small(g):
    bw = g.wd(380, 420)
    (g.pen(bw * 0.34, g.xh - g.hh).h(bw - g.hw, g.xh * 0.7)
        .to(g.hw, g.desc + g.hh, (-0.4, -1), "l").end())
    g.bar(0, bw, g.desc + g.hh)


@arm(0x057A)
def peh_small(g):
    ayb_small(g)
    bw = g.wd(690, 490, 0.85)
    g.vstem(bw - g.hw, g.desc, g.xh)


@arm(0x057B)
def jheh_small(g):
    bw = g.wd(450, 456)
    box = oval_skel(g, 0, g.xh * 0.24, bw, g.xh + g.ov)
    g.ovalc(*box)
    T = (g.hw, g.hh)
    g.line(*oval_touch(g, box, "br", T), *T, 0.92)
    g.bar(0, bw, g.hh)


@arm(0x057C)
def ra_small(g):
    bw = g.wd(436, 456)
    g.include("n")
    g.bar(bw * 0.55, bw + 48, g.hh)


_alias(0x057D, "u")


@arm(0x057E)
def vew_small(g):
    bw = g.wd(436, 456)
    cup(g, g.hw, bw - g.hw, g.xh)
    g.vstem(bw - g.hw, g.desc, g.asc)
    g.bar(bw * 0.54, bw + 48, g.desc + g.hh)


@arm(0x057F)
def tiwn_small(g):
    bw = g.wd(650, 490, 0.8)
    w = 0.88 if g.mono else 1
    # u + n sharing a middle stem: both curves ride it
    xm = bw * 0.5
    g.vstem(xm, 0, g.xh, w=w)
    g.transform(rot180((g.hw * w + xm) / 2, g.xh / 2))
    arch(g, g.hw * w, xm, g.xh + g.ov * 0.4, 0, w=w)
    g.transform(None)
    arch(g, xm, bw - g.hw * w, g.xh + g.ov * 0.4, 0, w=w)


@arm(0x0580)
def reh_small(g):
    bw = g.wd(430, 450)
    g.stem(0, g.desc, g.xh)
    shoulder(g, g.hw, bw - g.hw, g.xh, g.xh * 0.56)


_alias(0x0581, "g")


@arm(0x0582)
def yiwn_small(g):
    bw = g.wd(280, 350)
    hook(g, g.hw, 0, g.xh, bw - g.hw)


@arm(0x0583)
def piwr_small(g):
    bw = g.wd(650, 490, 0.8)
    cup(g, g.hw, bw * 0.44, g.xh, w=0.9 if g.mono else 1)
    g.vstem(bw * 0.44, g.desc, g.asc)
    shoulder(g, bw * 0.44, bw - g.hw, g.xh)


@arm(0x0584)
def keh_small(g):
    bw = g.wd(478, 476)
    g.include("p")
    g.bar(-45, bw * 0.68, g.desc * 0.25)


_alias(0x0585, "o")


@arm(0x0586)
def feh_small(g):
    bw = g.wd(500, 470)
    g.vstem(bw * 0.5, g.desc, g.asc)
    bowl_left(g, bw * 0.5, 0, g.xh * 0.4, g.asc)
    lower_bowl(g, bw * 0.5, bw - g.hw, g.xh * 0.5 + g.hh, g.hw, g.xh * 0.14)


# Turned ayb for phonetic notation, with the same rounded strokes.
_alias(0x0560, u(0x0561), sx=-1, sy=-1,
       dx=lambda g: g.wd(690, 490, 0.85), dy=lambda g: g.xh)


@arm(0x0588)
def yi_with_stroke(g):
    yi_small(g)
    bw = g.wd(230, 320)
    g.bar(-40, bw + 45, g.xh * 0.43, w=0.8)


# Dialectology modifiers: superscript eh, ini and yi (Unicode Armenian chart).
for _cp, _src in ((0x0558, 0x0567), (0x058B, 0x056B), (0x058C, 0x0575)):
    _alias(_cp, u(_src), sx=0.66, sy=0.54, dy=390, wscale=0.78)


@arm(0x0587)
def ew(g):
    bw = g.wd(630, 490, 0.8)
    mid = bw * 0.53
    cup(g, g.hw, mid, g.xh * 0.55, w=0.9 if g.mono else 1)
    g.stem(0, g.xh * 0.3, g.asc)
    hook(g, mid, 0, g.xh, bw - g.hw, w=0.9 if g.mono else 1)


# Punctuation is spacing (Armenian intonation signs follow the stressed vowel).
_alias(0x0589, "colon")


@arm(0x058A)
def hyphen(g):
    bw = g.wd(250, 350)
    (g.pen(g.hw, g.xh * 0.58).v(bw * 0.32, g.xh * 0.42)
        .l(bw - g.hw, g.xh * 0.42).end())


@arm(0x0559)
def left_half_ring(g):
    bw = g.wd(160, 180)
    (g.pen(bw - g.hw * 0.7, g.cap, 0.7).h(g.hw * 0.7, g.cap - 90)
        .v(bw - g.hw * 0.7, g.cap - 180).end())


_alias(0x055A, "quoteright")
_alias(0x055B, "acutecomb", kind="base")
_alias(0x055D, "gravecomb", kind="base")


@arm(0x055C)
def exclamation(g):
    g.line(0, g.cap - 70, 65 + g.grow * 0.15, g.cap + 120, 0.8)


@arm(0x055E)
def question(g):
    bw = g.wd(240, 260)
    (g.pen(g.hw * 0.8, g.cap - 85, 0.8).v(bw * 0.5, g.cap + 80)
        .h(bw - g.hw * 0.8, g.cap + 5).v(bw * 0.5, g.cap - 85).end())


@arm(0x055F)
def abbreviation(g):
    bw = g.wd(280, 320)
    (g.pen(g.hw, g.cap + 50).l(g.hw, g.cap)
        .v(bw * 0.3, g.cap - 55).l(bw - g.hw, g.cap - 55).end())


@arm(0x058F)
def dram(g):
    bw = g.wd(500, 470)
    stem_shoulder(g, g.hw, bw - g.hw, g.cap, y0=g.cap * 0.48, join_y=g.cap * 0.62)
    for y in (g.cap * 0.25, g.cap * 0.4):
        g.bar(bw * 0.44, bw + 40, y)


def _eternity(cp, sign):
    @arm(cp)
    def f(g):
        bw = g.wd(640, 490, 0.5)
        cx, cy, radius = bw / 2, g.xh / 2, min(bw, g.xh) * 0.45
        for i in range(8):
            theta = i * math.pi / 4
            def tx(p, t=theta):
                x, y = p
                return (cx + x * math.cos(t) - y * math.sin(t),
                        cy + x * math.sin(t) + y * math.cos(t))
            g.transform(tx)
            (g.pen(radius, 0, 0.64).c((radius, sign * radius * 0.5),
                (radius * 0.1, sign * radius * 0.62), (0, 0)).end())
        g.transform(None)


_eternity(0x058D, -1)
_eternity(0x058E, 1)


# Historical ligatures: encode the presentation form and expose optional liga.
# Drawing the constituents into a scratch builder lets spacing follow the ink
# at every weight without depending on compiled outlines.
LIGATURES = {0xFB13: (0x0574, 0x0576), 0xFB14: (0x0574, 0x0565),
             0xFB15: (0x0574, 0x056B), 0xFB16: (0x057E, 0x0576),
             0xFB17: (0x0574, 0x056D)}


def _ligature(cp, pair):
    def f(g):
        first = g.include(u(pair[0]))
        xs = [p[0] for st in first.strokes for sg in st.segs for p in sg.pts]
        dx = max(xs) + g.W + 60 + g.grow * 0.15
        g.include(u(pair[1]), shift(600 if g.mono else dx))
        if g.mono:
            g.advance = 1200
    # Glyph-name convention generates the liga substitution automatically.
    name = "_".join(u(c) for c in pair)
    glyph(name, cp, pack=PACK, zone="lc")(f)


for _cp, _pair in LIGATURES.items():
    _ligature(_cp, _pair)


def _features(family, outs):
    if family is None or PACK not in family.packs:
        return None
    return [("armn", "dflt"), ("armn", "HYE"), ("armn", "HYE0")], ""


FEATURE_HOOKS.append(_features)
