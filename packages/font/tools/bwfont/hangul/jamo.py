"""Hangul jamo skeletons + syllable layout (Bloxwap Sans KR / Mono KR).

Design: rounded modern gothic.  Every jamo is a function of a target *ink*
box: strokes are placed so their ink (pen already applied) fills the box,
whatever the weight.  Corners are separate strokes meeting at one skeleton
point, so the round caps make the soft corners; T-junctions start on the
other stroke's centre-line (cap hidden inside it).

Syllables (U+AC00..D7A3) are composites of three positioned parts:

    ko.L.<initial>.<ctx><f>   initial, ctx = vowel layout group, f = 0/1 (final?)
    ko.V.<vowel>.<f>          medial
    ko.T.<final>.<tctx>       final, tctx = V | Ho Hu Heu | Mo Mu Meu

The layout class of a syllable comes from its vowel: vertical (ㅏ-type,
the vowel stands on the right), horizontal (ㅗ-type, the vowel lies below)
or mixed (ㅘ-type), and from whether it has a final.  Geometry tables below
are in *face* fractions (0..1 across the syllable face box FACE).

Weight: the pen scale is han.engine.cjk_weight_factor(W) so Hangul colour
matches the hanzi of the SC family; dense jamo in small boxes (ㄹ ㅎ ㅃ ...)
get an extra reduction from `density()` so strokes never collide at Black.
Topology never depends on weight.
"""
from __future__ import annotations

import math

from ..han.engine import cjk_weight_factor
from ..skeleton import G, _transform_stroke

# ink box of a full syllable; em centre is (500, 380) like the hanzi FACE
FACE = (84.0, -42.0, 916.0, 802.0)
FW = FACE[2] - FACE[0]
FH = FACE[3] - FACE[1]
EM_CY = 380.0

DIAG = 0.94       # width factor of diagonal strokes
RINGW = 0.93      # rings look heavier than straight strokes
GAPK = 0.62       # min white between stacked strokes (x stroke thickness)


def fx(u):
    return FACE[0] + u * FW


def fy(v):
    return FACE[1] + v * FH


def wf(g):
    return cjk_weight_factor(g.W)


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def _unit(x, y):
    m = math.hypot(x, y)
    return (x / m, y / m)


def _ctrl(p0, p1, d0, d1, k=0.55):
    """Cubic handles leaving p0 along d0 and arriving at p1 along d1."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    a, b = _unit(*d0), _unit(*d1)
    den = a[0] * b[1] - a[1] * b[0]
    if abs(den) > 1e-6:
        s = (dx * b[1] - dy * b[0]) / den
        t = (dx * a[1] - dy * a[0]) / den
        l0, l1 = abs(s) * k, abs(t) * k
    else:
        l0 = l1 = math.hypot(dx, dy) * 0.36
    return (p0[0] + a[0] * l0, p0[1] + a[1] * l0), (p1[0] - b[0] * l1, p1[1] - b[1] * l1)


def _bez(p0, c1, c2, p1, t):
    mt = 1 - t
    a, b, c, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
    return (a * p0[0] + b * c1[0] + c * c2[0] + d * p1[0],
            a * p0[1] + b * c1[1] + c * c2[1] + d * p1[1])


class J:
    """Drawing context: ink box + pen scale.  X(u)/Y(v) address the skeleton
    range inside the box (u=0: the ink of a vertical stroke touches the
    left edge, v=1: the ink of a horizontal stroke touches the top)."""

    def __init__(self, g, box, s):
        self.g, self.s = g, s
        self.x0, self.y0, self.x1, self.y1 = box
        self.hw = g.hw * s
        self.hh = g.hh * s

    @property
    def bw(self):
        return self.x1 - self.x0

    @property
    def bh(self):
        return self.y1 - self.y0

    def X(self, u):
        a, b = self.x0 + self.hw, self.x1 - self.hw
        if b - a < 2:
            m = (a + b) / 2
            a, b = m - 1, m + 1
        return a + u * (b - a)

    def Y(self, v):
        a, b = self.y0 + self.hh, self.y1 - self.hh
        if b - a < 2:
            m = (a + b) / 2
            a, b = m - 1, m + 1
        return a + v * (b - a)

    def sub(self, u0, v0, u1, v1):
        return J(self.g, (self.x0 + u0 * self.bw, self.y0 + v0 * self.bh,
                          self.x0 + u1 * self.bw, self.y0 + v1 * self.bh), self.s)

    def line(self, a, b, w=1.0):
        self.g.pen(a[0], a[1], w).l(b[0], b[1], w).end(scale=self.s)

    def curve(self, a, b, d0, d1, w=1.0, k=0.55):
        c1, c2 = _ctrl(a, b, d0, d1, k)
        self.g.pen(a[0], a[1], w).c(c1, c2, b, w).end(scale=self.s)
        return (a, c1, c2, b)

    def ring(self, x0, y0, x1, y1, k=0.57):
        """Closed ring whose *ink* box is x0..x1 × y0..y1."""
        a, b = x0 + self.hw * RINGW, y0 + self.hh * RINGW
        c, d = x1 - self.hw * RINGW, y1 - self.hh * RINGW
        if c - a < 4:
            m = (a + c) / 2
            a, c = m - 2, m + 2
        if d - b < 4:
            m = (b + d) / 2
            b, d = m - 2, m + 2
        cx, cy = (a + c) / 2, (b + d) / 2
        w = RINGW
        (self.g.pen(cx, d, w).h(a, cy, k).v(cx, b, k).h(c, cy, k).v(cx, d, k)
            .close(scale=self.s))

    def dot(self, cx, cy, w=1.35):
        self.g.pen(cx - 0.5, cy, w).l(cx + 0.5, cy, w).end(scale=self.s)


# ---------------------------------------------------------------------------
# consonants (each draws into the whole ink box of j)
# ---------------------------------------------------------------------------

def _legs(j, A, Lp, Rp, t=0.42, bend=0.30):
    """ㅅ-type pair of legs from apex A: the left leg to Lp, the right leg
    branching off the left one (at parameter t) to Rp.  Legs start steep and
    flatten slightly towards their ends."""
    c = _unit(Lp[0] - A[0], Lp[1] - A[1])
    d0 = _unit(c[0] * (1 - bend), c[1])
    d1 = _unit(c[0] * (1 + bend * 1.2), c[1])
    seg = j.curve(A, Lp, d0, d1, w=DIAG, k=0.5)
    P = _bez(*seg, t)
    cr = _unit(Rp[0] - P[0], Rp[1] - P[1])
    e0 = _unit(cr[0] * (1 - bend * 0.5), cr[1])
    e1 = _unit(cr[0] * (1 + bend * 0.6), cr[1])
    j.curve(P, Rp, e0, e1, w=DIAG, k=0.5)


def c_g(j, sweep=0.0, knee=None):
    """ㄱ: bar + leg.  sweep>0 bends the leg towards the lower left (가)."""
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    j.line((xl, yt), (xr, yt))
    if sweep <= 0:
        j.line((xr, yt), (xr, yb))
        return
    h, w = yt - yb, xr - xl
    kf = (0.62 - 0.22 * sweep) if knee is None else knee
    ym = yb + h * kf
    xe = xr - w * 0.50 * sweep
    c1, c2 = _ctrl((xr, ym), (xe, yb), (0, -1), _unit(-0.95 * sweep, -1), 0.6)
    j.g.pen(xr, yt).l(xr, ym).c(c1, c2, (xe, yb)).end(scale=j.s)


def c_n(j):
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    j.line((xl, yt), (xl, yb))
    j.line((xl, yb), (xr, yb))


def c_d(j):
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    j.line((xl, yt), (j.X(0.97), yt))
    j.line((xl, yt), (xl, yb))
    j.line((xl, yb), (xr, yb))


def c_r(j):
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    ym = j.Y(0.5)
    j.line((xl, yt), (xr, yt))
    j.line((xr, yt), (xr, ym))
    j.line((xr, ym), (xl, ym))
    j.line((xl, ym), (xl, yb))
    j.line((xl, yb), (xr, yb))


def c_m(j):
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    j.line((xl, yt), (xl, yb))
    j.line((xl, yt), (xr, yt))
    j.line((xr, yt), (xr, yb))
    j.line((xl, yb), (xr, yb))


def c_b(j):
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    ym = j.Y(0.47)
    j.line((xl, yt), (xl, yb))
    j.line((xr, yt), (xr, yb))
    j.line((xl, ym), (xr, ym))
    j.line((xl, yb), (xr, yb))


def _branch(j, h=None):
    """Where the right leg leaves the left one: lower in tall boxes,
    nearer the apex in wide flat ones (소 속)."""
    ar = j.bw / (j.bh if h is None else h)
    a = min(1.0, max(0.0, (ar - 0.8) / 0.6))
    return 0.42 - 0.15 * a


def c_s(j):
    _legs(j, (j.X(0.5), j.Y(1)), (j.X(0), j.Y(0)), (j.X(1), j.Y(0)), t=_branch(j))


def c_ng(j, aspect=(1.10, 1.06)):
    w = min(j.bw, j.bh * aspect[0])
    h = min(j.bh, j.bw * aspect[1])
    cx, cy = (j.x0 + j.x1) / 2, (j.y0 + j.y1) / 2
    ov = 0.012 * h
    j.ring(cx - w / 2, cy - h / 2 - ov, cx + w / 2, cy + h / 2 + ov)


def c_j(j, top=None):
    xl, xr = j.X(0), j.X(1)
    yt = j.Y(1) if top is None else top
    j.line((xl, yt), (xr, yt))
    _legs(j, (j.X(0.5), yt), (j.X(0), j.Y(0)), (j.X(1), j.Y(0)),
          t=_branch(j, yt - j.y0 + j.hh) - 0.02)


def _tick(j, frac=0.19):
    return max(frac * j.bh, 2.5 * j.hh)


def c_c(j):
    yt = j.Y(1)
    yb = yt - _tick(j)
    j.line((j.X(0.5), yt), (j.X(0.5), yb))
    c_j(j, top=yb)


def c_k(j, sweep=0.0):
    c_g(j, sweep, knee=min(0.42, 0.62 - 0.22 * sweep) if sweep > 0 else None)
    ym = j.Y(0.5)
    j.line((j.X(0), ym), (j.X(1), ym))


def c_t(j):
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    xm = j.X(0.97)
    ym = j.Y(0.5)
    j.line((xl, yt), (xm, yt))
    j.line((xl, ym), (xm, ym))
    j.line((xl, yt), (xl, yb))
    j.line((xl, yb), (xr, yb))


def c_p(j):
    xl, xr, yt, yb = j.X(0), j.X(1), j.Y(1), j.Y(0)
    j.line((j.X(0.03), yt), (j.X(0.97), yt))
    j.line((xl, yb), (xr, yb))
    for u in (0.27, 0.73):
        j.line((j.X(u), yt), (j.X(u), yb))


def c_h(j, tick=True):
    """ㅎ: tick, bar, ring.  In tall boxes (하) the ring may not become an
    upright oval: the whole letter is shortened and centred instead."""
    def parts(k):
        yt = k.Y(1)
        ybar = yt - max(0.15 * k.bh, 2.1 * k.hh) if tick else yt
        top = ybar - k.hh - (0.055 * k.bh + 3)
        rw = min(k.bw * 0.76, (top - k.y0) * 1.32)
        return yt, ybar, top, rw
    yt, ybar, top, rw = parts(j)
    excess = (top - j.y0) - rw * 1.04
    if excess > 0:
        k = J(j.g, (j.x0, j.y0 + excess * 0.45, j.x1, j.y1 - excess * 0.55), j.s)
        yt, ybar, top, rw = parts(k)
        j = k
    if tick:
        j.line((j.X(0.5), yt), (j.X(0.5), ybar))
    j.line((j.X(0), ybar), (j.X(1), ybar))
    cx = (j.x0 + j.x1) / 2
    ov = 0.01 * (top - j.y0)
    j.ring(cx - rw / 2, j.y0 - ov, cx + rw / 2, top + ov)


def c_z(j):
    """ㅿ (pansios): triangle."""
    A = (j.X(0.5), j.Y(1))
    j.line(A, (j.X(0), j.Y(0)), w=DIAG)
    j.line(A, (j.X(1), j.Y(0)), w=DIAG)
    j.line((j.X(0), j.Y(0)), (j.X(1), j.Y(0)))


def c_yng(j):
    """ㆁ (yesieung): ㅇ with a tick."""
    yt = j.Y(1)
    yb = yt - _tick(j, 0.2)
    j.line((j.X(0.5), yt), (j.X(0.5), yb - j.hh * 0.5))
    k = J(j.g, (j.x0, j.y0, j.x1, yb - j.hh * 0.2), j.s)
    c_ng(k)


def c_qh(j):
    """ㆆ (yeorinhieuh): ㅎ without its tick."""
    c_h(j, tick=False)


BASE = {
    "g": c_g, "n": c_n, "d": c_d, "r": c_r, "m": c_m, "b": c_b, "s": c_s,
    "ng": c_ng, "j": c_j, "c": c_c, "k": c_k, "t": c_t, "p": c_p, "h": c_h,
    "z": c_z, "yng": c_yng, "qh": c_qh,
}
SWEEPS = {"g", "k"}
TALL = {"s": 2.0, "j": 2.0, "c": 2.3, "z": 2.0}   # max height/width of diagonal jamo

# (stacked horizontal strokes, side-by-side vertical strokes) for density()
DENS = {
    "g": (1, 1), "n": (1, 1), "d": (2, 1), "r": (3, 2), "m": (2, 2), "b": (2, 2),
    "s": (1.3, 2), "ng": (2, 2), "j": (2.2, 2), "c": (3.0, 2), "k": (2, 1), "t": (3, 1),
    "p": (2, 2.4), "h": (4.0, 2), "z": (2, 2), "yng": (2.6, 2), "qh": (3, 2),
}

# consonant clusters: list of (base, width share); '/' entries stack (kapyeoun)
CONS = {
    "g": [("g", 1)], "kk": [("g", .5), ("g", .5)], "n": [("n", 1)], "d": [("d", 1)],
    "tt": [("d", .5), ("d", .5)], "r": [("r", 1)], "m": [("m", 1)], "b": [("b", 1)],
    "pp": [("b", .5), ("b", .5)], "s": [("s", 1)], "ss": [("s", .5), ("s", .5)],
    "ng": [("ng", 1)], "j": [("j", 1)], "jj": [("j", .5), ("j", .5)], "c": [("c", 1)],
    "k": [("k", 1)], "t": [("t", 1)], "p": [("p", 1)], "h": [("h", 1)],
    "gs": [("g", .47), ("s", .53)], "nj": [("n", .43), ("j", .57)], "nh": [("n", .41), ("h", .59)],
    "rg": [("r", .5), ("g", .5)], "rm": [("r", .5), ("m", .5)], "rb": [("r", .5), ("b", .5)],
    "rs": [("r", .5), ("s", .5)], "rt": [("r", .5), ("t", .5)], "rp": [("r", .5), ("p", .5)],
    "rh": [("r", .48), ("h", .52)], "bs": [("b", .5), ("s", .5)],
    # archaic (compatibility jamo only)
    "nn": [("n", .5), ("n", .5)], "nd": [("n", .5), ("d", .5)], "ns": [("n", .48), ("s", .52)],
    "nz": [("n", .48), ("z", .52)], "rgs": [("r", .34), ("g", .32), ("s", .34)],
    "rd": [("r", .5), ("d", .5)], "rbs": [("r", .34), ("b", .32), ("s", .34)],
    "rz": [("r", .5), ("z", .5)], "rqh": [("r", .48), ("qh", .52)], "mb": [("m", .5), ("b", .5)],
    "ms": [("m", .5), ("s", .5)], "mz": [("m", .5), ("z", .5)], "bg": [("b", .5), ("g", .5)],
    "bd": [("b", .5), ("d", .5)], "bsg": [("b", .34), ("s", .33), ("g", .33)],
    "bsd": [("b", .34), ("s", .33), ("d", .33)], "bj": [("b", .5), ("j", .5)],
    "bt": [("b", .5), ("t", .5)], "sg": [("s", .5), ("g", .5)], "sn": [("s", .5), ("n", .5)],
    "sd": [("s", .5), ("d", .5)], "sb": [("s", .5), ("b", .5)], "sj": [("s", .5), ("j", .5)],
    "z": [("z", 1)], "ngng": [("ng", .5), ("ng", .5)], "yng": [("yng", 1)],
    "yngs": [("yng", .5), ("s", .5)], "yngz": [("yng", .5), ("z", .5)], "hh": [("h", .5), ("h", .5)],
    "qh": [("qh", 1)],
    "mw": "m/", "bw": "b/", "ppw": "pp/", "pw": "p/",
}


def _gap(bw, W):
    return 0.075 * bw + 0.30 * W


def density(g, spec, box):
    """Pen scale for consonant cluster `spec` in ink box: the CJK weight
    factor, reduced where stacked/parallel strokes would leave less white
    than GAPK × stroke between them."""
    f = wf(g)
    Hk, Wk = g.H * f, g.W * f
    bw, bh = box[2] - box[0], box[3] - box[1]
    if isinstance(spec, str):          # kapyeoun: base over a small ㅇ
        base = spec[:-1]
        return density(g, CONS[base], (box[0], box[1] + bh * 0.4, box[2], box[3]))
    n = len(spec)
    avail = bw - _gap(bw, Wk) * (n - 1)
    d = 1.0
    for base, share in spec:
        nh, nv = DENS[base]
        w = avail * share
        d = min(d, bh / (Hk * (nh + GAPK * max(0, nh - 1))))
        d = min(d, w / (Wk * (nv + GAPK * max(0, nv - 1))))
    return f * max(0.58, min(1.0, d))


def draw_cons(g, name, box, sweep=0.0, s=None):
    """Draw consonant (cluster) `name` filling ink box."""
    spec = CONS[name]
    if s is None:
        s = density(g, spec, box)
    j = J(g, box, s)
    if isinstance(spec, str):          # kapyeoun: X over a small ㅇ
        base = spec[:-1]
        top = j.sub(0, 0.40, 1, 1)
        draw_cons(g, base, (top.x0, top.y0, top.x1, top.y1), s=s)
        ring = j.sub(0.24, 0, 0.76, 0.40 - 0.07)
        c_ng(ring, aspect=(1.5, 1.0))
        return
    n = len(spec)
    gap = _gap(j.bw, g.W * s)
    avail = j.bw - gap * (n - 1)
    x = j.x0
    for i, (base, share) in enumerate(spec):
        w = avail * share
        y0, y1 = j.y0, j.y1
        if base in TALL and (y1 - y0) > w * TALL[base]:
            # narrow diagonal jamo (ㅆ ㅉ in ㅐ-type syllables): cap the height
            h = w * TALL[base]
            cy = (y0 + y1) / 2
            y0, y1 = cy - h / 2, cy + h / 2
        k = J(g, (x, y0, x + w, y1), s)
        fn = BASE[base]
        if base in SWEEPS:
            # in doubles only the last element sweeps fully
            sw = sweep if i == n - 1 else sweep * 0.35
            fn(k, sw)
        else:
            fn(k)
        x += w + gap


# ---------------------------------------------------------------------------
# vowels
# ---------------------------------------------------------------------------

# vowel -> (horizontal part, vertical part)
VOWELS = {
    "a": (None, "a"), "ae": (None, "ae"), "ya": (None, "ya"), "yae": (None, "yae"),
    "eo": (None, "eo"), "e": (None, "e"), "yeo": (None, "yeo"), "ye": (None, "ye"),
    "o": ("o", None), "wa": ("o", "a"), "wae": ("o", "ae"), "oe": ("o", "i"),
    "yo": ("yo", None), "u": ("u", None), "wo": ("u", "eo"), "we": ("u", "e"),
    "wi": ("u", "i"), "yu": ("yu", None), "eu": ("eu", None), "ui": ("eu", "i"),
    "i": (None, "i"),
    # archaic (compatibility jamo only)
    "yo-ya": ("yo", "ya"), "yo-yae": ("yo", "yae"), "yo-i": ("yo", "i"),
    "yu-yeo": ("yu", "yeo"), "yu-ye": ("yu", "ye"), "yu-i": ("yu", "i"),
}

# vertical parts: stem centres (face u), stub kind, stub count, initial right edge,
# left-stub end (ink u)
VP = {
    "a": dict(stems=(0.745,), kind="r", n=1, Lr=0.60),
    "ya": dict(stems=(0.745,), kind="r", n=2, Lr=0.60),
    "eo": dict(stems=(0.895,), kind="l", n=1, Lr=0.545, end=0.655),
    "yeo": dict(stems=(0.895,), kind="l", n=2, Lr=0.545, end=0.655),
    "ae": dict(stems=(0.655, 0.915), kind="c", n=1, Lr=0.50),
    "yae": dict(stems=(0.655, 0.915), kind="c", n=2, Lr=0.50),
    "e": dict(stems=(0.755, 0.925), kind="l", n=1, Lr=0.455, end=0.555),
    "ye": dict(stems=(0.755, 0.925), kind="l", n=2, Lr=0.455, end=0.555),
    "i": dict(stems=(0.77,), kind=None, n=0, Lr=0.62),
}
# mixed vowels: the lone ㅣ stands further right (귀 괴 긔 would look left-heavy)
VP_M = {"i": dict(stems=(0.85,), kind=None, n=0, Lr=0.66)}


def vpart(vp, t):
    return VP_M[vp] if t == "M" and vp in VP_M else VP[vp]


HCLS = {"o": "o", "yo": "o", "u": "u", "yu": "u", "eu": "eu"}

# vertical layout tables (face v fractions)
#   L: initial ink y-range;  vs: vertical-vowel stem ink y-range;  bar: centre of
#   the horizontal vowel bar;  stub: ink end of its short strokes;  vy: centre of
#   the vertical part's stubs (mixed);  T: top of the final box
VT = {
    ("V", None, 0): dict(L=(0.15, 0.955), vs=(0.0, 1.0)),
    ("V", None, 1): dict(L=(0.52, 0.99), vs=(0.41, 1.0), T=0.335),
    ("H", "o", 0): dict(L=(0.395, 0.99), bar=0.065, stub=0.31),
    ("H", "o", 1): dict(L=(0.68, 1.0), bar=0.465, stub=0.60, T=0.335),
    ("H", "u", 0): dict(L=(0.56, 0.99), bar=0.465, stub=0.0),
    ("H", "u", 1): dict(L=(0.765, 1.0), bar=0.665, stub=0.43, T=0.32),
    ("H", "eu", 0): dict(L=(0.33, 0.99), bar=0.20),
    ("H", "eu", 1): dict(L=(0.625, 1.0), bar=0.50, T=0.34),
    ("M", "o", 0): dict(L=(0.445, 0.975), bar=0.16, stub=0.365, vs=(0.0, 1.0), vy=0.50),
    ("M", "o", 1): dict(L=(0.69, 1.0), bar=0.49, stub=0.615, vs=(0.41, 1.0), vy=0.72, T=0.325),
    ("M", "u", 0): dict(L=(0.645, 0.975), bar=0.56, stub=0.06, vs=(0.0, 1.0), vy=0.30),
    ("M", "u", 1): dict(L=(0.79, 1.0), bar=0.71, stub=0.44, vs=(0.41, 1.0), vy=0.57, T=0.32),
    ("M", "eu", 0): dict(L=(0.37, 0.975), bar=0.235, vs=(0.0, 1.0)),
    ("M", "eu", 1): dict(L=(0.635, 1.0), bar=0.515, vs=(0.41, 1.0), T=0.325),
}

# final box x-range per layout type
TX = {"V": (0.07, 0.90), "H": (0.10, 0.90), "M": (0.05, 0.88)}
# initial x-range for horizontal vowels
LX_H = {0: (0.125, 0.875), 1: (0.165, 0.835)}


def vtype(vowel):
    hp, vp = VOWELS[vowel]
    if hp is None:
        return "V"
    return "H" if vp is None else "M"


def lctx(vowel):
    """Initial layout group of a vowel (vowels sharing the same initial box)."""
    return {"ya": "a", "yeo": "eo", "yae": "ae", "ye": "e", "yo": "o", "yu": "u"}.get(vowel, vowel)


def tctx(vowel):
    t = vtype(vowel)
    if t == "V":
        return "V"
    return t + HCLS[VOWELS[vowel][0]]


def layout(vowel, final):
    """Return dict: type, L box (ink abs), T box or None, vt table, vp/hp."""
    hp, vp = VOWELS[vowel]
    t = vtype(vowel)
    hc = HCLS.get(hp)
    vt = VT[(t, hc, final)]
    Ly = (fy(vt["L"][0]), fy(vt["L"][1]))
    if t == "V":
        Lx = (fx(0.0), fx(VP[vp]["Lr"]))
    elif t == "H":
        a, b = LX_H[final]
        Lx = (fx(a), fx(b))
    else:
        Lx = (fx(0.0), fx(vpart(vp, t)["Lr"] - 0.035))
    T = None
    if final:
        a, b = TX[t]
        T = (fx(a), fy(0.0), fx(b), fy(vt["T"]))
    return dict(type=t, L=(Lx[0], Ly[0], Lx[1], Ly[1]), T=T, vt=vt, hp=hp, vp=vp, hc=hc)


# width of single finals relative to the final box (diagonal jamo look wide)
TW = {"s": 0.80, "j": 0.82, "c": 0.82, "h": 0.86, "ss": 0.92, "n": 0.94, "ng": 1.0}


def final_box(cons, vowel):
    x0, y0, x1, y1 = layout(vowel, 1)["T"]
    k = TW.get(cons, 1.0)
    cx = (x0 + x1) / 2
    return (cx - (x1 - x0) * k / 2, y0, cx + (x1 - x0) * k / 2, y1)


def sweep_for(vowel, final):
    t = vtype(vowel)
    if t == "V":
        return 0.62 if final else 1.0
    return 0.0


def draw_vowel(g, vowel, final, s=None):
    """Draw the medial vowel in syllable position."""
    if s is None:
        s = wf(g)
    hw, hh = g.hw * s, g.hh * s
    Hk = g.H * s
    lay = layout(vowel, final)
    vt, hp, vp = lay["vt"], lay["hp"], lay["vp"]
    L = lay["L"]
    Lcx, Lcy = (L[0] + L[2]) / 2, (L[1] + L[3]) / 2

    def line(a, b):
        g.pen(*a).l(*b).end(scale=s)

    stem0_left = None
    if vp is not None:
        P = vpart(vp, lay["type"])
        y0 = fy(vt["vs"][0]) + hh
        y1 = fy(vt["vs"][1]) - hh
        xs = [fx(u) for u in P["stems"]]
        for x in xs:
            line((x, y1), (x, y0))
        stem0_left = xs[0] - hw
        if lay["type"] == "V":
            yc = Lcy
            sep = max(0.25 * (L[3] - L[1]), 2.1 * Hk)
        else:
            yc = fy(vt.get("vy", 0.5))
            sep = max(0.20 * FH * (0.75 if final else 1.0), 2.1 * Hk)
        ys = [yc] if P["n"] == 1 else ([yc + sep / 2, yc - sep / 2] if P["n"] == 2 else [])
        for y in ys:
            if P["kind"] == "r":
                line((xs[0], y), (fx(1.0) - hw, y))
            elif P["kind"] == "l":
                line((xs[0], y), (fx(P["end"]) + hw, y))
            elif P["kind"] == "c":
                line((xs[0], y), (xs[1], y))
    if hp is not None:
        yb = fy(vt["bar"])
        x0 = fx(0.0) + hw
        if lay["type"] == "H":
            x1 = fx(1.0) - hw
            cx = Lcx
            half = 0.5 * (L[2] - L[0])
        else:
            x1 = stem0_left - (0.085 * FW + 0.25 * g.W * s) - hw
            cx = Lcx
            half = 0.5 * (L[2] - L[0])
        line((x0, yb), (x1, yb))
        hc = HCLS[hp]
        if hc != "eu":
            if hp in ("yo", "yu"):
                dx = max(0.30 * half, 1.6 * g.W * s)
                xs = [cx - dx, cx + dx]
            else:
                xs = [cx + (0.02 * FW if hc == "u" and lay["type"] == "H" else 0.0)]
            if hc == "o":
                ye = fy(vt["stub"]) - hh
            else:
                ye = fy(vt["stub"]) + hh
            for x in xs:
                line((x, yb), (x, ye))


# ---------------------------------------------------------------------------
# standalone (compatibility) jamo
# ---------------------------------------------------------------------------

def compat_cons_box(name):
    spec = CONS[name]
    n = 1 if isinstance(spec, str) else len(spec)
    w = {1: 540, 2: 700, 3: 780}[n]
    h = 600
    if isinstance(spec, str):
        h = 700
    return (500 - w / 2, EM_CY - h / 2, 500 + w / 2, EM_CY + h / 2)


def draw_compat_vowel(g, vowel):
    """A vowel alone: drawn in syllable layout (no initial/final) then
    re-centred (and squeezed for horizontal vowels) in the em."""
    sub = G(g.p, g.name)
    t = vtype(vowel)
    if vowel == "araea":
        return
    draw_vowel(sub, vowel, 0)
    pts = [p for st in sub.strokes for sg in st.segs for p in sg.pts]
    xmin = min(p[0] for p in pts)
    xmax = max(p[0] for p in pts)
    ymin = min(p[1] for p in pts)
    ymax = max(p[1] for p in pts)
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    sx = {"V": 1.0, "H": 0.84, "M": 0.92}[t]
    sy = {"V": 0.80, "H": 1.0, "M": 0.84}[t]
    if t == "H" and ymax - ymin > 1:
        sy = 400.0 / (ymax - ymin)
    T = lambda p: (500 + (p[0] - cx) * sx, EM_CY + (p[1] - cy) * sy)
    for st in sub.strokes:
        g._add(_transform_stroke(st, T))
