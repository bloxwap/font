"""Kana drawing context.

Every kana is drawn in a 1000 x 1000 *design grid* (y up).  The grid is
mapped onto an ink box in the em: the skeleton range is inset by the pen
radius, so the ink of the extreme strokes touches the box at every weight
(the same rule the hanzi FACE and the Hangul jamo use).  Pen scale is
han.engine.cjk_weight_factor(W) so kana colour matches the kanji; topology
never depends on weight (only positions, linearly).

Boxes
    FULL   ~90 % of the kanji face, centred on the ideographic em centre
           (500, 380); Mono adds +100 (1200 advance)
    small  70 % of FULL, sitting on the FULL bottom, centred a little left
    half   halfwidth katakana: same height as FULL, half width
"""
from __future__ import annotations

import math

from ..han.engine import FACE, cjk_weight_factor

CY = 380.0                       # ideographic em centre (y)
SIZE = 0.90                      # kana face / kanji face
HW_ = (FACE[2] - FACE[0]) / 2 * SIZE
HH_ = (FACE[3] - FACE[1]) / 2 * SIZE
FULL = (500 - HW_, CY - HH_, 500 + HW_, CY + HH_)
SMALL_K = 0.74
SMALL_CX = 482.0                 # small kana: horizontal centre (sans em)
HALF_K = 0.50                    # halfwidth katakana: width ratio (sans)
HALF_K_MONO = 0.56



def wfactor(g):
    return cjk_weight_factor(g.W)


def _dir(a):
    if isinstance(a, (tuple, list)):
        m = math.hypot(*a)
        return (a[0] / m, a[1] / m)
    r = math.radians(a)
    return (math.cos(r), math.sin(r))


def handles(p0, p1, d0, d1, k0=0.56, k1=None):
    """Cubic handles leaving p0 along d0, arriving at p1 along d1."""
    k1 = k0 if k1 is None else k1
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    chord = math.hypot(dx, dy)
    den = d0[0] * d1[1] - d0[1] * d1[0]
    l0 = l1 = None
    if abs(den) > 0.03:
        s = (dx * d1[1] - dy * d1[0]) / den
        t = (d0[0] * dy - d0[1] * dx) / den
        if s > 0 and t > 0:
            l0, l1 = s * k0, t * k1
    if l0 is None:
        dot = d0[0] * d1[0] + d0[1] * d1[1]
        base = 0.62 if dot < -0.5 else 0.38
        l0, l1 = chord * base * k0 / 0.56, chord * base * k1 / 0.56
    l0 = min(l0, 0.66 * chord)
    l1 = min(l1, 0.66 * chord)
    return ((p0[0] + d0[0] * l0, p0[1] + d0[1] * l0),
            (p1[0] - d1[0] * l1, p1[1] - d1[1] * l1))


class K:
    """Design-grid drawing context bound to a glyph builder."""

    def __init__(self, g, box, s):
        self.g, self.s = g, s
        x0, y0, x1, y1 = box
        rx, ry = g.hw * s, g.hh * s
        self.ax = (x1 - x0 - 2 * rx) / 1000.0
        self.ay = (y1 - y0 - 2 * ry) / 1000.0
        self.ox, self.oy = x0 + rx, y0 + ry
        # stroke thickness in design units (vertical stroke / horizontal stroke)
        self.t = g.W * s / self.ax
        self.th = g.H * s / self.ay
        self.Ws = g.W * s
        self.voiced = None        # 'd' / 'h' while drawing the base of a voiced kana
        g.transform(lambda p: (self.ox + p[0] * self.ax, self.oy + p[1] * self.ay))

    def done(self):
        self.g.transform(None)

    def em(self, u, v):
        return (self.ox + u * self.ax, self.oy + v * self.ay)

    def em_cy_design(self):
        """Design-grid v of the ideographic em centre (y = 380)."""
        return (CY - self.oy) / self.ay

    # -- strokes ------------------------------------------------------------
    def L(self, x0, y0, x1, y1, w=1.0, w1=None):
        self.g.pen(x0, y0, w).l(x1, y1, w if w1 is None else w1).end(scale=self.s)

    def S(self, *pts, w=1.0, k=0.56):
        """Smooth stroke through points (x, y, angle[, k]) -- angle in
        degrees (0 = right, 90 = up) or a direction vector; the tangent is
        shared by both segments meeting at a point, so the path is smooth."""
        x, y = pts[0][0], pts[0][1]
        ws = w if isinstance(w, (list, tuple)) else [w] * len(pts)
        p = self.g.pen(x, y, ws[0])
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            ka = a[3] if len(a) > 3 else k
            kb = b[3] if len(b) > 3 else k
            c1, c2 = handles(a[:2], b[:2], _dir(a[2]), _dir(b[2]), ka, kb)
            p.c(c1, c2, (b[0], b[1]), ws[i + 1])
        p.end(scale=self.s)

    def ring(self, cx, cy, rx, ry, w=0.93, k=0.555):
        """Closed ring, skeleton radii in design units."""
        (self.g.pen(cx, cy + ry, w).h(cx - rx, cy, k).v(cx, cy - ry, k)
            .h(cx + rx, cy, k).v(cx, cy + ry, k).close(scale=self.s))

    # -- voicing marks (geometry in em units so they stay isotropic) ----------
    def _ramp(self):
        """0 at Thin .. 1 at Black (hanzi pen width)."""
        return min(1.0, max(0.0, (self.Ws - 21.0) / 96.0))

    def dakuten(self, cx, cy, scale=1.0):
        ws = self.Ws
        d = (100 + 0.36 * ws) * scale           # distance between the ticks
        hl = (46 + 0.04 * ws) * scale           # half length of a tick
        w = 0.98 - 0.12 * self._ramp()          # lighter at Black: keeps the pair open
        ang = math.radians(-60)                 # ticks run down-right
        ux, uy = math.cos(ang), math.sin(ang)
        for sgn in (-1, 1):
            ex, ey = cx + sgn * d / 2 / self.ax, cy + sgn * 6 / self.ay
            self.L(ex - ux * hl / self.ax, ey - uy * hl / self.ay,
                   ex + ux * hl / self.ax, ey + uy * hl / self.ay, w=w)

    def handakuten(self, cx, cy, scale=1.0):
        w = 0.93 - 0.15 * self._ramp()
        r = (36 + 0.36 * self.Ws * w) * scale
        self.ring(cx, cy, r / self.ax, r / self.ay, w=w)

    def mark(self, kind, cx, cy, scale=1.0):
        """Voicing mark centred on design-grid point (cx, cy)."""
        if kind == "d":
            self.dakuten(cx, cy, scale)
        elif kind == "h":
            self.handakuten(cx, cy, scale)

    def mark_em(self, kind, x, y, scale=1.0):
        """Voicing mark centred on em point (x, y)."""
        self.mark(kind, (x - self.ox) / self.ax, (y - self.oy) / self.ay, scale)


def mark_centre(g, mono_off=0.0):
    """Default em centre of the voicing mark on a full-size kana: upper
    right corner of the kana box; drifts slightly inwards / up with weight
    (the base ink grows inwards from its box, the mark ink grows around
    its centre)."""
    ws = g.W * wfactor(g)
    return (822.0 - 0.25 * (ws - 70.0) + mono_off, 744.0)
