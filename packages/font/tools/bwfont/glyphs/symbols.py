"""Symbols: legal marks, lozenge and UI / keyboard icons.

Icons live on the font grid: a cap-height box (smaller in Mono so they fit
the 600-unit cell), drawn with the family pen (slightly lighter, IW) and
round joins.  Filled shapes are built as pre-made contours (g.extra).
"""
from __future__ import annotations

import math

from ..geometry import Contour
from ..skeleton import glyph, G, circle, mirror_x
from .latin_upper import KR, round_terminal

IW = 0.9          # icon stroke width factor (Regular); lightens with weight
LW = 0.8          # letters inside legal marks (©®™…)


def _iw(g):
    """Icon width factor: icons are dense, so they lighten a little as weight grows."""
    return IW - g.grow * (0.003 if g.mono else 0.0021)


def _lw(g):
    return LW - g.grow * (0.0026 if g.mono else 0.0018)
NUDGE = 0.8       # avoid exactly coincident round caps at corners


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _box(g: G):
    """(centre y, half size) of the icon box.  Also gives icons some air."""
    g.sb = {"l": 26 + g.grow * 0.1, "r": 26 + g.grow * 0.1}
    if g.mono:
        return 350.0, 286 + g.grow * 0.08
    return g.cap / 2, g.cap / 2 + g.grow * 0.3


def _rot(deg, cx=0.0, cy=0.0):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return lambda p: (cx + (p[0] - cx) * c - (p[1] - cy) * s, cy + (p[0] - cx) * s + (p[1] - cy) * c)


def _arc(p, cx, cy, rx, ry, a0, a1, w=None):
    """Append an elliptical arc a0 -> a1 (degrees, CCW if a1 > a0) to pen path p."""
    n = max(1, math.ceil(abs(a1 - a0) / 90 - 1e-9))
    step = (a1 - a0) / n
    for i in range(n):
        t0 = math.radians(a0 + step * i)
        t1 = math.radians(a0 + step * (i + 1))
        k = 4 / 3 * math.tan((t1 - t0) / 4)
        p0 = (cx + rx * math.cos(t0), cy + ry * math.sin(t0))
        p3 = (cx + rx * math.cos(t1), cy + ry * math.sin(t1))
        c1 = (p0[0] - k * rx * math.sin(t0), p0[1] + k * ry * math.cos(t0))
        c2 = (p3[0] + k * rx * math.sin(t1), p3[1] - k * ry * math.cos(t1))
        p.c(c1, c2, p3, w if i == n - 1 else None)
    return p


def _ring(g: G, cx, cy, ro, w=None, ry=None):
    """Closed circle whose *ink* outer radius is ro."""
    w = _iw(g) if w is None else w
    ryo = ro if ry is None else ry
    rx, ry_ = ro - g.hw * w, ryo - g.hh * w
    p = g.pen(cx, cy + ry_, w)
    _arc(p, cx, cy, rx, ry_, 90, 450)
    p.close()


def _seg(g: G, a, b, w=None, scale=1.0):
    """Line a -> b (skeleton) starting a hair inside a so corner caps don't coincide."""
    w = _iw(g) if w is None else w
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    a2 = (a[0] + dx / L * NUDGE, a[1] + dy / L * NUDGE)
    g.line(a2[0], a2[1], b[0], b[1], w, scale=scale)


def _polyline(g: G, pts, w=None, closed=False, scale=1.0):
    w = _iw(g) if w is None else w
    n = len(pts)
    for i in range(n if closed else n - 1):
        _seg(g, pts[i], pts[(i + 1) % n], w, scale)


def _rpoly(pts, r, k=0.6):
    """Filled CCW polygon with rounded corners (radius r, or list of radii)."""
    area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))
    rs = r if isinstance(r, (list, tuple)) else [r] * len(pts)
    if area < 0:
        pts = pts[::-1]
        rs = rs[::-1]
    n = len(pts)
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


def _ellipse(cx, cy, rx, ry, deg=0.0):
    T = _rot(deg)
    return circle(0, 0, 1).transform(lambda p: (cx + T((p[0] * rx, p[1] * ry))[0],
                                               cy + T((p[0] * rx, p[1] * ry))[1]))


def _rrect(g: G, x0, y0, x1, y1, rad, w=None):
    """Rounded rectangle (closed smooth stroke) from its ink box."""
    w = _iw(g) if w is None else w
    hx, hy = g.hw * w, g.hh * w
    x0, y0, x1, y1 = x0 + hx, y0 + hy, x1 - hx, y1 - hy
    p = g.pen(x0 + rad, y1, w)
    (p.h(x0, y1 - rad, k=0.56).l(x0, y0 + rad).v(x0 + rad, y0, k=0.56).l(x1 - rad, y0)
        .h(x1, y0 + rad, k=0.56).l(x1, y1 - rad).v(x1 - rad, y1, k=0.56))
    p.close()


# --- small letters for the legal marks ----------------------------------------

def _C(g: G, cx, cy, rh, w=None, open_deg=50):
    w = _lw(g) if w is None else w
    rx = rh * 0.94 - g.hw * w
    ry = rh - g.hh * w
    p = g.pen(cx + rx * math.cos(math.radians(open_deg)), cy + ry * math.sin(math.radians(open_deg)), w)
    _arc(p, cx, cy, rx, ry, open_deg, 360 - open_deg)
    p.end()


def _Rp(g: G, x0, y0, h, wd, leg=True, w=None):
    """R (or P without leg) with ink box x0..x0+wd, y0..y0+h."""
    w = _lw(g) if w is None else w
    hx, hy = g.hw * w, g.hh * w
    xs = x0 + hx
    top = y0 + h - hy
    mid = y0 + h * (0.44 if leg else 0.40)
    xr = x0 + wd - hx - (8 if leg else 0)
    rad = (top - mid) / 2
    g.line(xs, y0 + hy, xs, top, w)
    (g.pen(xs + NUDGE, top, w).l(xr - rad, top).h(xr, top - rad, k=0.6)
        .v(xr - rad, mid, k=0.6).l(xs, mid).end())
    if leg:
        _seg(g, (xr - rad * 1.05, mid), (x0 + wd - hx, y0 + hy), w * 1.0)


def _T(g: G, x0, top, h, wd, w=None):
    w = _lw(g) if w is None else w
    hx, hy = g.hw * w, g.hh * w
    g.line(x0 + hx, top - hy, x0 + wd - hx, top - hy, w)
    g.line(x0 + wd / 2, top - hy - NUDGE, x0 + wd / 2, top - h + hy, w)


def _M(g: G, x0, top, h, wd, w=None):
    w = _lw(g) if w is None else w
    hx, hy = g.hw * w, g.hh * w
    l, r = x0 + hx, x0 + wd - hx
    b = top - h + hy
    t = top - hy
    vx, vy = (l + r) / 2, top - h * 0.80
    g.line(l, b, l, t, w)
    g.line(r, b, r, t, w)
    _seg(g, (l, t), (vx, vy), w * 0.96)
    _seg(g, (r, t), (vx, vy), w * 0.96)


def _S(g: G, x0, y0, x1, y1, w=None):
    """Small S (℠): terminals cut from the bowl ovals (`round_terminal`, as in
    the capital S), so each end flows straight out of its bowl."""
    w = _lw(g) if w is None else w
    hx, hy = g.hw * w, g.hh * w
    h = y1 - y0
    cx = (x0 + x1) / 2
    lx, rx = x0 + hx + 4, x1 - hx
    yT, yB = y1 - hy, y0 + hy
    ym = y0 + h * 0.5
    ya, yb = y0 + h * 0.74, y0 + h * 0.26       # left / right extremes
    ct, t0 = round_terminal(lx, ya, yT, x1 - hx - 8, y0 + h * 0.80, KR)
    cb, t1 = round_terminal(rx, yb, yB, x0 + hx + 4, y0 + h * 0.20, KR)
    t1 = (t1[3], t1[2], t1[1], t1[0])
    (g.pen(*t0[0], w)
        .c(t0[1], t0[2], t0[3])
        .h(lx, ya, k=KR)
        .v(cx, ym, k=0.56)
        .h(rx, yb, k=0.56)
        .v(cb, yB, k=KR)
        .c(t1[1], t1[2], t1[3])
        .end())


def _legal_ring(g: G):
    if g.mono:
        ro = 290 + g.grow * 0.1
        cy = 350
    else:
        ro = 372 + g.grow * 0.3
        cy = g.cap / 2
    _ring(g, 0, cy, ro, _lw(g))
    return cy, ro


# ---------------------------------------------------------------------------
# legal marks
# ---------------------------------------------------------------------------

@glyph("copyright", 0xA9)
def copyright(g: G):
    cy, ro = _legal_ring(g)
    _C(g, 6, cy, ro * 0.46 + g.grow * 0.15)


@glyph("registered", 0xAE)
def registered(g: G):
    cy, ro = _legal_ring(g)
    h = ro * 0.98 + g.grow * 0.2
    wd = ro * 0.68 + g.grow * 0.25
    _Rp(g, -wd / 2 + 6, cy - h / 2, h, wd)


@glyph("uni2117", 0x2117)
def phonographic(g: G):
    cy, ro = _legal_ring(g)
    h = ro * 0.98 + g.grow * 0.2
    wd = ro * 0.62 + g.grow * 0.25
    _Rp(g, -wd / 2 + 14, cy - h / 2, h, wd, leg=False)


def _sup_metrics(g: G):
    h = 300 + g.grow * 0.25
    if g.mono:
        return h * 0.92, 0.72
    return h, _lw(g)


@glyph("trademark", 0x2122)
def trademark(g: G):
    h, w = _sup_metrics(g)
    top = g.cap
    if g.mono:
        tw, mw, gap = 186 + g.grow * 0.2, 252 + g.grow * 0.3, 30
    else:
        tw, mw, gap = 236 + g.grow * 0.3, 316 + g.grow * 0.5, 56 + g.grow * 0.1
    _T(g, 0, top, h, tw, w)
    _M(g, tw + gap, top, h, mw, w)


@glyph("uni2120", 0x2120)
def servicemark(g: G):
    h, w = _sup_metrics(g)
    top = g.cap
    if g.mono:
        sw, mw, gap = 180 + g.grow * 0.2, 252 + g.grow * 0.3, 36
    else:
        sw, mw, gap = 214 + g.grow * 0.3, 316 + g.grow * 0.5, 60 + g.grow * 0.1
    _S(g, 0, top - h - g.ov * 0.6, sw, top + g.ov * 0.6, w)
    _M(g, sw + gap, top, h, mw, w)


@glyph("lozenge", 0x25CA)
def lozenge(g: G):
    hwid = (210 if g.mono else 238) + g.grow * 0.3
    y0, y1 = -10, g.cap + 10
    cy = (y0 + y1) / 2
    w = 0.94
    hx, hy = g.hw * w, g.hh * w
    pts = [(0, y1 - hy * 1.2), (hwid - hx, cy), (0, y0 + hy * 1.2), (-hwid + hx, cy)]
    _polyline(g, pts, w, closed=True)


# ---------------------------------------------------------------------------
# keyboard symbols
# ---------------------------------------------------------------------------

@glyph("uni2318", 0x2318)
def command(g: G):
    cy, R = _box(g)
    hx = g.hw * _iw(g)
    rho = (R - hx) / 2.8
    a = rho * 0.8
    for i in range(4):
        g.transform(_rot(-90 * i, 0, cy))
        p = g.pen(0, cy + a, _iw(g)).l(a + rho, cy + a)
        _arc(p, a + rho, cy + a + rho, rho, rho, -90, 180)
        p.l(a, cy - 6).end()
        g.transform(None)


@glyph("uni2325", 0x2325)
def option(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    xl, xr = -R + hx, R - hx
    h = R * 0.62
    yt, yb = cy + h - hy, cy - h + hy
    x1 = xl + (xr - xl) * 0.34
    x2 = xl + (xr - xl) * 0.70
    _polyline(g, [(xl, yt), (x1, yt), (x2, yb), (xr, yb)])
    g.line(x2 + 8, yt, xr, yt, _iw(g))


@glyph("uni21E7", 0x21E7)
def shift_key(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    top, bot = cy + R - hy * 1.3, cy - R + hy
    hw_ = R * 0.92 - hx * 1.4
    sw = R * 0.40 - hx
    mid = cy - R * 0.02
    pts = [(0, top), (hw_, mid), (sw, mid), (sw, bot), (-sw, bot), (-sw, mid), (-hw_, mid)]
    _polyline(g, pts, closed=True)


@glyph("uni2303", 0x2303)
def control(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    wd = R * 0.78
    yt = cy + R * 0.62 - hy
    yb = cy - R * 0.12 + hy
    _seg(g, (0, yt), (-wd + hx, yb))
    _seg(g, (0, yt), (wd - hx, yb))


@glyph("uni238B", 0x238B)
def escape(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    r = R * 0.86
    rx, ry = r - hx, r - hy
    # broken circle, open towards the upper left
    a0 = 180 + 12
    p = g.pen(rx * math.cos(math.radians(a0)), cy + ry * math.sin(math.radians(a0)), _iw(g))
    _arc(p, 0, cy, rx, ry, a0, 360 + 90 - 12)
    p.end()
    # north-west arrow
    tip = (-R + hx + 6, cy + R - hy - 6)
    tail = (R * 0.10, cy - R * 0.10)
    ah = R * 0.52
    g.line(tail[0], tail[1], tip[0] + 4, tip[1] - 4, _iw(g))
    _seg(g, tip, (tip[0] + ah, tip[1]))
    _seg(g, tip, (tip[0], tip[1] - ah))


@glyph("uni23CE", 0x23CE)
def return_key(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    xr = R - hx
    xl = -R + hx
    yt = cy + R * 0.66 - hy
    yb = cy - R * 0.36
    rad = R * 0.34
    (g.pen(xr, yt, _iw(g)).l(xr, yb + rad).v(xr - rad, yb, k=0.56).l(xl + NUDGE, yb).end())
    ah = R * 0.44
    _seg(g, (xl, yb), (xl + ah, yb + ah))
    _seg(g, (xl, yb), (xl + ah, yb - ah))


def _erase(g: G, right=False):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    xl, xr = -R * 1.06 + hx, R * 1.06 - hx
    h = R * 0.74 - hy
    xk = xl + h * 0.85
    pts = [(xl, cy), (xk, cy + h), (xr, cy + h), (xr, cy - h), (xk, cy - h)]
    xc = (xk + xr) / 2 + 6
    s = R * 0.26
    if right:
        T = mirror_x(0)
        pts = [T(p) for p in pts]
        xc = -xc
    _polyline(g, pts, closed=True)
    g.line(xc - s, cy - s, xc + s, cy + s, _iw(g))
    g.line(xc - s, cy + s, xc + s, cy - s, _iw(g))


@glyph("uni232B", 0x232B)
def erase_left(g: G):
    _erase(g)


@glyph("uni2326", 0x2326)
def erase_right(g: G):
    _erase(g, right=True)


def _tab(g: G, right=True):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    xl, xr = -R + hx, R - hx
    ah = R * 0.46
    xt = xr - R * 0.30            # arrow tip
    T = (lambda p: p) if right else mirror_x(0)
    P = lambda x, y: T((x, y))
    g.line(*P(xl, cy), *P(xt - NUDGE, cy), _iw(g))
    _seg(g, P(xt, cy), P(xt - ah, cy + ah))
    _seg(g, P(xt, cy), P(xt - ah, cy - ah))
    g.line(*P(xr, cy - R * 0.62 + hy), *P(xr, cy + R * 0.62 - hy), _iw(g))


@glyph("uni21E5", 0x21E5)
def tab_right(g: G):
    _tab(g, True)


@glyph("uni21E4", 0x21E4)
def tab_left(g: G):
    _tab(g, False)


@glyph("uni2302", 0x2302)
def house(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    wd = R * 0.80 - hx
    bot = cy - R + hy
    eave = cy + R * 0.12
    top = cy + R - hy * 1.3
    _polyline(g, [(-wd, bot), (wd, bot), (wd, eave), (0, top), (-wd, eave)], closed=True)


# ---------------------------------------------------------------------------
# power symbols
# ---------------------------------------------------------------------------

def _power_r(g: G):
    cy, R = _box(g)
    return cy - R * 0.06, R * 0.90


@glyph("uni23FB", 0x23FB)
def power(g: G):
    cy, R = _box(g)
    pc, r = _power_r(g)
    rx, ry = r - g.hw * _iw(g), r - g.hh * _iw(g)
    a0 = 90 - 46
    p = g.pen(rx * math.cos(math.radians(a0)), pc + ry * math.sin(math.radians(a0)), _iw(g))
    _arc(p, 0, pc, rx, ry, a0, a0 - 268)
    p.end()
    g.line(0, cy + R - g.hh * _iw(g), 0, pc + R * 0.06, _iw(g))


@glyph("uni23FC", 0x23FC)
def power_onoff(g: G):
    cy, R = _box(g)
    pc, r = _power_r(g)
    _ring(g, 0, pc, r)
    g.line(0, cy + R - g.hh * _iw(g), 0, pc + R * 0.06, _iw(g))


@glyph("uni23FD", 0x23FD)
def power_on(g: G):
    cy, R = _box(g)
    g.line(0, cy - R + g.hh * _iw(g), 0, cy + R - g.hh * _iw(g), _iw(g))


# ---------------------------------------------------------------------------
# checks and crosses
# ---------------------------------------------------------------------------

def _check(g: G, scale=1.0):
    cy, R = _box(g)
    w = _iw(g)
    hx, hy = g.hw * w * scale, g.hh * w * scale
    a = (-R * 0.86 + hx, cy - R * 0.02)
    b = (-R * 0.30, cy - R * 0.70 + hy)
    c = (R * 0.86 - hx, cy + R * 0.66 - hy)
    _seg(g, b, a, w, scale)
    _seg(g, b, c, w, scale)


@glyph("uni2713", 0x2713)
def check(g: G):
    _check(g)


@glyph("uni2714", 0x2714)
def check_heavy(g: G):
    _check(g, 1.6)


def _cross(g: G, scale=1.0, ballot=False):
    cy, R = _box(g)
    s = R * 0.66
    hx = g.hw * _iw(g) * scale
    s = s - hx * 0.7
    if not ballot:
        g.line(-s, cy - s, s, cy + s, _iw(g), scale=scale)
        g.line(-s, cy + s, s, cy - s, _iw(g), scale=scale)
        return
    # hand-drawn ballot x: gently bowed strokes
    (g.pen(-s * 0.92, cy + s, _iw(g)).to(s, cy - s * 1.04, (0.6, -1), (0.9, -1), k=0.6).end(scale=scale))
    (g.pen(s * 0.96, cy + s * 1.04, _iw(g)).to(-s * 0.98, cy - s, (-0.75, -1), (-0.6, -1), k=0.6).end(scale=scale))


@glyph("uni2715", 0x2715)
def mult_x(g: G):
    _cross(g)


@glyph("uni2717", 0x2717)
def ballot_x(g: G):
    _cross(g, ballot=True)


@glyph("uni2718", 0x2718)
def ballot_x_heavy(g: G):
    _cross(g, 1.6, ballot=True)


# ---------------------------------------------------------------------------
# stars, hearts, suits
# ---------------------------------------------------------------------------

def _star_pts(cx, cy, ro, ri, n=5):
    pts = []
    for i in range(2 * n):
        a = math.radians(90 + i * 180 / n)
        r = ro if i % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


@glyph("uni2605", 0x2605)
def star_black(g: G):
    cy, R = _box(g)
    ro = R * 1.04
    c = cy - ro * 0.095
    rr = 34 + g.grow * 0.15
    g.extra.append(_rpoly(_star_pts(0, c, ro, ro * 0.44), [rr, 10] * 5))


@glyph("uni2606", 0x2606)
def star_white(g: G):
    cy, R = _box(g)
    ro = R * 1.04 - g.hw * _iw(g) * 1.2
    c = cy - R * 1.04 * 0.095
    _polyline(g, _star_pts(0, c, ro, ro * 0.47), closed=True)


def _heart_geo(cy, R, inset=0.0):
    """Square-and-two-circles heart; returns (s, bottom tip y)."""
    s = (2 * R * 0.94 - 2 * inset) / 1.707
    h = 1.56 * s
    bot = cy - h / 2 - R * 0.02
    return s, bot


def _heart_fill(g: G, cx, cy, R, flip=False):
    s, bot = _heart_geo(cy, R)
    q = s / math.sqrt(2)
    T = (lambda p: p) if not flip else (lambda p: (p[0], 2 * cy - p[1]))
    sq = [(cx, bot), (cx + q, bot + q), (cx, bot + 2 * q), (cx - q, bot + q)]
    rb = 26 + g.grow * 0.1
    g.extra.append(_rpoly([T(p) for p in sq], [rb, 1, 1, 1]))
    for sx in (1, -1):
        ccx, ccy = T((cx + sx * q / 2, bot + 1.5 * q))
        g.extra.append(circle(ccx, ccy, s / 2))


@glyph("uni2665", 0x2665)
def heart_black(g: G):
    cy, R = _box(g)
    _heart_fill(g, 0, cy, R)


@glyph("uni2764", 0x2764)
def heart_heavy(g: G):
    cy, R = _box(g)
    _heart_fill(g, 0, cy, R * 1.04)


@glyph("uni2661", 0x2661)
def heart_white(g: G):
    cy, R = _box(g)
    hx = g.hw * _iw(g)
    s, bot = _heart_geo(cy, R, hx)
    bot += g.hh * _iw(g) * 1.3
    q = s / math.sqrt(2)
    for sx in (1, -1):
        cc = (sx * q / 2, bot + 1.5 * q)
        p = g.pen(sx * NUDGE * 0.7, bot + NUDGE * 0.7, _iw(g)).l(sx * q, bot + q)
        if sx > 0:
            _arc(p, cc[0], cc[1], s / 2, s / 2, -45, 135)
        else:
            _arc(p, cc[0], cc[1], s / 2, s / 2, 225, 45)
        p.end()


def _foot(g: G, cx, top, bot, wd):
    """Flared stem foot of spade / club (filled)."""
    nw = 18 + g.grow * 0.25
    r = 18 + g.grow * 0.1
    g.extra.append(_rpoly([(cx - nw, top), (cx + nw, top), (cx + wd, bot), (cx - wd, bot)],
                          [1, 1, r, r]))


@glyph("uni2660", 0x2660)
def spade(g: G):
    cy, R = _box(g)
    hc = cy + R * 0.16
    _heart_fill(g, 0, hc, R * 0.86, flip=True)
    _foot(g, 0, hc - R * 0.2, cy - R, R * 0.36)


@glyph("uni2663", 0x2663)
def club(g: G):
    cy, R = _box(g)
    r = R * 0.34
    ty = cy + R - r
    by = cy - R * 0.04
    dx = R * 0.50
    g.extra.append(circle(0, ty, r))
    g.extra.append(circle(-dx, by, r))
    g.extra.append(circle(dx, by, r))
    g.extra.append(circle(0, by + r * 0.5, r * 0.8))
    _foot(g, 0, by + r * 0.3, cy - R, R * 0.36)


@glyph("uni2666", 0x2666)
def diamond_suit(g: G):
    cy, R = _box(g)
    wd = R * 0.72
    rr = 30 + g.grow * 0.15
    g.extra.append(_rpoly([(0, cy + R), (-wd, cy), (0, cy - R), (wd, cy)], rr))


def _spark_pts(cx, cy, r, inner):
    pts = []
    for i in range(8):
        a = math.radians(90 + i * 45)
        rr = r if i % 2 == 0 else inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


@glyph("uni2726", 0x2726)
def spark_black(g: G):
    cy, R = _box(g)
    r = R * 1.0
    rt = 22 + g.grow * 0.12
    g.extra.append(_rpoly(_spark_pts(0, cy, r, r * 0.22), [rt, r * 0.10] * 4, k=0.62))


@glyph("uni2727", 0x2727)
def spark_white(g: G):
    cy, R = _box(g)
    r = R - g.hh * _iw(g) * 1.2
    tips = [(0, cy + r), (-r, cy), (0, cy - r), (r, cy)]
    for i in range(4):
        a, b = tips[i], tips[(i + 1) % 4]
        da = (-a[0] * 0.15 + (b[0] - a[0]) * 0.0, cy - a[1])
        # leave towards the centre, arrive heading out to the next tip
        d0 = ((0 - a[0]) * 1.0 + (b[0] - a[0]) * 0.18, (cy - a[1]) * 1.0 + (b[1] - a[1]) * 0.18)
        d1 = ((b[0] - 0) * 1.0 + (b[0] - a[0]) * 0.18, (b[1] - cy) * 1.0 + (b[1] - a[1]) * 0.18)
        st = (a[0] + d0[0] / r * NUDGE, a[1] + d0[1] / r * NUDGE)
        g.pen(st[0], st[1], _iw(g)).to(b[0], b[1], d0, d1, k=0.62).end()


# ---------------------------------------------------------------------------
# misc
# ---------------------------------------------------------------------------

@glyph("uni26A0", 0x26A0)
def warning(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    wd = R * 1.10 - hx * 1.3
    top = cy + R - hy * 1.6
    bot = cy - R + hy
    _polyline(g, [(0, top), (-wd, bot), (wd, bot)], closed=True)
    d = g.W * _iw(g) * 0.92 + 14
    ib = bot + hy                         # inner ink bottom
    it = top - hy * 2.4                   # inner apex (ink, approx.)
    ih = it - ib
    g.dot(0, ib + ih * 0.12 + d / 2, d)
    sb = ib + ih * 0.12 + d + ih * 0.08 + hy * 0.8
    st = ib + ih * 0.66 - hy * 0.8
    from ..skeleton import _span
    sb, st = _span(sb, st)
    g.line(0, sb, 0, st, _iw(g) * 0.8, _iw(g) * 0.92)


@glyph("uni26A1", 0x26A1)
def bolt(g: G):
    cy, R = _box(g)
    pts = [(0.26, 1.0), (-0.52, -0.08), (-0.02, -0.08), (-0.24, -1.0), (0.54, 0.10), (0.04, 0.10)]
    pts = [(x * R, cy + y * R) for x, y in pts]
    rr = 16 + g.grow * 0.1
    g.extra.append(_rpoly(pts, [rr, rr, 4, rr, rr, 4]))


def _ballot(g: G):
    cy, R = _box(g)
    s = R * 0.90
    _rrect(g, -s, cy - s, s, cy + s, s * 0.26)
    return cy, s


@glyph("uni2610", 0x2610)
def ballot(g: G):
    _ballot(g)


@glyph("uni2611", 0x2611)
def ballot_check(g: G):
    cy, s = _ballot(g)
    k = s * 0.50
    a = (-k, cy + k * 0.02)
    b = (-k * 0.30, cy - k * 0.66)
    c = (k, cy + k * 0.62)
    _seg(g, b, a)
    _seg(g, b, c)


@glyph("uni2612", 0x2612)
def ballot_x_box(g: G):
    cy, s = _ballot(g)
    k = s * 0.44
    g.line(-k, cy - k, k, cy + k, _iw(g))
    g.line(-k, cy + k, k, cy - k, _iw(g))


def _note_head(g: G, cx, cy, R):
    g.extra.append(_ellipse(cx, cy, R * 0.32, R * 0.23, deg=22))


@glyph("uni266A", 0x266A)
def note(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    hcx, hcy = -R * 0.30, cy - R + R * 0.25
    _note_head(g, hcx, hcy, R)
    xs = hcx + R * 0.32 * 0.93 - hx
    top = cy + R - hy
    g.line(xs, hcy + R * 0.05, xs, top, _iw(g))
    (g.pen(xs + NUDGE * 0.5, top - NUDGE, _iw(g))
        .to(xs + R * 0.50, top - R * 0.56, (0.55, -1), (0.1, -1), k=0.6)
        .to(xs + R * 0.38, top - R * 1.0, (0.1, -1), (-0.6, -1), k=0.6)
        .end())


@glyph("uni266B", 0x266B)
def notes(g: G):
    cy, R = _box(g)
    hx, hy = g.hw * _iw(g), g.hh * _iw(g)
    xs = []
    rise = R * 0.18
    for i, hcx in enumerate((-R * 0.66, R * 0.50)):
        hcy = cy - R + R * 0.25 + (rise if i else 0)
        _note_head(g, hcx, hcy, R)
        x = hcx + R * 0.32 * 0.93 - hx
        xs.append((x, hcy))
    top0 = cy + R * 0.86 - hy
    top1 = top0 + rise
    for (x, hcy), top in zip(xs, (top0, top1)):
        g.line(x, hcy + R * 0.05, x, top - 4, _iw(g))
    bt = g.H * 1.6
    (x0, _), (x1, _) = xs
    g.extra.append(_rpoly([(x0 - hx, top0 + hy - bt), (x1 + hx, top1 + hy - bt), (x1 + hx, top1 + hy),
                           (x0 - hx, top0 + hy)], 12 + g.grow * 0.08))


@glyph("uni2630", 0x2630)
def trigram(g: G):
    cy, R = _box(g)
    wd = R * 0.92
    for f in (-0.62, 0, 0.62):
        g.bar(-wd, wd, cy + f * R, _iw(g))


def _info_i(g: G, cx, base, h, w=None):
    """Small slab i: stem, foot bar, entry flag and dot.  h: stem ink height."""
    w = _iw(g) if w is None else w
    hx, hy = g.hw * w, g.hh * w
    d = g.W * w * 1.1 + 14
    sw = h * 0.30
    top = base + h
    g.line(cx - sw * 0.9, top - hy, cx - NUDGE, top - hy, w)
    g.line(cx, top - hy, cx, base + hy, w)
    g.line(cx - sw, base + hy, cx + sw, base + hy, w)
    g.dot(cx, top + d / 2 + h * 0.16 + 6, d)


@glyph("uni2139", 0x2139)
def info(g: G):
    _info_i(g, 0, 0, g.xh, 1.0)


@glyph("uni24D8", 0x24D8)
def circled_i(g: G):
    cy, R = _box(g)
    _ring(g, 0, cy, R, _lw(g))
    h = R * 0.78
    _info_i(g, 0, cy - R * 0.56, h, _lw(g))
