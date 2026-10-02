"""Bezier math and the skeleton stroker.

Every Bloxwap glyph is drawn as a skeleton (centre-line) and expanded here
with an elliptical pen.  The stroker is deliberately *structural*: the number
of output points depends only on the skeleton topology and a split plan that
is recorded once (at a reference weight) and replayed for every master, so
all masters are point-compatible and interpolate cleanly in variable fonts.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

KAPPA = 0.5522847498


# --------------------------------------------------------------------------
# vector helpers
# --------------------------------------------------------------------------

def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def length(v):
    return math.hypot(v[0], v[1])


def norm(v):
    d = math.hypot(v[0], v[1])
    if d < 1e-12:
        return (0.0, 0.0)
    return (v[0] / d, v[1] / d)


def left(v):
    """Left-hand normal of a direction (y-up)."""
    return (-v[1], v[0])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def intersect(p, d, q, e):
    """Intersection of line p + s*d with q + t*e, or None when parallel."""
    den = cross(d, e)
    if abs(den) < 1e-9:
        return None
    s = cross(sub(q, p), e) / den
    return add(p, mul(d, s))


# --------------------------------------------------------------------------
# cubic helpers
# --------------------------------------------------------------------------

def cubic_point(p0, p1, p2, p3, t):
    mt = 1 - t
    a = mt * mt * mt
    b = 3 * mt * mt * t
    c = 3 * mt * t * t
    d = t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def cubic_split(p0, p1, p2, p3, t):
    a = lerp(p0, p1, t)
    b = lerp(p1, p2, t)
    c = lerp(p2, p3, t)
    d = lerp(a, b, t)
    e = lerp(b, c, t)
    f = lerp(d, e, t)
    return (p0, a, d, f), (f, e, c, p3)


def cubic_split_n(seg, n):
    """Split a cubic into n pieces of equal parameter length."""
    out = []
    rest = seg
    for i in range(n, 1, -1):
        a, rest = cubic_split(*rest, 1.0 / i)
        out.append(a)
    out.append(rest)
    return out


def start_tangent(p0, p1, p2, p3):
    for q in (p1, p2, p3):
        d = sub(q, p0)
        if length(d) > 1e-6:
            return norm(d)
    return (1.0, 0.0)


def end_tangent(p0, p1, p2, p3):
    for q in (p2, p1, p0):
        d = sub(p3, q)
        if length(d) > 1e-6:
            return norm(d)
    return (1.0, 0.0)


def turning(seg):
    a = start_tangent(*seg)
    b = end_tangent(*seg)
    ang = abs(math.atan2(cross(a, b), dot(a, b)))
    # also account for curves that swing out and back
    p0, p1, p2, p3 = seg
    legs = [sub(p1, p0), sub(p2, p1), sub(p3, p2)]
    legs = [norm(v) for v in legs if length(v) > 1e-6]
    total = 0.0
    for u, v in zip(legs, legs[1:]):
        total += abs(math.atan2(cross(u, v), dot(u, v)))
    return max(ang, total)


# --------------------------------------------------------------------------
# skeleton representation
# --------------------------------------------------------------------------

@dataclass
class Seg:
    kind: str            # 'line' or 'cubic'
    pts: tuple           # (p0, p1) or (p0, c1, c2, p1)


@dataclass
class Stroke:
    segs: list
    widths: list         # width factor per node (len(segs)+1)
    closed: bool = False
    caps: tuple = ("round", "round")
    scale: float = 1.0   # overall width factor for this stroke
    taper: str = "smooth"  # how width interpolates along a segment


@dataclass
class Contour:
    """Output contour: list of ('line', p) / ('curve', c1, c2, p); starts at start."""
    start: tuple
    ops: list = field(default_factory=list)
    closes: bool = True   # last op returns to start (structural, not measured)

    def transform(self, f):
        c = Contour(f(self.start), closes=self.closes)
        for op in self.ops:
            c.ops.append((op[0],) + tuple(f(p) for p in op[1:]))
        return c

    def reversed(self):
        pts = [self.start]
        for op in self.ops:
            pts.append(op[-1])
        ops = []
        for i in range(len(self.ops) - 1, -1, -1):
            op = self.ops[i]
            dest = pts[i]
            if op[0] == "line":
                ops.append(("line", dest))
            else:
                ops.append(("curve", op[2], op[1], dest))
        return Contour(pts[-1], ops, self.closes)

    def points(self):
        yield self.start
        for op in self.ops:
            yield from op[1:]

    def draw(self, pen):
        pen.moveTo(self.start)
        n = len(self.ops)
        for i, op in enumerate(self.ops):
            last = i == n - 1
            if op[0] == "line":
                if last and self.closes:
                    continue
                pen.lineTo(op[1])
            else:
                if last and self.closes:
                    pen.curveTo(op[1], op[2], self.start)
                else:
                    pen.curveTo(op[1], op[2], op[3])
        pen.closePath()


def _close(a, b):
    return abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6


# --------------------------------------------------------------------------
# offsetting
# --------------------------------------------------------------------------

def _smooth(t):
    return t * t * (3 - 2 * t)


def _offset_line(p0, p1, r0, r1, sign):
    d = norm(sub(p1, p0))
    n = mul(left(d), sign)
    return [("line", add(p0, mul(n, r0)), add(p1, mul(n, r1)))]


def _offset_cubic(seg, r0, r1, sign, flags):
    """Tiller-Hanson offset of one cubic piece.  `flags` is the recorded
    degeneracy plan so the result is structurally weight-independent."""
    p0, p1, p2, p3 = seg
    d1 = start_tangent(*seg)
    d3 = end_tangent(*seg)
    n1 = mul(left(d1), sign)
    n3 = mul(left(d3), sign)
    rm = (r0 + r1) / 2
    q0 = add(p0, mul(n1, r0))
    q3 = add(p3, mul(n3, r1))
    mid_ok = flags
    if mid_ok:
        d2 = norm(sub(p2, p1))
        n2 = mul(left(d2), sign)
        a = intersect(add(p0, mul(n1, r0)), d1, add(p1, mul(n2, rm)), d2)
        b = intersect(add(p2, mul(n2, rm)), d2, add(p3, mul(n3, r1)), d3)
    else:
        a = b = None
    if a is None:
        a = add(p1, mul(n1, r0))
    if b is None:
        b = add(p2, mul(n3, r1))
    return [("curve", q0, a, b, q3)]


def _mid_ok(seg):
    p0, p1, p2, p3 = seg
    d1 = start_tangent(*seg)
    d3 = end_tangent(*seg)
    if length(sub(p2, p1)) < 1.0:
        return False
    d2 = norm(sub(p2, p1))
    if abs(cross(d1, d2)) < 0.02 or abs(cross(d2, d3)) < 0.02:
        return False
    return True


class Plan:
    """Records structural decisions on the first (reference) pass and replays
    them afterwards."""

    def __init__(self):
        self.data = {}
        self.recording = True
        self.cursor = 0
        self.key = None

    def begin(self, key):
        self.key = key
        self.cursor = 0
        if key not in self.data:
            self.data[key] = []
            self._rec = True
        else:
            self._rec = False

    def get(self, compute):
        lst = self.data[self.key]
        if self._rec:
            v = compute()
            lst.append(v)
            return v
        if self.cursor >= len(lst):
            raise RuntimeError(f"incompatible skeleton for {self.key}")
        v = lst[self.cursor]
        self.cursor += 1
        return v


def _pieces(stroke: Stroke, plan: Plan):
    """Yield (kind, pts, r0f, r1f) pieces with width factors."""
    n = len(stroke.segs)
    for i, s in enumerate(stroke.segs):
        w0 = stroke.widths[i]
        w1 = stroke.widths[i + 1]
        if s.kind == "line":
            plan.get(lambda: ("line",))
            yield ("line", s.pts, w0, w1)
            continue
        k = plan.get(lambda: ("cubic", max(1, math.ceil(turning(s.pts) / math.radians(32) - 1e-6))))[1]
        parts = cubic_split_n(s.pts, k)
        for j, part in enumerate(parts):
            t0 = j / k
            t1 = (j + 1) / k
            if stroke.taper == "smooth":
                a = w0 + (w1 - w0) * _smooth(t0)
                b = w0 + (w1 - w0) * _smooth(t1)
            else:
                a = w0 + (w1 - w0) * t0
                b = w0 + (w1 - w0) * t1
            flags = plan.get(lambda: ("mid", _mid_ok(part)))[1]
            yield ("cubic", part, a, b, flags)


def _side(pieces, R, sign):
    out = []
    for pc in pieces:
        if pc[0] == "line":
            out += _offset_line(pc[1][0], pc[1][1], R * pc[2], R * pc[3], sign)
        else:
            out += _offset_cubic(pc[1], R * pc[2], R * pc[3], sign, pc[4])
    return out


def _chain(contour: Contour, segs):
    """Append offset segments to contour.  Consecutive pieces are *snapped*
    together (shared point = midpoint) rather than bridged with lines, so the
    point structure never depends on geometry."""
    for s in segs:
        start = s[1]
        if contour.ops:
            _move_end(contour, lerp(contour_end(contour), start, 0.5))
        else:
            contour.start = start
        if s[0] == "line":
            contour.ops.append(("line", s[2]))
        else:
            contour.ops.append(("curve", s[2], s[3], s[4]))


def _move_end(contour: Contour, p):
    """Move the current end point (and its incoming handle) to p."""
    op = contour.ops[-1]
    if op[0] == "line":
        contour.ops[-1] = ("line", p)
    else:
        d = sub(p, op[3])
        contour.ops[-1] = ("curve", op[1], add(op[2], d), p)


def contour_end(c: Contour):
    if not c.ops:
        return c.start
    return c.ops[-1][-1]


def _rev_segs(segs):
    out = []
    for s in reversed(segs):
        if s[0] == "line":
            out.append(("line", s[2], s[1]))
        else:
            out.append(("curve", s[4], s[3], s[2], s[1]))
    return out


def _cap(contour, center, tangent, r, kind):
    """Cap from current point (center - r*n) around to (center + r*n) where
    n is the left normal of `tangent` (pointing direction of the cap)."""
    n = left(tangent)
    a = sub(center, mul(n, r))
    tip = add(center, mul(tangent, r))
    b = add(center, mul(n, r))
    _move_end(contour, a)
    if kind == "round":
        k = KAPPA * r
        contour.ops.append(("curve", add(a, mul(tangent, k)), sub(tip, mul(n, k)), tip))
        contour.ops.append(("curve", add(tip, mul(n, k)), add(b, mul(tangent, k)), b))
    else:
        contour.ops.append(("line", b))


SMOOTH_JOIN = math.radians(25)   # joints bending less than this are meant to be smooth


def _g1(contour: Contour):
    """Make every near-smooth joint exactly smooth (G1).  The offset pieces of a
    stroke side are snapped together at shared points, which leaves a small kink
    in the tangent at each one; at small sizes those kinks read as faceting.
    Handles are rotated about their on-curve point (lengths kept), so the point
    structure never changes and masters stay compatible.  Real corners (butt caps,
    cap/side junctions) bend far more than SMOOTH_JOIN and are left alone."""
    ops = contour.ops
    n = len(ops)
    if n < 2:
        return

    def end_pt(i):
        return contour.start if i < 0 else ops[i][-1]

    joints = range(n - 1) if not contour.closes else range(n)
    for i in joints:
        j = (i + 1) % n
        a, b = ops[i], ops[j]
        p = ops[i][-1]
        prev_pt = end_pt(i - 1) if i > 0 else contour.start
        # incoming tangent (into p) and outgoing tangent (out of p)
        if a[0] == "curve":
            hin = a[2]
            tin = sub(p, hin)
            if length(tin) < 1e-6:
                tin = sub(p, a[1])
        else:
            hin = None
            tin = sub(p, prev_pt)
        if b[0] == "curve":
            hout = b[1]
            tout = sub(hout, p)
            if length(tout) < 1e-6:
                tout = sub(b[2], p)
        else:
            hout = None
            tout = sub(b[1], p)
        if length(tin) < 1e-6 or length(tout) < 1e-6:
            continue
        u, v = norm(tin), norm(tout)
        ang = math.atan2(abs(cross(u, v)), dot(u, v))
        if ang < 1e-9 or ang > SMOOTH_JOIN:
            continue
        if a[0] == "line" and b[0] == "line":
            continue
        if a[0] == "line":
            d = u                      # keep the straight side, turn the handle
        elif b[0] == "line":
            d = v
        else:
            d = norm(add(u, v))
        if hin is not None:
            ops[i] = ("curve", a[1], sub(p, mul(d, length(sub(p, hin)))), p)
        if hout is not None:
            b = ops[j]
            ops[j] = ("curve", add(p, mul(d, length(sub(hout, p)))), b[2], b[3])


def stroke_outline(stroke: Stroke, R: float, plan: Plan):
    """Expand a skeleton stroke (already in pen space, circular pen of
    radius R) into one or two contours (PostScript orientation)."""
    R = R * stroke.scale
    pieces = list(_pieces(stroke, plan))
    if not pieces:
        return []
    right = _side(pieces, R, -1.0)
    leftside = _side(pieces, R, 1.0)

    if stroke.closed:
        out = []
        for segs in (right, _rev_segs(leftside)):
            c = Contour(segs[0][1])
            _chain(c, segs)
            # close: snap last end and first start together
            m = lerp(contour_end(c), c.start, 0.5)
            _move_end(c, m)
            first = c.ops[0]
            if first[0] == "curve":
                d = sub(m, c.start)
                c.ops[0] = ("curve", add(first[1], d), first[2], first[3])
            c.start = m
            _g1(c)
            out.append(c)
        return out

    first = pieces[0]
    last = pieces[-1]
    p_start = first[1][0]
    p_end = last[1][-1]
    t_start = start_tangent(*first[1]) if first[0] == "cubic" else norm(sub(first[1][1], first[1][0]))
    t_end = end_tangent(*last[1]) if last[0] == "cubic" else norm(sub(last[1][1], last[1][0]))
    r_start = R * first[2]
    r_end = R * last[3]

    c = Contour(right[0][1])
    _chain(c, right)
    _cap(c, p_end, t_end, r_end, stroke.caps[1])
    _chain(c, _rev_segs(leftside))
    _cap(c, p_start, mul(t_start, -1), r_start, stroke.caps[0])
    # the start cap ends exactly where the contour starts
    _move_end(c, c.start)
    _g1(c)
    return [c]


# --------------------------------------------------------------------------
# flattening (for measurement / previews)
# --------------------------------------------------------------------------

def flatten(contour: Contour, steps=12):
    pts = [contour.start]
    cur = contour.start
    for op in contour.ops:
        if op[0] == "line":
            pts.append(op[1])
            cur = op[1]
        else:
            for i in range(1, steps + 1):
                pts.append(cubic_point(cur, op[1], op[2], op[3], i / steps))
            cur = op[3]
    return pts
