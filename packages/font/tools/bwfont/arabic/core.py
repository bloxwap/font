"""Arabic construction core: metrics, joining context, finishing, decor.

Coordinates: font units.  The *join line* is the baseline stroke: a
horizontal stroke of thickness g.H whose ink spans y = 0 .. g.H (skeleton
centre JY = g.hh).  Every glyph that joins on a side carries a butt-capped
stub on the join line reaching exactly x = 0 (left join) or x = advance
(right join), so neighbours connect seamlessly.

Rasm functions draw a *body* in local coordinates and fill a `Ctx` with:
    lx, rx      skeleton x on the join line where the left/right stub starts
    jl, jr      stub lengths (Sans) beyond lx / rx
    sbl, sbr    side bearings on non-joining sides (Sans)
    pt          named points: 'above' (x, y of the bottom of dots above),
                'below' (x, y of the top of dots below), 'ring', 'hh', ...
    top, bot    (x, y) body extent used for harakat anchors
`finish()` positions the body, adds the join stubs, sets the advance and
anchors, and marks the glyph fixed.
"""
from __future__ import annotations

import math

from ..skeleton import G, _transform_stroke, shift

MONO = 600.0
LW = 0.88          # stroke factor of small loops (feh, meem, waw, sad ...)
DIAG = 0.94        # diagonals


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------

def gw(g: G, sans, mono=None, grow=0.5, mgrow=None):
    """Width-like value that grows with weight (separate Mono value)."""
    if g.mono:
        m = sans if mono is None else mono
        return m + g.grow * (grow * 0.6 if mgrow is None else mgrow)
    return sans + g.grow * grow


def JY(g):            # join-line skeleton y
    return g.hh


def T(g):             # tooth height (beh/noon/yeh init+medi)
    return 300 + 0.42 * g.grow


def ST(g):            # seen / sad teeth
    return 0.8 * T(g)


def AH(g):            # alef / lam / tah ascender
    return 730.0


def KH(g):            # kaf / gaf ascender
    return 690.0


def DESC(g):          # deep bowls (noon, seen, lam, qaf ...)
    return -300 - 0.12 * g.grow


def D(g):             # dot diameter
    return 0.7 * g.W + 50


def DG(g):            # gap between dots
    return 0.2 * D(g) + 10


def DGAP(g):          # body -> dots
    return 0.28 * D(g) + 30


def MGAP(g):          # body/dots -> harakat
    return 44 + 0.15 * g.grow


def JS(g):            # default join stub (Sans)
    return 66 + 0.55 * g.grow


def SB(g):            # default side bearing (Sans)
    return 48 + 0.3 * g.grow


def MWF(g):           # stroke factor of small marks
    return 0.8 - 0.0016 * g.grow


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def _seg_pts(sg, n=12):
    if sg.kind == "line":
        return list(sg.pts)
    p0, p1, p2, p3 = sg.pts
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        a, b, c, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def ink_box(g: G, strokes=None, extra=None):
    strokes = g.strokes if strokes is None else strokes
    extra = g.extra if extra is None else extra
    xs, ys = [], []
    for s in strokes:
        for i, sg in enumerate(s.segs):
            w0, w1 = s.widths[i], s.widths[i + 1]
            pts = _seg_pts(sg)
            n = max(1, len(pts) - 1)
            for j, (x, y) in enumerate(pts):
                w = (w0 + (w1 - w0) * j / n) * s.scale
                xs += [x - g.hw * w, x + g.hw * w]
                ys += [y - g.hh * w, y + g.hh * w]
    for c in extra:
        for p in c.points():
            xs.append(p[0])
            ys.append(p[1])
    if not xs:
        return (0, 0, 0, 0)
    return min(xs), min(ys), max(xs), max(ys)


def move_all(g: G, fn, n_strokes=0, n_extra=0):
    """Apply a point transform to strokes/extras drawn after the given counts."""
    g.strokes[n_strokes:] = [_transform_stroke(s, fn) for s in g.strokes[n_strokes:]]
    g.extra[n_extra:] = [c.transform(fn) for c in g.extra[n_extra:]]


def stamp(g: G, fn, cx, y, above=True, align="c"):
    """Draw `fn(sub)` into g so its ink box is centred on cx (align 'c'),
    and its bottom (above=True) or top (above=False) is at y.
    Returns the far extreme (top or bottom)."""
    sub = G(g.p, g.name)
    fn(sub)
    x0, y0, x1, y1 = ink_box(sub)
    if align == "c":
        dx = cx - (x0 + x1) / 2
    elif align == "l":
        dx = cx - x0
    else:
        dx = cx - x1
    dy = (y - y0) if above else (y - y1)
    T_ = shift(dx, dy)
    for s in sub.strokes:
        g.strokes.append(_transform_stroke(s, T_))
    for c in sub.extra:
        g.extra.append(c.transform(T_))
    return (y + (y1 - y0)) if above else (y - (y1 - y0))


# ---------------------------------------------------------------------------
# dots
# ---------------------------------------------------------------------------

# rows listed from the body outwards; offsets in units of the dot pitch
DOT_ROWS = {
    "1": [[0]],
    "2": [[-0.5, 0.5]],
    "3": [[-0.5, 0.5], [0]],          # above: pointing up; below: pointing down
    "3r": [[0], [-0.5, 0.5]],         # reversed triangle
    "3h": [[-1, 0, 1]],
    "4": [[-0.5, 0.5], [-0.5, 0.5]],
    "2v": [[0], [0]],
}


def dots(g: G, pat, cx, y, above=True, d=None):
    d = D(g) if d is None else d
    s = d + DG(g)
    rows = DOT_ROWS[pat]
    tri = pat in ("3", "3r")
    step = s * (0.86 if tri else 0.94)
    sg = 1 if above else -1
    for i, row in enumerate(rows):
        yc = y + sg * (d / 2 + i * step)
        for ox in row:
            g.dot(cx + ox * s, yc, d)
    return y + sg * (d + (len(rows) - 1) * step)


def dots_width(g, pat):
    d = D(g)
    s = d + DG(g)
    rows = DOT_ROWS[pat]
    return d + s * max(max(r) - min(r) for r in rows)


# ---------------------------------------------------------------------------
# small marks (drawn around the origin; place them with stamp())
# ---------------------------------------------------------------------------

def mk_fatha(g, w=None, s=1.0):
    w = MWF(g) if w is None else w
    L = (150 + 0.5 * g.grow) * s
    g.line(-L / 2, 0, L / 2, L * 0.42, w)


def mk_fathatan(g):
    w = MWF(g)
    L = 150 + 0.5 * g.grow
    gap = g.H * w + 34 + 0.1 * g.grow
    for i in range(2):
        g.line(-L / 2, i * gap, L / 2, L * 0.42 + i * gap, w)


def mk_damma(g, w=None, s=1.0, flip=False):
    w = MWF(g) if w is None else w
    hd = (96 + 0.8 * g.grow) * s           # head ink width
    th = (66 + 0.3 * g.grow) * s           # tail drop below the head
    hx, hy = g.hw * w, g.hh * w
    g.oval(0, th, hd, th + hd * 1.04, w=w)
    sx = hd * 0.5
    p = g.pen(sx, th + hy, w)
    p.to(-hd * 0.18, hy, "l", (-0.5, -1), k=0.62)
    p.end()
    if flip:
        pass


def mk_dammatan(g):
    w = MWF(g)
    mk_damma(g, w)
    hd = 96 + 0.8 * g.grow
    th = 66 + 0.3 * g.grow
    # a second, reversed curl on the head (classic dammatan)
    hy = g.hh * w
    top = th + hd * 1.04 - hy
    (g.pen(hd - g.hw * w, th + hd * 0.6, w)
        .to(hd + hd * 0.55, top + hd * 0.05, (0.3, 1), (1, 0.15), k=0.62)
        .end())


def mk_sukun(g):
    w = 0.6
    sd = 150 + 1.1 * g.grow
    g.oval(-sd / 2, 0, sd / 2, sd, w=w)


def mk_shadda(g, s=1.0):
    w = MWF(g)
    sw = (176 + 0.9 * g.grow) * s
    sh = (78 + 0.4 * g.grow) * s
    g.pen(0, sh, w).v(sw / 4, 0).h(sw / 2, sh).end()
    g.pen(sw / 2, sh, w).v(3 * sw / 4, 0).h(sw, sh).end()


def mk_madda(g, s=1.0):
    w = MWF(g)
    mw = (232 + 0.7 * g.grow) * s
    mh = (64 + 0.3 * g.grow) * s
    a, b = -mw / 2, mw / 2
    lo, hi = 0, mh
    (g.pen(a, lo + mh * 0.1, w)
        .to(a * 0.42, hi, (0.35, 1), "r", k=0.6)
        .to(b * 0.42, lo, (1, -1.0), "r", k=0.6)
        .to(b, hi - mh * 0.1, "r", (0.35, 1), k=0.6)
        .end())


def mk_hamza(g, s=1.0, w=None):
    """Hamza: a small c-shaped head with a tail running down-right."""
    w = MWF(g) if w is None else w
    A = (176 + 0.55 * g.grow) * s
    B = (210 + 0.4 * g.grow) * s
    (g.pen(0.92 * A, 0.80 * B, w)
        .to(0.50 * A, B, (-0.55, 1), "l", k=0.6)
        .h(0.10 * A, 0.66 * B, k=0.6)
        .v(0.52 * A, 0.34 * B, k=0.6)
        .end())
    g.line(0.36 * A, 0.34 * B, 1.06 * A, 0.04 * B, w, w * 0.92)


def mk_tah(g):
    w = MWF(g) * 0.92
    lw = 150 + 0.7 * g.grow
    lh = 64 + 0.3 * g.grow
    g.oval(-lw / 2, 0, lw / 2, lh, w=w)
    xs = -lw * 0.16
    g.line(xs, lh - g.hh * w, xs - 4, lh + 112 + 0.3 * g.grow, w)


def mk_v(g, inv=False):
    w = MWF(g) * 0.92
    vw = 118 + 0.7 * g.grow
    vh = 96 + 0.3 * g.grow
    if inv:
        g.line(-vw / 2, 0, 0, vh, w)
        g.line(vw / 2, 0, 0, vh, w)
    else:
        g.line(-vw / 2, vh, 0, 0, w)
        g.line(vw / 2, vh, 0, 0, w)


def mk_ring(g):
    w = 0.56
    r = D(g) * 0.68
    g.oval(-r, -r, r, r, w=w)


def mk_dalef(g, s=1.0):
    w = MWF(g)
    h = (160 + 0.3 * g.grow) * s
    g.line(0, 0, -h * 0.08, h, w)


def mk_wasla(g):
    w = MWF(g) * 0.92
    a = 104 + 0.6 * g.grow
    h = 74 + 0.3 * g.grow
    (g.pen(-a, 0, w)
        .to(-a * 0.25, h, (0.25, 1), "r", k=0.6)
        .to(a, h * 0.45, "r", (0.4, -1), k=0.6)
        .end())


def mk_whamza(g):
    w = MWF(g)
    mk_hamza(g, 0.6)
    A = (176 + 0.55 * g.grow) * 0.6
    wl = A * 1.2
    lo = -(40 + 0.25 * g.grow)
    (g.pen(-wl * 0.1, lo + 8, w * 0.9)
        .to(wl * 0.45, lo, (0.6, 1), "r", k=0.6)
        .to(wl, lo + 8, "r", (0.6, 1), k=0.6)
        .end())


def mk_bar(g):
    w = MWF(g)
    L = 150 + 0.4 * g.grow
    g.line(-L / 2, 0, L / 2, 0, w)


def mk_meem(g, s=1.0):
    w = MWF(g)
    d = (86 + 0.6 * g.grow) * s
    g.oval(0, 0, d, d, w=w)
    g.line(g.hw * w, d * 0.45, g.hw * w, -d * 0.9, w)


def mk_seen_small(g):
    w = MWF(g)
    sw = 170 + 0.8 * g.grow
    sh = 70 + 0.3 * g.grow
    g.pen(0, sh, w).v(sw / 6, 0).h(sw / 3, sh).end()
    g.pen(sw / 3, sh, w).v(sw / 2, 0).h(2 * sw / 3, sh).end()
    g.pen(2 * sw / 3, sh, w).v(5 * sw / 6, 0).h(sw, sh * 0.5).end()


def mk_noon_small(g):
    w = MWF(g)
    nw = 120 + 0.6 * g.grow
    nh = 70 + 0.3 * g.grow
    g.pen(0, nh, w).v(nw / 2, 0).h(nw, nh).end()
    g.dot(nw / 2, nh + D(g) * 0.35, D(g) * 0.5)


def mk_yeh_small(g):
    w = MWF(g)
    a = 150 + 0.6 * g.grow
    h = 90 + 0.3 * g.grow
    (g.pen(a * 0.75, h, w)
        .to(a * 0.45, h * 0.62, "l", "d", k=0.6)
        .to(a * 0.95, h * 0.05, "d", "d", k=0.6)
        .end())
    # the corner at the bottom right is a separate stroke (rounded join)
    (g.pen(a * 0.95, h * 0.05, w)
        .to(0, 0, "l", "u", k=0.6)
        .end())


MARK_FN = {
    "tah": mk_tah, "v": mk_v, "iv": lambda g: mk_v(g, True), "ring": mk_ring,
    "hamza": lambda g: mk_hamza(g, 0.62), "madda": mk_madda, "wasla": mk_wasla,
    "dalef": mk_dalef, "damma": lambda g: mk_damma(g, s=0.85), "whamza": mk_whamza,
    "bar": mk_bar, "fatha": mk_fatha, "sukun": mk_sukun,
}


# ---------------------------------------------------------------------------
# joining context
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, g: G, form: str):
        self.g = g
        self.form = form
        self.lj = form in ("init", "medi")
        self.rj = form in ("medi", "fina")
        self.lx = 0.0
        self.rx = 0.0
        self.jl = JS(g)
        self.jr = JS(g)
        self.sbl = SB(g)
        self.sbr = SB(g)
        self.pt = {}
        self.top = None
        self.bot = None
        self.mono_dx = 0.0
        self.extra_anchors = {}

    # shortcuts
    @property
    def W(self):
        return self.g.W

    @property
    def hw(self):
        return self.g.hw

    @property
    def hh(self):
        return self.g.hh


def apply_decor(c: Ctx, tokens):
    """Draw dot patterns and small marks; returns (top_y, bottom_y) reached."""
    g = c.g
    ax, ay = c.pt.get("above", (0, 0))
    bx, by = c.pt.get("below", (0, 0))
    top = None
    bot = None
    gap = DG(g) * 1.1
    for t in tokens:
        if t[0] == "a" and t[1:] in DOT_ROWS:
            ay2 = dots(g, t[1:], ax, ay, True)
            top = ay2
            ay = ay2 + gap
        elif t[0] == "b" and t[1:] in DOT_ROWS:
            by2 = dots(g, t[1:], bx, by, False)
            bot = by2
            by = by2 - gap
        elif t in ("tah", "v", "iv", "hamza", "madda", "wasla", "dalef", "damma", "whamza"):
            ay2 = stamp(g, MARK_FN[t], ax, ay, True)
            top = ay2
            ay = ay2 + gap
        elif t in ("tahb", "vb", "ivb", "hamzab", "whamzab"):
            base = t[:-1]
            by2 = stamp(g, MARK_FN[base], bx, by, False)
            bot = by2
            by = by2 - gap
        elif t == "ring":
            rx, ry = c.pt.get("ring", (bx, by))
            if "ring" in c.pt:
                r = D(g) * 0.68
                stamp(g, mk_ring, rx, ry - r, True)
                bot = min(bot if bot is not None else 1e9, ry - r)
            else:
                by2 = stamp(g, mk_ring, bx, by, False)
                bot = by2
                by = by2 - gap
        elif t == "hh":
            hx, hy = c.pt.get("hh", (ax + 120, ay))
            y2 = stamp(g, MARK_FN["hamza"], hx, hy, True)
            top = max(top or -1e9, y2)
        elif t == "bar":
            px, py = c.pt.get("bar", (bx, by))
            stamp(g, mk_bar, px, py - (g.H * MWF(g)) / 2, True)
        else:
            raise ValueError(f"unknown decor {t!r}")
    return top, bot


def finish(c: Ctx, decor_top=None, decor_bot=None):
    g = c.g
    x0, y0, x1, y1 = ink_box(g)
    if g.mono:
        adv = MONO
        ox = adv / 2 - (x0 + x1) / 2 + c.mono_dx
    else:
        L = (c.lx - c.jl) if c.lj else (x0 - c.sbl)
        R = (c.rx + c.jr) if c.rj else (x1 + c.sbr)
        ox = -L
        adv = R - L
    T_ = shift(ox, 0)
    move_all(g, T_)
    jy = JY(g)
    if c.lj:
        g.line(0, jy, c.lx + ox, jy, caps=("butt", "round"))
    if c.rj:
        g.line(c.rx + ox, jy, adv, jy, caps=("round", "butt"))
    g.fixed = True
    g.advance = round(adv)
    # harakat anchors
    tx, ty = c.top if c.top is not None else ((x0 + x1) / 2, y1)
    bx, by = c.bot if c.bot is not None else ((x0 + x1) / 2, y0)
    if "above" in c.pt:
        tx = c.pt["above"][0]
    if "below" in c.pt and c.bot is None:
        bx = c.pt["below"][0]
    if decor_top is not None:
        ty = max(ty, decor_top)
    if decor_bot is not None:
        by = min(by, decor_bot)
    g.anchor("top", tx + ox, ty + MGAP(g))
    g.anchor("bottom", bx + ox, by - MGAP(g))
    for k, (x, y) in c.extra_anchors.items():
        g.anchor(k, x + ox, y)
    return adv
