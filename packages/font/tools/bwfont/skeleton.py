"""Glyph drawing DSL.

Glyphs are Python functions that receive a `G` (glyph builder) and draw
*skeletons*: centre-lines that the stroker expands with the family pen.

Coordinates are font units (UPM 1000).  Useful attributes on `G`:

    g.W, g.H     vertical-stem and horizontal-bar thickness for this master
    g.hw, g.hh   half of the above (pen radii)
    g.xh, g.cap, g.asc, g.desc   vertical metrics
    g.ov         overshoot for round shapes
    g.mono       True when building Bloxwap Mono

Most helpers take *outer* (ink) coordinates and inset the skeleton by the pen
radius themselves, so a stem drawn with `g.stem(x, 0, g.xh)` has its ink
sitting exactly on the baseline and x-height.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .geometry import Seg, Stroke, stroke_outline, Plan, Contour, KAPPA


# Curve smoothness. Glyph code writes tensions on the old squarish scale (0.58-0.62);
# soften() pulls anything above a circular quarter toward it, so every bowl, arch and
# shoulder reads round and smooth (Nunito-like) without touching each glyph. Tensions
# at or below CIRCLE_K (deliberately loose curves, necks, tails) pass through unchanged.
CIRCLE_K = 0.552
SQUARENESS = 0.15            # share of the extra squareness kept (1.0 = the old look)


def soften(k):
    return k if k <= CIRCLE_K else CIRCLE_K + (k - CIRCLE_K) * SQUARENESS


def circle(cx, cy, r, ry=None):
    """Counter-clockwise circle contour (PostScript orientation)."""
    ry = r if ry is None else ry
    k = KAPPA
    c = Contour((cx + r, cy))
    c.ops.append(("curve", (cx + r, cy + ry * k), (cx + r * k, cy + ry), (cx, cy + ry)))
    c.ops.append(("curve", (cx - r * k, cy + ry), (cx - r, cy + ry * k), (cx - r, cy)))
    c.ops.append(("curve", (cx - r, cy - ry * k), (cx - r * k, cy - ry), (cx, cy - ry)))
    c.ops.append(("curve", (cx + r * k, cy - ry), (cx + r, cy - ry * k), (cx + r, cy)))
    return c

# ---------------------------------------------------------------------------
# parameters
# ---------------------------------------------------------------------------

REG_W = 84.0


@dataclass
class Params:
    W: float = REG_W
    H: float = 74.0
    xh: float = 540.0
    cap: float = 720.0
    asc: float = 760.0
    desc: float = -210.0
    ov: float = 10.0
    slant: float = 0.0          # degrees, positive leans right
    mono: bool = False
    mono_adv: float = 600.0
    family: str = "sans"

    @property
    def grow(self):
        """How much heavier than Regular this master is, in stem units."""
        return self.W - REG_W


def params_for(family: str, stem: float, slant: float = 0.0) -> Params:
    # horizontal contrast grows slightly with weight
    H = 2.74 + 0.802 * stem
    p = Params(W=stem, H=H, slant=slant, family=family)
    if family == "mono":
        p.mono = True
    return p


# ---------------------------------------------------------------------------
# glyph registry
# ---------------------------------------------------------------------------

@dataclass
class GlyphDef:
    name: str
    unicodes: tuple
    func: object
    kind: str = "base"        # 'base', 'mark', 'space'
    zone: str = "auto"        # spacing zone: 'lc', 'uc', 'fig', 'auto'
    families: tuple = ("sans", "mono")
    pack: str = "core"        # script pack (see families.py)


GLYPHS: dict[str, GlyphDef] = {}


def glyph(name, *unicodes, kind="base", zone="auto", families=("sans", "mono"), pack="core"):
    def deco(f):
        GLYPHS[name] = GlyphDef(name, tuple(unicodes), f, kind, zone, families, pack)
        return f
    return deco


# ---------------------------------------------------------------------------
# path builder
# ---------------------------------------------------------------------------

class P:
    """Smooth skeleton path builder (one stroke).  Tangent continuity at
    joins is the caller's responsibility: corners must be separate strokes.

    Methods return self so paths can be chained:
        g.pen(x, y).h(x2, y2).v(x3, y3).end()
    """

    def __init__(self, g, x, y, w=1.0):
        self.g = g
        self.segs = []
        self.widths = [w]
        self.cur = (x, y)
        self.start = (x, y)

    # straight segment
    def l(self, x, y, w=None):
        self.segs.append(Seg("line", (self.cur, (x, y))))
        self._w(w)
        self.cur = (x, y)
        return self

    # raw cubic
    def c(self, c1, c2, p, w=None):
        self.segs.append(Seg("cubic", (self.cur, tuple(c1), tuple(c2), tuple(p))))
        self._w(w)
        self.cur = tuple(p)
        return self

    def h(self, x, y, k=None, w=None, k2=None):
        """Quarter curve leaving horizontally, arriving vertically."""
        k = soften(self.g.k if k is None else k)
        k2 = k if k2 is None else soften(k2)
        x0, y0 = self.cur
        return self.c((x0 + (x - x0) * k, y0), (x, y + (y0 - y) * k2), (x, y), w)

    def v(self, x, y, k=None, w=None, k2=None):
        """Quarter curve leaving vertically, arriving horizontally."""
        k = soften(self.g.k if k is None else k)
        k2 = k if k2 is None else soften(k2)
        x0, y0 = self.cur
        return self.c((x0, y0 + (y - y0) * k), (x + (x0 - x) * k2, y), (x, y), w)

    def to(self, x, y, d0, d1, k=None, w=None, k2=None):
        """General curve with given unit tangent directions at both ends.
        Handle lengths are k * chord-projected distances."""
        k = soften(self.g.k if k is None else k)
        k2 = k if k2 is None else soften(k2)
        x0, y0 = self.cur
        dx, dy = x - x0, y - y0
        chord = math.hypot(dx, dy)
        a = _unit(d0)
        b = _unit(d1)
        # solve for the corner where the tangents meet; fall back to chord
        den = a[0] * b[1] - a[1] * b[0]
        if abs(den) > 1e-6:
            s = (dx * b[1] - dy * b[0]) / den
            t = (dx * a[1] - dy * a[0]) / den
            l0 = abs(s) * k
            l1 = abs(t) * k2
        else:
            l0 = l1 = chord * 0.36
        return self.c((x0 + a[0] * l0, y0 + a[1] * l0), (x - b[0] * l1, y - b[1] * l1), (x, y), w)

    def _w(self, w):
        self.widths.append(self.widths[-1] if w is None else w)

    def end(self, caps=("round", "round"), scale=1.0, taper="smooth"):
        if isinstance(caps, str):
            caps = (caps, caps)
        self.g._add(Stroke(self.segs, self.widths, False, caps, scale, taper))
        return self.g

    def close(self, scale=1.0):
        if math.hypot(self.cur[0] - self.start[0], self.cur[1] - self.start[1]) > 1e-6:
            self.l(*self.start)
        self.widths[-1] = self.widths[0]
        self.g._add(Stroke(self.segs, self.widths, True, ("round", "round"), scale))
        return self.g


def _span(a, b, minimum=1.0):
    """Keep a skeleton span pointing forward: when the ink box is smaller
    than the pen (heavy weights) the stroke collapses to a dot instead of
    turning inside out (which would flip its winding)."""
    if b - a >= minimum:
        return a, b
    m = (a + b) / 2
    return m - minimum / 2, m + minimum / 2


def _unit(d):
    if isinstance(d, str):
        return {"r": (1, 0), "l": (-1, 0), "u": (0, 1), "d": (0, -1)}[d]
    m = math.hypot(*d)
    return (d[0] / m, d[1] / m)


# ---------------------------------------------------------------------------
# glyph builder
# ---------------------------------------------------------------------------

class G:
    def __init__(self, params: Params, name: str):
        self.p = params
        self.name = name
        self.W = params.W
        self.H = params.H
        self.hw = params.W / 2
        self.hh = params.H / 2
        self.xh = params.xh
        self.cap = params.cap
        self.asc = params.asc
        self.desc = params.desc
        self.ov = params.ov
        self.mono = params.mono
        self.grow = params.grow
        self.k = 0.58                 # default curve tension (softened, see soften())
        self.strokes = []             # skeleton strokes in design space
        self.extra = []               # pre-built contours (e.g. dots, pixels)
        self.anchors = {}
        self.components = []          # (glyph name, (dx, dy), scale)
        self.advance = None           # fixed advance (else auto spacing)
        self.lsb = None
        self.rsb = None
        self.sb = {}                  # spacing hints
        self.zone = None
        self.fixed = False            # True: keep drawn position, fixed advance, no auto-spacing
        self._tx = None               # transform applied to new strokes

    # -- registration -----------------------------------------------------
    def _add(self, stroke: Stroke):
        if self._tx is not None:
            stroke = _transform_stroke(stroke, self._tx)
        self.strokes.append(stroke)

    # -- metrics helpers --------------------------------------------------
    def wd(self, sans, mono=None, grow=0.5):
        """Body width.  Grows with weight; in Mono uses `mono` (or a squeeze
        of the sans width into the cell)."""
        if self.mono:
            if mono is None:
                mono = min(sans, 468)
            return mono + self.grow * 0.25
        return sans + self.grow * grow

    # -- primitives -------------------------------------------------------
    def pen(self, x, y, w=1.0):
        return P(self, x, y, w)

    def line(self, x0, y0, x1, y1, w0=1.0, w1=None, caps=("round", "round"), scale=1.0):
        w1 = w0 if w1 is None else w1
        return self.pen(x0, y0, w0).l(x1, y1, w1).end(caps, scale)

    def stem(self, x, y0, y1, w=1.0, caps=("round", "round"), scale=1.0):
        """Vertical stem whose *ink* spans y0..y1 and whose *left ink edge*
        is at x (so x..x+W)."""
        r = self.hh * w * scale
        cx = x + self.hw * w * scale
        a, b = _span(y0 + r, y1 - r)
        return self.line(cx, a, cx, b, w, w, caps, scale)

    def vstem(self, cx, y0, y1, w=1.0, caps=("round", "round"), scale=1.0):
        """Vertical stem centred on cx with ink spanning y0..y1."""
        r = self.hh * w * scale
        a, b = _span(y0 + r, y1 - r)
        return self.line(cx, a, cx, b, w, w, caps, scale)

    def bar(self, x0, x1, y, w=1.0, caps=("round", "round"), scale=1.0):
        """Horizontal bar whose ink spans x0..x1, centred on y."""
        r = self.hw * w * scale
        a, b = _span(x0 + r, x1 - r)
        return self.line(a, y, b, y, w, w, caps, scale)

    def hbar(self, x0, x1, cy, w=1.0, caps=("round", "round"), scale=1.0):
        return self.bar(x0, x1, cy, w, caps, scale)

    def dot(self, cx, cy, d=None):
        """Round dot (i-dot, period).  Diameter defaults to ~1.18 stem."""
        if d is None:
            d = self.W * 1.16 + 10
        self.extra.append(circle(cx, cy, d / 2))
        return self

    def oval(self, x0, y0, x1, y1, k=None, w=1.0, ccw=True):
        """Closed oval whose *outer* ink box is x0..x1, y0..y1."""
        hx = self.hw * w
        hy = self.hh * w
        return self.ovalc(x0 + hx, y0 + hy, x1 - hx, y1 - hy, k, w, ccw)

    def ovalc(self, x0, y0, x1, y1, k=None, w=1.0, ccw=True):
        """Closed oval on skeleton box (centre-line coordinates)."""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        p = self.pen(cx, y1, w)
        if ccw:
            p.h(x0, cy, k).v(cx, y0, k).h(x1, cy, k).v(cx, y1, k)
        else:
            p.h(x1, cy, k).v(cx, y0, k).h(x0, cy, k).v(cx, y1, k)
        return p.close()

    # -- reuse ------------------------------------------------------------
    def transform(self, fn):
        """Context manager-ish: g.transform(fn) then draw, then g.transform(None)."""
        self._tx = fn
        return self

    def include(self, name, fn=None):
        """Draw another glyph's skeleton into this one (optionally transformed)."""
        sub = G(self.p, name)
        GLYPHS[name].func(sub)
        for s in sub.strokes:
            self.strokes.append(_transform_stroke(s, fn) if fn else s)
        self.extra += [c.transform(fn) for c in sub.extra] if fn else sub.extra
        return sub

    def anchor(self, name, x, y):
        self.anchors[name] = (x, y)


def derive(name, *unicodes, src, sx=1.0, sy=None, dx=0.0, dy=0.0, wscale=1.0, kind="base",
           zone="auto", families=("sans", "mono"), post=None, pack=None):
    """Register a glyph made by transforming another glyph's *skeleton*.
    Stroke weight is re-applied after the transform (times `wscale`), so
    scaled glyphs (small caps, superiors, ...) keep a consistent colour.
    sx/sy/dx/dy may be numbers or callables of the builder `g`."""
    sy_ = sx if sy is None else sy

    def f(g: G):
        sub = G(g.p, src)
        GLYPHS[src].func(sub)
        val = lambda v: v(g) if callable(v) else v
        a, b, c, d = val(sx), val(sy_), val(dx), val(dy)
        T = lambda p: (p[0] * a + c, p[1] * b + d)
        for st in sub.strokes:
            s2 = _transform_stroke(st, T)
            s2.scale *= val(wscale)
            g.strokes.append(s2)
        for cn in sub.extra:
            # dots: move centre, scale size by the weight factor too
            pts = list(cn.points())
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            k = (a + b) / 2 * 0.5 + val(wscale) * 0.5
            nc = T((cx, cy))
            g.extra.append(cn.transform(lambda p: (nc[0] + (p[0] - cx) * k, nc[1] + (p[1] - cy) * k)))
        g.anchors = {kk: T(v) for kk, v in sub.anchors.items()}
        g.advance = sub.advance
        if post:
            post(g)
    import sys as _sys
    f.__module__ = _sys._getframe(1).f_globals.get("__name__", f.__module__)
    if pack is None:
        pack = GLYPHS[src].pack if src in GLYPHS else "core"
    GLYPHS[name] = GlyphDef(name, tuple(unicodes), f, kind, zone, families, pack)
    return f


def _unfold(s: Stroke) -> Stroke:
    """Clamp straight segments that would run *backwards* against their
    smooth neighbour (e.g. a t/f/j tail whose finishing line gets shorter
    than zero at heavy weights).  The line keeps a tiny forward length, so
    the cap lands where the curve ends; topology is unchanged."""
    from .geometry import start_tangent, end_tangent
    segs = [Seg(sg.kind, tuple(sg.pts)) for sg in s.segs]
    n = len(segs)
    for i, sg in enumerate(segs):
        if sg.kind != "line":
            continue
        p0, p1 = sg.pts
        v = (p1[0] - p0[0], p1[1] - p0[1])
        if i > 0:
            prev = segs[i - 1]
            d = end_tangent(*prev.pts) if prev.kind == "cubic" else _unit2(prev.pts[0], prev.pts[1])
            proj = v[0] * d[0] + v[1] * d[1]
            if d != (0.0, 0.0) and proj < 1.0:
                q = (p0[0] + d[0] * 1.0, p0[1] + d[1] * 1.0)
                segs[i] = Seg("line", (p0, q))
                if i + 1 < n:
                    nx = segs[i + 1]
                    dx, dy = q[0] - p1[0], q[1] - p1[1]
                    pts = list(nx.pts)
                    pts[0] = q
                    if nx.kind == "cubic":
                        pts[1] = (pts[1][0] + dx, pts[1][1] + dy)
                    segs[i + 1] = Seg(nx.kind, tuple(pts))
                continue
        if i + 1 < n and i == 0:
            nxt = segs[i + 1]
            d = start_tangent(*nxt.pts) if nxt.kind == "cubic" else _unit2(nxt.pts[0], nxt.pts[1])
            proj = v[0] * d[0] + v[1] * d[1]
            if d != (0.0, 0.0) and proj < 1.0:
                segs[i] = Seg("line", ((p1[0] - d[0] * 1.0, p1[1] - d[1] * 1.0), p1))
    return Stroke(segs, list(s.widths), s.closed, s.caps, s.scale, s.taper)


def _unit2(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    m = math.hypot(dx, dy)
    return (dx / m, dy / m) if m > 1e-9 else (0.0, 0.0)


def _transform_stroke(s: Stroke, fn):
    segs = [Seg(sg.kind, tuple(fn(p) for p in sg.pts)) for sg in s.segs]
    return Stroke(segs, list(s.widths), s.closed, s.caps, s.scale, s.taper)


def mirror_x(cx):
    return lambda p: (2 * cx - p[0], p[1])


def mirror_y(cy):
    return lambda p: (p[0], 2 * cy - p[1])


def shift(dx, dy=0):
    return lambda p: (p[0] + dx, p[1] + dy)


def scale_about(sx, sy, ox=0, oy=0):
    return lambda p: (ox + (p[0] - ox) * sx, oy + (p[1] - oy) * sy)


# ---------------------------------------------------------------------------
# rendering skeletons to outlines
# ---------------------------------------------------------------------------

def outline(g: G, plan: Plan, key: str):
    """Expand all strokes of `g` into contours in design space."""
    p = g.p
    ratio = p.W / p.H              # y-stretch that makes the pen circular
    R = p.W / 2
    sk = math.tan(math.radians(p.slant))
    yc = p.xh / 2

    def fwd(pt):
        x, y = pt
        x = x + (y - yc) * sk
        return (x, y * ratio)

    def back(pt):
        return (pt[0], pt[1] / ratio)

    out = []
    for i, s in enumerate(g.strokes):
        plan.begin((key, i))
        ss = _transform_stroke(_unfold(s), fwd)
        cs = [c.transform(back) for c in stroke_outline(ss, R, plan)]
        flips = plan.get(lambda: ("orient", _orient_flags(cs, s.closed)))[1]
        out += [c.reversed() if f else c for c, f in zip(cs, flips)]
    for c in g.extra:
        out.append(c.transform(lambda pt: (pt[0] + (pt[1] - yc) * sk, pt[1])))
    return out


def _area(c):
    from .geometry import flatten
    pts = flatten(c, 6)
    a = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        a += x0 * y1 - x1 * y0
    return a / 2


def _orient_flags(cs, closed):
    """Every stroke must fill with the same winding sign (PostScript: outer
    counter-clockwise) or overlapping strokes would cancel out.  Mirrored
    skeletons produce clockwise outlines.  Returns per-contour reverse flags
    (decided once at the reference master, replayed via the plan)."""
    if not cs:
        return ()
    if not closed or len(cs) == 1:
        return tuple(_area(c) < 0 for c in cs)
    areas = [_area(c) for c in cs]
    outer = max(range(len(cs)), key=lambda i: abs(areas[i]))
    return tuple((a >= 0) != (i == outer) for i, a in enumerate(areas))


def skew_point(p: Params, pt):
    sk = math.tan(math.radians(p.slant))
    return (pt[0] + (pt[1] - p.xh / 2) * sk, pt[1])
