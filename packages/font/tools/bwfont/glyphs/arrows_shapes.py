"""Arrows (U+2190 block, double arrows, hooks, circles, long arrows) and
geometric shapes (triangles, squares, circles, diamonds, dotted circle).

Arrows are pen strokes: a shaft plus a head made of two wing strokes meeting
at the tip (their round caps form the rounded join).  They sit on the math
axis (AX) and use a tabular advance like the figures.

Filled shapes are pre-built contours (g.extra) with rounded corners; their
outlined counterparts are pen strokes, one per side (rule 2).
"""
from __future__ import annotations

import math

from ..geometry import Contour, KAPPA
from ..skeleton import glyph, G, circle, mirror_x, mirror_y

AX = 340.0            # math axis (centre of arrows / operators)
WING = 0.92           # wing stroke width factor (diagonals)
ANG = 45.0            # half-angle of single arrow heads
ANG2 = 52.0           # half-angle of double arrow heads


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------

def adv_arrow(g: G):
    return 600 if g.mono else 560 + g.grow * 0.5


def ink_arrow(g: G):
    """Ink length of a horizontal arrow."""
    return g.wd(486, 480, grow=0.6)


def set_cell(g: G, adv):
    """Fixed advance with geometric (not optical) centring of the ink."""
    g.advance = adv
    g.lsb = 0
    g.rsb = 0


def head_len(g: G):
    # wings must stay clearly longer than the stroke is thick, so the head
    # reads as a chevron (not a blob) at heavy weights
    return 128 + g.W * 0.78


def head_len2(g: G):
    return 156 + g.W * 0.84


def dbl_gap(g: G):
    """Half distance between the shafts of a double arrow."""
    return 60 + g.W * 0.3


# ---------------------------------------------------------------------------
# arrow primitives (local frame: travel along +x, axis at t = 0)
# ---------------------------------------------------------------------------

def push(g: G, F):
    """Compose transform F inside the current one (restore with pop)."""
    old = g._tx
    g._tx = F if old is None else (lambda p: old(F(p)))
    return old


def pop(g: G, old):
    g._tx = old


def frame(ox, oy, ux, uy):
    """Map local (s, t) to design space: origin + s*u + t*n (n = left normal)."""
    m = math.hypot(ux, uy)
    ux, uy = ux / m, uy / m
    nx, ny = -uy, ux
    return lambda p: (ox + p[0] * ux + p[1] * nx, oy + p[0] * uy + p[1] * ny)


def ww(g: G):
    """Wing width factor: a touch lighter at heavy weights so the head keeps
    a visible notch."""
    return 0.95 - g.W * 0.0007


def wings(g: G, s, L, ang, sign=1, w=None):
    """Arrow head: two wings from the tip (s, 0) going back at +-ang, built
    as ONE contour with a round join at the tip (identical round caps on top
    of each other make the overlap remover drop pieces).
    sign=+1: arrow points to +s; -1: points to -s."""
    w = ww(g) if w is None else w
    a = math.radians(ang)
    dx, dy = L * math.cos(a), L * math.sin(a)
    T = g._tx or (lambda p: p)
    pts = [T((s - sign * dx, dy)), T((s, 0)), T((s - sign * dx, -dy))]
    g.extra += outline_poly(g, pts, w)


# ---------------------------------------------------------------------------
# exact stroked polylines (pen space = design space with y * W/H, where the
# family's elliptical pen is a circle)
# ---------------------------------------------------------------------------

def _arc_ops(c, R, a0, sweep, n):
    """Append n cubic pieces of a circular arc around c, from angle a0."""
    ops = []
    step = sweep / n
    h = 4 / 3 * math.tan(step / 4) * R
    for i in range(n):
        t0 = a0 + step * i
        t1 = t0 + step
        p0 = (c[0] + R * math.cos(t0), c[1] + R * math.sin(t0))
        p1 = (c[0] + R * math.cos(t1), c[1] + R * math.sin(t1))
        d0 = (-math.sin(t0), math.cos(t0))
        d1 = (-math.sin(t1), math.cos(t1))
        ops.append(("curve", (p0[0] + d0[0] * h, p0[1] + d0[1] * h),
                    (p1[0] - d1[0] * h, p1[1] - d1[1] * h), p1))
    return ops


def _ang(v):
    return math.atan2(v[1], v[0])


def _isect(p, d, q, e):
    den = d[0] * e[1] - d[1] * e[0]
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + d[0] * t, p[1] + d[1] * t)


def _dirs(P, closed):
    n = len(P)
    m = n if closed else n - 1
    D = []
    for i in range(m):
        a, b = P[i], P[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        D.append(((b[0] - a[0]) / L, (b[1] - a[1]) / L))
    return D


def _right_side(P, R):
    """Right-hand offset of an open polyline: round joins on convex (left
    turn) vertices, mitre points on concave ones.  Returns (start, ops)."""
    D = _dirs(P, False)
    rn = [(d[1], -d[0]) for d in D]                # right normals
    off = lambda p, nn: (p[0] + nn[0] * R, p[1] + nn[1] * R)
    start = off(P[0], rn[0])
    ops = []
    for i in range(1, len(P) - 1):
        V = P[i]
        da, db = D[i - 1], D[i]
        cr = da[0] * db[1] - da[1] * db[0]
        if cr > 0:      # left turn: right side is the outside -> round join
            ops.append(("line", off(V, rn[i - 1])))
            sweep = _ang(rn[i]) - _ang(rn[i - 1])
            sweep = (sweep + math.pi) % (2 * math.pi) - math.pi
            ops += _arc_ops(V, R, _ang(rn[i - 1]), sweep, 2)
        else:
            ops.append(("line", _isect(off(V, rn[i - 1]), da, off(V, rn[i]), db)))
    ops.append(("line", off(P[-1], rn[-1])))
    return start, ops


def outline_poly(g: G, pts, w=1.0, closed=False):
    """Outline of a polyline stroked with the family pen: round caps, round
    outer joins, mitred inner joins -- as exact contours, no overlaps.
    Open: one contour.  Closed (convex polygon): outer + inner contour."""
    ratio = g.W / g.H
    R = g.hw * w
    P = [(x, y * ratio) for x, y in pts]
    back = lambda c: c.transform(lambda p: (p[0], p[1] / ratio))
    if closed:
        a2 = sum(P[i - 1][0] * P[i][1] - P[i][0] * P[i - 1][1] for i in range(len(P)))
        if a2 < 0:
            P.reverse()
        n = len(P)
        D = _dirs(P, True)
        rn = [(d[1], -d[0]) for d in D]
        ln = [(-d[1], d[0]) for d in D]
        off = lambda p, nn: (p[0] + nn[0] * R, p[1] + nn[1] * R)
        # outer: round joins at every (convex) vertex, counter-clockwise
        first = off(P[0], rn[-1])
        outer = Contour(first)
        for i in range(n):
            a, b = rn[i - 1], rn[i]
            if i:
                outer.ops.append(("line", off(P[i], a)))
            sweep = (_ang(b) - _ang(a) + math.pi) % (2 * math.pi) - math.pi
            outer.ops += _arc_ops(P[i], R, _ang(a), sweep, 2)
        outer.ops.append(("line", first))
        # inner: mitre points, clockwise
        q = [_isect(off(P[i], ln[i - 1]), D[i - 1], off(P[i], ln[i]), D[i]) for i in range(n)]
        q.reverse()
        inner = Contour(q[0], [("line", p) for p in q[1:]] + [("line", q[0])])
        return [back(outer), back(inner)]
    s0, ops = _right_side(P, R)
    c = Contour(s0, ops)
    D = _dirs(P, False)
    rn_last = (D[-1][1], -D[-1][0])
    ln_first = (-D[0][1], D[0][0])
    c.ops += _arc_ops(P[-1], R, _ang(rn_last), math.pi, 2)          # end cap
    s1, ops1 = _right_side(list(reversed(P)), R)
    c.ops += ops1                                                     # left side, backwards
    c.ops += _arc_ops(P[0], R, _ang(ln_first), math.pi, 2)          # start cap
    return [back(c)]


def arrow1(g: G, s0, s1, head0=False, head1=True, L=None, ang=ANG):
    """Single arrow along the local axis, skeleton from s0 to s1 (tips)."""
    L = head_len(g) if L is None else L
    back = g.hw * 1.0          # shaft cap tucked inside the wings (no coincident caps)
    a = s0 + (back if head0 else 0)
    b = s1 - (back if head1 else 0)
    g.line(a, 0, b, 0)
    if head1:
        wings(g, s1, L, ang, 1)
    if head0:
        wings(g, s0, L, ang, -1)


def arrow2(g: G, s0, s1, head0=False, head1=True, L=None, ang=ANG2, d=None):
    """Double arrow (⇒): two shafts at t = +-d ending inside the wings."""
    L = head_len2(g) if L is None else L
    d = dbl_gap(g) if d is None else d
    cut = d / math.tan(math.radians(ang)) + g.hw * 0.45
    a = s0 + (cut if head0 else 0)
    b = s1 - (cut if head1 else 0)
    for t in (d, -d):
        g.line(a, t, b, t)
    if head1:
        wings(g, s1, L, ang, 1)
    if head0:
        wings(g, s0, L, ang, -1)


def horiz(g: G, fn, ink=None, cy=AX, **kw):
    """Horizontal arrow whose ink spans 0..ink.  Wing caps define the tip."""
    ink = ink_arrow(g) if ink is None else ink
    tipr = g.hw * ww(g)
    h0 = kw.get("head0", False)
    h1 = kw.get("head1", True)
    s0 = tipr if h0 else g.hw
    s1 = ink - (tipr if h1 else g.hw)
    _old = push(g, frame(0, cy, 1, 0))
    fn(g, s0, s1, **kw)
    pop(g, _old)


def vert(g: G, fn, ink=None, cx=0.0, cy=AX, up=True, **kw):
    """Vertical arrow centred on (cx, cy), ink length `ink`."""
    ink = vlen(g) if ink is None else ink
    tipr = g.hh * ww(g)
    h0 = kw.get("head0", False)
    h1 = kw.get("head1", True)
    s0 = (tipr if h0 else g.hh) - ink / 2
    s1 = ink / 2 - (tipr if h1 else g.hh)
    _old = push(g, frame(cx, cy, 0, 1 if up else -1))
    fn(g, s0, s1, **kw)
    pop(g, _old)


def both_ink(g: G):
    """Double-headed arrows use (almost) the whole advance."""
    return adv_arrow(g) - 36


def both_k(g: G):
    """Head scale for double-headed arrows: smaller at heavy weights so the
    shaft between the two heads stays visible."""
    return 0.98 - g.W * 0.0017


def vlen(g: G):
    return 668 + g.grow * 0.1


# ---------------------------------------------------------------------------
# arrows
# ---------------------------------------------------------------------------

def _harrow(name, cp, right=True, both=False):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        if both:
            horiz(g, arrow1, ink=both_ink(g), head0=True, head1=True, L=head_len(g) * both_k(g))
        elif right:
            horiz(g, arrow1)
        else:
            horiz(g, arrow1, head0=True, head1=False)
        set_cell(g, adv_arrow(g))
    return f


def _varrow(name, cp, up=True, both=False):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        if both:
            vert(g, arrow1, head0=True, head1=True, L=head_len(g) * (both_k(g) + 0.06))
        else:
            vert(g, arrow1, up=up)
        set_cell(g, adv_arrow(g))
    return f


_harrow("arrowleft", 0x2190, right=False)
_harrow("arrowright", 0x2192)
_harrow("arrowboth", 0x2194, both=True)
_varrow("arrowup", 0x2191)
_varrow("arrowdown", 0x2193, up=False)
_varrow("arrowupdn", 0x2195, both=True)


def _diag(name, cp, ux, uy):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        # ink box ~ size x size centred on (size/2, AX)
        size = g.wd(450, 446, grow=0.4)
        half = size / 2
        # skeleton half-extent along x/y (tip caps add ~hw / hh)
        sx = half - g.hw * WING
        L = math.hypot(sx, sx) * 2
        _old = push(g, frame(half, AX, ux, uy))
        arrow1(g, -L / 2, L / 2, L=head_len(g) * 1.02 + 6)
        pop(g, _old)
        set_cell(g, adv_arrow(g))
    return f


_diag("uni2196", 0x2196, -1, 1)
_diag("uni2197", 0x2197, 1, 1)
_diag("uni2198", 0x2198, 1, -1)
_diag("uni2199", 0x2199, -1, -1)


# double arrows ⇐ ⇑ ⇒ ⇓ ⇔ ⇕
def _hdouble(name, cp, right=True, both=False):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        if both:
            horiz(g, arrow2, ink=both_ink(g), head0=True, head1=True, L=head_len2(g) * both_k(g))
        elif right:
            horiz(g, arrow2)
        else:
            horiz(g, arrow2, head0=True, head1=False)
        set_cell(g, adv_arrow(g))
    return f


def _vdouble(name, cp, up=True, both=False):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        d = 58 + g.W * 0.36
        if both:
            vert(g, arrow2, head0=True, head1=True, d=d, L=head_len2(g) * (both_k(g) + 0.06))
        else:
            vert(g, arrow2, up=up, d=d)
        set_cell(g, adv_arrow(g))
    return f


_hdouble("uni21D0", 0x21D0, right=False)
_vdouble("uni21D1", 0x21D1)
_hdouble("uni21D2", 0x21D2)
_vdouble("uni21D3", 0x21D3, up=False)
_hdouble("uni21D4", 0x21D4, both=True)
_vdouble("uni21D5", 0x21D5, both=True)


# long arrows ⟵ ⟶ ⟷
def _long(name, cp, right=True, both=False):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        ink = g.wd(900, 548, grow=0.5)
        kw = dict(head0=True, head1=True) if both else (dict() if right else dict(head0=True, head1=False))
        horiz(g, arrow1, ink=ink, **kw)
        set_cell(g, 600 if g.mono else 1000 + g.grow * 0.5)
    return f


_long("uni27F5", 0x27F5, right=False)
_long("uni27F6", 0x27F6)
_long("uni27F7", 0x27F7, both=True)


# ⇄ ⇆ : two arrows stacked
def _pair(name, cp, top_right=True):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        off = 138 + g.grow * 0.25
        L = head_len(g) * 0.84
        if top_right:
            horiz(g, arrow1, cy=AX + off, L=L)
            horiz(g, arrow1, cy=AX - off, L=L, head0=True, head1=False)
        else:
            horiz(g, arrow1, cy=AX + off, L=L, head0=True, head1=False)
            horiz(g, arrow1, cy=AX - off, L=L)
        set_cell(g, adv_arrow(g))
    return f


_pair("uni21C4", 0x21C4, True)
_pair("uni21C6", 0x21C6, False)


# ↩ ↪ hooked arrows
def hook_left(g: G):
    """↩ : head on the left pointing left, hook on the right curling up."""
    ink = ink_arrow(g)
    r = 132 + g.grow * 0.25                 # hook radius (skeleton)
    ylo = AX - r + 6
    yhi = ylo + 2 * r
    tip = g.hw * ww(g)
    xr = ink - g.hw
    (g.pen(tip + g.hw, ylo)
        .l(xr - r, ylo)
        .h(xr, ylo + r, k=0.56)
        .v(xr - r, yhi, k=0.56)
        .l(xr - r - 24, yhi)
        .end())
    _old = push(g, frame(0, ylo, 1, 0))
    wings(g, tip, head_len(g), ANG, -1)
    pop(g, _old)


@glyph("uni21A9", 0x21A9, zone="fig")
def arrowhookleft(g: G):
    hook_left(g)
    set_cell(g, adv_arrow(g))


@glyph("uni21AA", 0x21AA, zone="fig")
def arrowhookright(g: G):
    ink = ink_arrow(g)
    _old = push(g, mirror_x(ink / 2))
    hook_left(g)
    pop(g, _old)
    set_cell(g, adv_arrow(g))


# ↰ ↱ ↲ ↳ : bent arrows
def _bent(name, cp, flipx, flipy):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        ink = g.wd(470, 466, grow=0.4)
        fx = mirror_x(ink / 2) if flipx else (lambda p: p)
        fy = mirror_y(AX) if flipy else (lambda p: p)
        _bent_into(g, lambda p: fx(fy(p)))
        set_cell(g, adv_arrow(g))
    return f


def _bent_into(g: G, T):
    """↲ (before transform T): stem down on the right, turning left at the
    bottom; head points left."""
    ink = g.wd(470, 466, grow=0.4)
    top = AX + 300
    ybot = AX - 110
    rc = 120 + g.grow * 0.2
    xs = ink - g.hw
    tip = g.hw * ww(g)
    old = push(g, T)
    (g.pen(xs, top - g.hh)
        .l(xs, ybot + rc)
        .v(xs - rc, ybot, k=0.58)
        .l(tip + g.hw, ybot)
        .end())
    inner = push(g, frame(0, ybot, 1, 0))
    wings(g, tip, head_len(g), ANG, -1)
    pop(g, inner)
    pop(g, old)


_bent("uni21B0", 0x21B0, False, True)    # ↰ up, tip left
_bent("uni21B1", 0x21B1, True, True)     # ↱ up, tip right
_bent("uni21B2", 0x21B2, False, False)   # ↲ down, tip left
_bent("uni21B3", 0x21B3, True, False)    # ↳ down, tip right


# ↺ ↻ open circle arrows
def arc_pen(g: G, cx, cy, R, a0, a1, w=1.0):
    """Circular arc from angle a0 to a1 (degrees) as one smooth stroke."""
    n = max(1, math.ceil(abs(a1 - a0) / 90 - 1e-9))
    step = (a1 - a0) / n
    pt = lambda a: (cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
    p = g.pen(*pt(a0), w)
    hl = 4 / 3 * math.tan(math.radians(abs(step)) / 4) * R
    sgn = 1 if step > 0 else -1
    for i in range(n):
        a = a0 + step * i
        b = a + step
        pa, pb = pt(a), pt(b)
        ta = (-math.sin(math.radians(a)) * sgn, math.cos(math.radians(a)) * sgn)
        tb = (-math.sin(math.radians(b)) * sgn, math.cos(math.radians(b)) * sgn)
        p.c((pa[0] + ta[0] * hl, pa[1] + ta[1] * hl), (pb[0] - tb[0] * hl, pb[1] - tb[1] * hl), pb)
    return p


CIRC_TAIL, CIRC_HEAD = 4.0, 96.0


def circle_arrow(g: G):
    """↻ clockwise: tail at upper right, head at the top pointing right."""
    D = g.wd(500, 470, grow=0.4)
    R = D / 2 - g.hw
    cx = D / 2
    a_tail, a_head = CIRC_TAIL, CIRC_HEAD - 360.0
    arc_pen(g, cx, AX, R, a_tail, a_head).end()
    tip = (cx + R * math.cos(math.radians(a_head)), AX + R * math.sin(math.radians(a_head)))
    th = math.radians(a_head)
    u = (math.sin(th), -math.cos(th))           # clockwise tangent
    _old = push(g, frame(tip[0], tip[1], u[0], u[1]))
    wings(g, 0, head_len(g) * 0.86, ANG)
    pop(g, _old)
    return D


@glyph("uni21BB", 0x21BB, zone="fig")
def cw_circle(g: G):
    circle_arrow(g)
    set_cell(g, adv_arrow(g))


@glyph("uni21BA", 0x21BA, zone="fig")
def ccw_circle(g: G):
    D = g.wd(500, 470, grow=0.4)
    old = push(g, mirror_x(D / 2))
    circle_arrow(g)
    pop(g, old)
    set_cell(g, adv_arrow(g))


# ➔ heavy wide-headed rightwards arrow
@glyph("uni2794", 0x2794, zone="fig")
def heavy_arrow(g: G):
    ink = ink_arrow(g)
    sc = (g.W * 0.9 + 50) / g.W        # heavy at every weight, tapering at Black
    wsc = ww(g) * sc
    tipr = g.hw * wsc
    s1 = ink - tipr
    old = push(g, frame(0, AX, 1, 0))
    g.line(g.hw * sc, 0, s1 - g.hw * sc, 0, scale=sc)
    wings(g, s1, head_len(g) * 1.08 + 20, 48, w=wsc)
    pop(g, old)
    set_cell(g, adv_arrow(g))


# ---------------------------------------------------------------------------
# filled-shape contour helpers
# ---------------------------------------------------------------------------

def rounded_poly(pts, r):
    """Counter-clockwise polygon with circular-ish rounded corners of radius r."""
    pts = list(pts)
    a2 = 0.0
    for i in range(len(pts)):
        a2 += pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1]
    if a2 < 0:
        pts.reverse()
    n = len(pts)
    corners = []
    for i in range(n):
        v = pts[i]
        a = pts[i - 1]
        b = pts[(i + 1) % n]
        ua = _unit((a[0] - v[0], a[1] - v[1]))
        ub = _unit((b[0] - v[0], b[1] - v[1]))
        inner = math.acos(max(-1.0, min(1.0, ua[0] * ub[0] + ua[1] * ub[1])))
        turn = math.pi - inner
        cut = r / math.tan(inner / 2)
        kk = (4 / 3 * math.tan(turn / 4)) / math.tan(turn / 2)
        p1 = (v[0] + ua[0] * cut, v[1] + ua[1] * cut)
        p2 = (v[0] + ub[0] * cut, v[1] + ub[1] * cut)
        c1 = (p1[0] + (v[0] - p1[0]) * kk, p1[1] + (v[1] - p1[1]) * kk)
        c2 = (p2[0] + (v[0] - p2[0]) * kk, p2[1] + (v[1] - p2[1]) * kk)
        corners.append((p1, c1, c2, p2))
    c = Contour(corners[-1][3])
    for p1, c1, c2, p2 in corners:
        c.ops.append(("line", p1))
        c.ops.append(("curve", c1, c2, p2))
    return c


def _unit(v):
    m = math.hypot(*v)
    return (v[0] / m, v[1] / m)


def half_disc(cx, cy, R, left=True):
    """Half disc (left or right), counter-clockwise."""
    k = KAPPA
    if left:
        c = Contour((cx, cy + R))
        c.ops.append(("curve", (cx - R * k, cy + R), (cx - R, cy + R * k), (cx - R, cy)))
        c.ops.append(("curve", (cx - R, cy - R * k), (cx - R * k, cy - R), (cx, cy - R)))
        c.ops.append(("line", (cx, cy + R)))
    else:
        c = Contour((cx, cy - R))
        c.ops.append(("curve", (cx + R * k, cy - R), (cx + R, cy - R * k), (cx + R, cy)))
        c.ops.append(("curve", (cx + R, cy + R * k), (cx + R * k, cy + R), (cx, cy + R)))
        c.ops.append(("line", (cx, cy - R)))
    return c


def corner_r(g: G):
    return 22 + g.W * 0.42


def shape_sb(g: G):
    if g.mono:
        g.advance = 600
        g.lsb = g.rsb = 0
    else:
        g.lsb = g.rsb = 56 + g.grow * 0.05


def tri_size(g: G, small=False):
    w = g.wd(560, 480, grow=0.0)
    return w * (0.6 if small else 1.0)


def tri_pts(w, h, direction, cx, cy):
    """Triangle with base w, height h, pointing up/down/left/right, bbox centred."""
    if direction == "up":
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx, cy + h / 2)]
    if direction == "down":
        return [(cx - w / 2, cy + h / 2), (cx, cy - h / 2), (cx + w / 2, cy + h / 2)]
    if direction == "right":
        return [(cx - h / 2, cy - w / 2), (cx + h / 2, cy), (cx - h / 2, cy + w / 2)]
    return [(cx + h / 2, cy - w / 2), (cx + h / 2, cy + w / 2), (cx - h / 2, cy)]


TRI_H = 0.88
OUTW = 0.94           # pen width factor for outlined shapes


def _tri_filled(name, cp, direction, small=False):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        w = tri_size(g, small)
        h = w * TRI_H
        r = corner_r(g) * (0.62 if small else 1.0)
        g.extra.append(rounded_poly(tri_pts(w, h, direction, 0, AX), r))
        shape_sb(g)
    return f


def _tri_outline(name, cp, direction, small=False):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        w = tri_size(g, small)
        h = w * TRI_H
        # inset the skeleton so the outer ink roughly matches the filled triangle
        ins = 0.5
        pts = tri_pts(w - g.W * (1 + ins), h - g.H * (1 + ins * 0.6), direction, 0, AX)
        if direction in ("left", "right"):
            pts = tri_pts(w - g.H * (1 + ins), h - g.W * (1 + ins * 0.6), direction, 0, AX)
        g.extra += outline_poly(g, pts, OUTW, closed=True)
        shape_sb(g)
    return f


_tri_filled("uni25B2", 0x25B2, "up")
_tri_filled("uni25BC", 0x25BC, "down")
_tri_filled("uni25C0", 0x25C0, "left")
_tri_filled("uni25B6", 0x25B6, "right")
_tri_outline("uni25B3", 0x25B3, "up")
_tri_outline("uni25BD", 0x25BD, "down")
_tri_outline("uni25C1", 0x25C1, "left")
_tri_outline("uni25B7", 0x25B7, "right")
_tri_filled("uni25B4", 0x25B4, "up", True)
_tri_filled("uni25BE", 0x25BE, "down", True)
_tri_filled("uni25C2", 0x25C2, "left", True)
_tri_filled("uni25B8", 0x25B8, "right", True)


# squares ■ □ ▪ ▫, rectangles ▬ ▮
def sq_size(g: G):
    return g.wd(540, 470, grow=0.0)


def _rect_filled(name, cp, wf, hf):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        s = sq_size(g)
        w, h = s * wf, s * hf
        r = corner_r(g) * min(1.0, 0.6 + 0.4 * min(wf, hf))
        g.extra.append(rounded_poly([(-w / 2, AX - h / 2), (w / 2, AX - h / 2), (w / 2, AX + h / 2),
                                     (-w / 2, AX + h / 2)], r))
        shape_sb(g)
    return f


def _rect_outline(name, cp, wf, hf):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        s = sq_size(g)
        w, h = s * wf, s * hf
        x0, x1 = -w / 2 + g.hw, w / 2 - g.hw
        y0, y1 = AX - h / 2 + g.hh, AX + h / 2 - g.hh
        g.extra += outline_poly(g, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 1.0, closed=True)
        shape_sb(g)
    return f


_rect_filled("uni25A0", 0x25A0, 1.0, 1.0)
_rect_outline("uni25A1", 0x25A1, 1.0, 1.0)
_rect_filled("uni25AA", 0x25AA, 0.56, 0.56)
_rect_outline("uni25AB", 0x25AB, 0.56, 0.56)
_rect_filled("uni25AC", 0x25AC, 1.12, 0.46)
_rect_filled("uni25AE", 0x25AE, 0.52, 1.1)


# circles ● ○ ◦ ◉ ◐ ◑
def circ_d(g: G):
    return g.wd(600, 500, grow=0.0)


@glyph("uni25CF", 0x25CF, zone="fig")
def blackcircle(g: G):
    D = circ_d(g)
    g.extra.append(circle(0, AX, D / 2))
    shape_sb(g)


@glyph("uni25CB", 0x25CB, zone="fig")
def whitecircle(g: G):
    D = circ_d(g)
    g.oval(-D / 2, AX - D / 2, D / 2, AX + D / 2)
    shape_sb(g)


@glyph("uni25E6", 0x25E6, zone="fig")
def whitebullet(g: G):
    D = 220 + g.W * 0.9
    g.oval(-D / 2, AX - D / 2, D / 2, AX + D / 2, w=0.72)
    shape_sb(g)


@glyph("uni25C9", 0x25C9, zone="fig")
def fisheye(g: G):
    D = circ_d(g)
    g.oval(-D / 2, AX - D / 2, D / 2, AX + D / 2, w=0.9)
    d = D * 0.42 - g.W * 0.4
    g.extra.append(circle(0, AX, d / 2))
    shape_sb(g)


def _half(name, cp, left):
    @glyph(name, cp, zone="fig")
    def f(g: G):
        D = circ_d(g)
        g.oval(-D / 2, AX - D / 2, D / 2, AX + D / 2)
        g.extra.append(half_disc(0, AX, D / 2 - g.hw * 0.5, left))
        shape_sb(g)
    return f


_half("uni25D0", 0x25D0, True)
_half("uni25D1", 0x25D1, False)


# diamonds ◆ ◇
def dia_size(g: G):
    return g.wd(600, 500, grow=0.0)


@glyph("uni25C6", 0x25C6, zone="fig")
def blackdiamond(g: G):
    s = dia_size(g) / 2
    g.extra.append(rounded_poly([(0, AX - s), (s, AX), (0, AX + s), (-s, AX)], corner_r(g) * 0.9))
    shape_sb(g)


@glyph("uni25C7", 0x25C7, zone="fig")
def whitediamond(g: G):
    s = dia_size(g) / 2
    sx = s - g.hw * WING * 1.3
    sy = s - g.hh * WING * 1.3
    pts = [(0, AX - sy), (sx, AX), (0, AX + sy), (-sx, AX)]
    g.extra += outline_poly(g, pts, OUTW, closed=True)
    shape_sb(g)


# ◌ dotted circle: x-height sized like 'o', so combining marks sit right on it
@glyph("uni25CC", 0x25CC, zone="lc")
def dottedcircle(g: G):
    D = g.wd(540, 500, grow=0.2)
    d = 38 + g.W * 0.3
    cy = g.xh / 2
    R = D / 2 - d / 2
    n = 12
    for i in range(n):
        a = math.radians(90 + 360 * i / n)
        g.extra.append(circle(D / 2 + R * math.cos(a), cy + R * math.sin(a), d / 2))
    g.anchor("top", D / 2, g.xh)
    g.anchor("bottom", D / 2, 0)
    g.anchor("center", D / 2, cy)
