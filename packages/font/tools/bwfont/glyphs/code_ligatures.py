"""Mono programming ligatures (`a_b.code` -> Mono `calt`).

Each ligature of N characters occupies N cells (advance 600*N).  Shapes are
drawn self-contained in absolute cell coordinates (cell k spans
600k..600k+600) and pinned with lsb/rsb so the ink stays where the separate
characters would sit.  Arrows / operators sit on the math axis.
"""
from __future__ import annotations

import math

from ..skeleton import glyph, G
from .arrows_shapes import AX, frame, push, pop, wings, outline_poly, ww

CELL = 600.0


def lig(name):
    return glyph(name, zone="fig", families=("mono",))


def place(g: G, n, x0, x1):
    """Advance n cells; keep the ink (designed to span x0..x1) in place."""
    g.advance = CELL * n
    g.lsb = x0
    g.rsb = CELL * n - x1


# ---------------------------------------------------------------------------
# shared metrics
# ---------------------------------------------------------------------------

MARGIN = 92.0          # ink margin from the outer cell edges for arrows / bars


def eq_d(g: G):
    """Half distance between the two bars of '=' (matches `equal`)."""
    return 94 + g.grow * 0.4


def tri_d(g: G):
    """Distance between the bars of a triple-bar (===)."""
    return 112 + g.W * 0.5


def head_l(g: G):
    return 214 + g.W * 0.62


HEAD_ANG = 41.0
HEAD_ANG2 = 47.0


def bars(g: G, x0, x1, ys):
    for y in ys:
        g.bar(x0, x1, y)


def arrow_code(g: G, n, left=False, right=True, double=False):
    """Long single (->) or double (=>) arrow over n cells, ink MARGIN..n*600-MARGIN."""
    x0, x1 = MARGIN, CELL * n - MARGIN
    tipr = g.hw * ww(g)
    s0 = x0 + (tipr if left else g.hw)
    s1 = x1 - (tipr if right else g.hw)
    old = push(g, frame(0, AX, 1, 0))
    if double:
        d = eq_d(g)
        L = head_l(g) * 1.08
        cut = d / math.tan(math.radians(HEAD_ANG2)) + g.hw * 0.45
        a = s0 + (cut if left else 0)
        b = s1 - (cut if right else 0)
        g.line(a, d, b, d)
        g.line(a, -d, b, -d)
        if right:
            wings(g, s1, L, HEAD_ANG2, 1)
        if left:
            wings(g, s0, L, HEAD_ANG2, -1)
    else:
        L = head_l(g)
        a = s0 + (g.hw if left else 0)
        b = s1 - (g.hw if right else 0)
        g.line(a, 0, b, 0)
        if right:
            wings(g, s1, L, HEAD_ANG, 1)
        if left:
            wings(g, s0, L, HEAD_ANG, -1)
    pop(g, old)
    place(g, n, x0, x1)


# ---------------------------------------------------------------------------
# arrows
# ---------------------------------------------------------------------------

@lig("hyphen_greater.code")
def hyphen_greater(g: G):            # ->
    arrow_code(g, 2)


@lig("less_hyphen.code")
def less_hyphen(g: G):               # <-
    arrow_code(g, 2, left=True, right=False)


@lig("hyphen_hyphen_greater.code")
def hyphen_hyphen_greater(g: G):     # -->
    arrow_code(g, 3)


@lig("less_hyphen_hyphen.code")
def less_hyphen_hyphen(g: G):        # <--
    arrow_code(g, 3, left=True, right=False)


@lig("less_hyphen_greater.code")
def less_hyphen_greater(g: G):       # <->
    arrow_code(g, 3, left=True, right=True)


@lig("equal_greater.code")
def equal_greater(g: G):             # =>
    arrow_code(g, 2, double=True)


@lig("less_equal_greater.code")
def less_equal_greater(g: G):        # <=>
    arrow_code(g, 3, left=True, right=True, double=True)


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------

def leq(g: G, flip=False):
    """Joined <= : wide chevron over a bar (≤), two cells."""
    x0, x1 = MARGIN + 60, 2 * CELL - MARGIN - 60
    # vertical geometry follows the single ≤ (lessequal) sign
    by = AX - 236 - g.grow * 0.1               # bar centre
    half_ink = 172 + g.grow * 0.05
    cy = by + g.hh + 70 + g.grow * 0.5 + half_ink
    half = half_ink - g.hh * ww(g)             # skeleton half-height
    tipr = g.hw * ww(g)
    tip = x0 + tipr
    end = x1 - g.hw * ww(g)
    if flip:
        tip, end = x1 - tipr, x0 + g.hw * ww(g)
    g.extra += outline_poly(g, [(end, cy + half), (tip, cy), (end, cy - half)], ww(g))
    g.bar(x0, x1, by)
    place(g, 2, x0, x1)


@lig("less_equal.code")
def less_equal(g: G):                # <=
    leq(g)


@lig("greater_equal.code")
def greater_equal(g: G):             # >=
    leq(g, flip=True)


def slash(g: G, cx, half_h, slope=0.42):
    """Diagonal through a bar group, centred on (cx, AX)."""
    dx = half_h * slope
    g.line(cx - dx, AX - half_h, cx + dx, AX + half_h, 0.92)


@lig("exclam_equal.code")
def exclam_equal(g: G):              # !=  -> ≠
    x0, x1 = MARGIN, 2 * CELL - MARGIN
    d = eq_d(g)
    bars(g, x0, x1, (AX + d, AX - d))
    slash(g, CELL, d + 150 + g.W * 0.3)
    place(g, 2, x0, x1)


@lig("equal_equal.code")
def equal_equal(g: G):               # ==
    x0, x1 = MARGIN, 2 * CELL - MARGIN
    d = eq_d(g)
    bars(g, x0, x1, (AX + d, AX - d))
    place(g, 2, x0, x1)


@lig("equal_equal_equal.code")
def equal_equal_equal(g: G):         # ===
    x0, x1 = MARGIN, 3 * CELL - MARGIN
    d = tri_d(g)
    bars(g, x0, x1, (AX + d, AX, AX - d))
    place(g, 3, x0, x1)


@lig("exclam_equal_equal.code")
def exclam_equal_equal(g: G):        # !==  -> ≢
    x0, x1 = MARGIN, 3 * CELL - MARGIN
    d = tri_d(g)
    bars(g, x0, x1, (AX + d, AX, AX - d))
    slash(g, 1.5 * CELL, d + 130 + g.W * 0.3)
    place(g, 3, x0, x1)


# ---------------------------------------------------------------------------
# brackets-ish
# ---------------------------------------------------------------------------

@lig("less_greater.code")
def less_greater(g: G):              # <>  -> flat diamond
    x0, x1 = MARGIN + 50, 2 * CELL - MARGIN - 50
    w = ww(g)
    half = 200 + g.W * 0.25
    pts = [(x0 + g.hw * w, AX), (CELL, AX - half), (x1 - g.hw * w, AX), (CELL, AX + half)]
    g.extra += outline_poly(g, pts, w, closed=True)
    place(g, 2, x0, x1)


def pipe_tri(g: G, flip=False):
    """|> : the bar becomes the back of a triangle pointing right."""
    w = ww(g)
    back = CELL / 2 - g.W / 2 + g.hw            # bar skeleton (bar centred in cell 1)
    tip_ink = 2 * CELL - MARGIN - 10
    tip = tip_ink - g.hw * w
    half = 250 + g.W * 0.2
    x0, x1 = back - g.hw * w, tip_ink
    pts = [(back, AX - half), (tip, AX), (back, AX + half)]
    if flip:
        pts = [(2 * CELL - x, y) for x, y in pts]
        x0, x1 = 2 * CELL - x1, 2 * CELL - x0
    g.extra += outline_poly(g, pts, w, closed=True)
    place(g, 2, x0, x1)


@lig("bar_greater.code")
def bar_greater(g: G):               # |>
    pipe_tri(g)


@lig("less_bar.code")
def less_bar(g: G):                  # <|
    pipe_tri(g, flip=True)


@lig("bar_bar.code")
def bar_bar(g: G):                   # ||
    off = 104 + g.W * 0.2
    y0, y1 = -210, 780                          # same span as `bar`
    g.vstem(CELL - off, y0, y1)
    g.vstem(CELL + off, y0, y1)
    place(g, 2, CELL - off - g.hw, CELL + off + g.hw)


@lig("colon_colon.code")
def colon_colon(g: G):               # ::  (pulled together)
    d = g.W * 1.16 + 10
    off = 112 + g.W * 0.3
    for x in (CELL - off, CELL + off):
        g.dot(x, d / 2)
        g.dot(x, g.xh - d / 2)
    place(g, 2, CELL - off - d / 2, CELL + off + d / 2)
