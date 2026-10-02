"""Pixel outlines.

Every "on" pixel is its own closed contour: a rounded rectangle with exactly
8 on-curve points (4 straight sides + 4 cubic corner arcs).  Radius 0 still
emits all points (degenerate arcs), so every master is point-compatible and
the variable font interpolates (size along `wght`, radius along `ROND`).
"""
from __future__ import annotations

import math

from ..geometry import Contour
from .art import CELL

K = 0.5522847498

# ---- italic: rows step right by half a pixel every two rows ---------------
ITALIC_STEP = 50          # units per step (half a pixel)
ITALIC_ROWS = 2           # rows per step
ITALIC_BIAS = -50         # keeps the x-height band centred in the cell
ITALIC_ANGLE = math.degrees(math.atan(ITALIC_STEP / (ITALIC_ROWS * CELL)))


def italic_dx(row: int) -> int:
    return ITALIC_STEP * math.floor(row / ITALIC_ROWS) + ITALIC_BIAS


def _r(v):
    return round(v)


def rrect(x0, y0, x1, y1, r):
    """Rounded rectangle, counter-clockwise (PostScript outer direction)."""
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    k = r * (1 - K)       # distance of handles from the corner
    p = _r
    c = Contour((p(x0 + r), p(y0)))
    c.ops = [
        ("line", (p(x1 - r), p(y0))),
        ("curve", (p(x1 - k), p(y0)), (p(x1), p(y0 + k)), (p(x1), p(y0 + r))),
        ("line", (p(x1), p(y1 - r))),
        ("curve", (p(x1), p(y1 - k)), (p(x1 - k), p(y1)), (p(x1 - r), p(y1))),
        ("line", (p(x0 + r), p(y1))),
        ("curve", (p(x0 + k), p(y1)), (p(x0), p(y1 - k)), (p(x0), p(y1 - r))),
        ("line", (p(x0), p(y0 + r))),
        ("curve", (p(x0), p(y0 + k)), (p(x0 + k), p(y0)), (p(x0 + r), p(y0))),
    ]
    return c


def pixel(cx, cy, size, rond):
    h = size / 2
    return rrect(cx - h, cy - h, cx + h, cy + h, rond * h)


def poly(points):
    """Closed polygon (counter-clockwise expected)."""
    c = Contour((_r(points[0][0]), _r(points[0][1])))
    for x, y in points[1:]:
        c.ops.append(("line", (_r(x), _r(y))))
    c.ops.append(("line", (_r(points[0][0]), _r(points[0][1]))))
    return c


def ring_sector(cx, cy, r_out, r_in, a0, a1):
    """Quarter-ring between angles a0→a1 (degrees, multiples of 90, a1=a0+90)."""
    def pt(r, a):
        return (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))

    def arc(r, a, b):
        p0, p3 = pt(r, a), pt(r, b)
        s = 1 if b > a else -1
        t0 = (-math.sin(math.radians(a)) * s, math.cos(math.radians(a)) * s)
        t1 = (-math.sin(math.radians(b)) * s, math.cos(math.radians(b)) * s)
        h = r * K
        return (p0[0] + t0[0] * h, p0[1] + t0[1] * h), (p3[0] - t1[0] * h, p3[1] - t1[1] * h), p3

    p = _r
    s0 = pt(r_out, a0)
    c = Contour((p(s0[0]), p(s0[1])))
    c1, c2, e = arc(r_out, a0, a1)
    c.ops.append(("curve", (p(c1[0]), p(c1[1])), (p(c2[0]), p(c2[1])), (p(e[0]), p(e[1]))))
    i0 = pt(r_in, a1)
    c.ops.append(("line", (p(i0[0]), p(i0[1]))))
    c1, c2, e = arc(r_in, a1, a0)
    c.ops.append(("curve", (p(c1[0]), p(c1[1])), (p(c2[0]), p(c2[1])), (p(e[0]), p(e[1]))))
    c.ops.append(("line", (p(s0[0]), p(s0[1]))))
    return c
