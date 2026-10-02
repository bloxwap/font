"""Box Drawing (U+2500–257F) and Block Elements (U+2580–259F).

Everything here is built as filled contours (g.extra) on the exact
terminal cell: x 0..600, y -240..960 (the hhea/typo line box), so lines and
blocks connect seamlessly between neighbouring cells and lines.  Ends that
touch the cell boundary are butt-cut by construction.

Italic: box drawing stays upright (the generic italic shear is undone here),
otherwise vertical lines would not connect from one line to the next.

The line structure of U+2500–254B / 2550–256C / 2574–257F is derived from
the Unicode character names (e.g. "DOWN LIGHT AND RIGHT HEAVY").
"""
from __future__ import annotations

import math
import unicodedata

from ..geometry import Contour, KAPPA
from ..skeleton import glyph, G

X0, X1 = 0.0, 600.0
Y0, Y1 = -240.0, 960.0
CX = (X0 + X1) / 2          # 300
CY = (Y0 + Y1) / 2          # 360

LIGHT, HEAVY, DOUBLE = 1, 2, 3


# ---------------------------------------------------------------------------
# thickness (all linear in W => interpolation-safe)
# ---------------------------------------------------------------------------

def t_light(g: G):
    return g.W


def t_heavy(g: G):
    return g.W * 1.75 + 12


def t_double(g: G):
    """Thickness of each line of a double line."""
    return g.W * 0.62 + 8


def s_double(g: G):
    """Offset of each double line's centre from the cell centre-line."""
    td = t_double(g)
    gap = td * 0.9 + 24
    return (td + gap) / 2


# ---------------------------------------------------------------------------
# contour helpers
# ---------------------------------------------------------------------------

def _area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2


def poly(pts, ccw=True):
    """Closed polygon contour (counter-clockwise unless ccw=False)."""
    pts = list(pts)
    if (_area(pts) > 0) != ccw:
        pts.reverse()
    c = Contour(pts[0])
    for p in pts[1:]:
        c.ops.append(("line", p))
    c.ops.append(("line", pts[0]))
    return c


def rect(x0, y0, x1, y1, ccw=True):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ccw)


def hband(x0, x1, cy, t):
    return rect(x0, cy - t / 2, x1, cy + t / 2)


def vband(cx, y0, y1, t):
    return rect(cx - t / 2, y0, cx + t / 2, y1)


def clip_rect(pts, x0, y0, x1, y1):
    """Sutherland–Hodgman clip of a convex polygon to a rectangle."""
    def clip(pts, inside, cut):
        out = []
        for i in range(len(pts)):
            a = pts[i - 1]
            b = pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(cut(a, b))
                out.append(b)
            elif ia:
                out.append(cut(a, b))
        return out

    def cx_(xv):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0]))

    def cy_(yv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yv - a[1]) / (b[1] - a[1]), yv)

    pts = clip(pts, lambda p: p[0] >= x0, cx_(x0))
    pts = clip(pts, lambda p: p[0] <= x1, cx_(x1))
    pts = clip(pts, lambda p: p[1] >= y0, cy_(y0))
    pts = clip(pts, lambda p: p[1] <= y1, cy_(y1))
    return pts


def diag_band(p0, p1, t):
    """Band of perpendicular thickness t along p0->p1, clipped to the cell."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy * t / 2, ux * t / 2
    ex, ey = ux * t * 2, uy * t * 2          # extend past the corners, then clip
    a = (p0[0] - ex, p0[1] - ey)
    b = (p1[0] + ex, p1[1] + ey)
    pts = [(a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), (b[0] + nx, b[1] + ny), (a[0] + nx, a[1] + ny)]
    return poly(clip_rect(pts, X0, Y0, X1, Y1))


def arc_band(t, r):
    """Rounded corner, canonical orientation (arms right and down, like ╭):
    centre-line from (X1, CY) to (CX + r, CY), quarter arc to (CX, CY - r),
    then down to (CX, Y0).  Uniform thickness t."""
    ro, ri = r + t / 2, r - t / 2
    ox, oy = CX + r, CY - r                  # arc centre
    k = KAPPA
    c = Contour((X1, CY - t / 2))
    # inner (lower/right) edge, travelling towards the arc
    c.ops.append(("line", (X1, CY + t / 2)))
    c.ops.append(("line", (ox, oy + ro)))
    c.ops.append(("curve", (ox - ro * k, oy + ro), (ox - ro, oy + ro * k), (ox - ro, oy)))
    c.ops.append(("line", (ox - ro, Y0)))
    c.ops.append(("line", (ox - ri, Y0)))
    c.ops.append(("line", (ox - ri, oy)))
    c.ops.append(("curve", (ox - ri, oy + ri * k), (ox - ri * k, oy + ri), (ox, oy + ri)))
    c.ops.append(("line", (X1, CY - t / 2)))
    return c


def _mirror(c: Contour, mx: bool, my: bool):
    if not (mx or my):
        return c
    f = lambda p: ((2 * CX - p[0]) if mx else p[0], (2 * CY - p[1]) if my else p[1])
    c = c.transform(f)
    if mx != my:
        c = c.reversed()
    return c


def finish(g: G, contours, sans_too=True):
    """Add contours, undo the italic shear and pin the cell geometry."""
    sk = math.tan(math.radians(g.p.slant))
    yc = g.xh / 2
    unskew = lambda p: (p[0] - (p[1] - yc) * sk, p[1])
    xs = []
    for c in contours:
        xs += [p[0] for p in c.points()]
        g.extra.append(c.transform(unskew) if sk else c)
    xmin, xmax = min(xs), max(xs)
    g.advance = 600
    g.lsb = xmin - X0
    g.rsb = X1 - xmax
    g.zone = "auto"


# ---------------------------------------------------------------------------
# lines from arm descriptions
# ---------------------------------------------------------------------------

DIRS = {"LEFT": "l", "RIGHT": "r", "UP": "u", "DOWN": "d",
        "HORIZONTAL": "lr", "VERTICAL": "ud"}
WEIGHTS = {"LIGHT": LIGHT, "SINGLE": LIGHT, "HEAVY": HEAVY, "DOUBLE": DOUBLE}


def parse_arms(name):
    """'BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY' -> {'d': 1, 'r': 2}."""
    body = name.replace("BOX DRAWINGS ", "")
    parts = [p.split() for p in body.split(" AND ")]
    default = None
    for p in parts:
        for w in p:
            if w in WEIGHTS:
                default = WEIGHTS[w]
                break
        if default:
            break
    arms = {}
    for p in parts:
        wt = next((WEIGHTS[w] for w in p if w in WEIGHTS), default)
        for w in p:
            for d in DIRS.get(w, ""):
                arms[d] = wt
    return arms


def lines_simple(g: G, arms):
    """Light / heavy arms meeting in the centre."""
    th = {LIGHT: t_light(g), HEAVY: t_heavy(g)}
    l, r, u, d = (arms.get(k) for k in "lrud")
    tv = max([th[a] for a in (u, d) if a] or [0])
    tH = max([th[a] for a in (l, r) if a] or [0])
    out = []
    # horizontal
    if l and l == r:
        out.append(hband(X0, X1, CY, th[l]))
    else:
        for arm, opp, sgn in ((l, r, -1), (r, l, 1)):
            if not arm:
                continue
            if tv:
                ext = tv / 2
            elif opp and th[opp] >= th[arm]:
                ext = th[opp] / 2
            else:
                ext = 0
            if sgn < 0:
                out.append(hband(X0, CX + ext, CY, th[arm]))
            else:
                out.append(hband(CX - ext, X1, CY, th[arm]))
    # vertical
    if u and u == d:
        out.append(vband(CX, Y0, Y1, th[u]))
    else:
        for arm, opp, sgn in ((d, u, -1), (u, d, 1)):
            if not arm:
                continue
            if tH:
                ext = tH / 2
            elif opp and th[opp] >= th[arm]:
                ext = th[opp] / 2
            else:
                ext = 0
            if sgn < 0:
                out.append(vband(CX, Y0, CY + ext, th[arm]))
            else:
                out.append(vband(CX, CY - ext, Y1, th[arm]))
    return out


def lines_double(g: G, arms):
    """Glyphs with double lines (U+2550–256C).  Single arms are light."""
    tl, td, s = t_light(g), t_double(g), s_double(g)
    l, r, u, d = (arms.get(k) for k in "lrud")
    D = DOUBLE
    out = []

    # ---- horizontal ------------------------------------------------------
    hdouble = D in (l, r)
    vdouble = D in (u, d)
    if hdouble:
        through = l == D and r == D
        for yy, vside in ((CY + s, u), (CY - s, d)):
            if through:
                if vside == D:   # broken by the vertical double on this side
                    out.append(hband(X0, CX - s + td / 2, yy, td))
                    out.append(hband(CX + s - td / 2, X1, yy, td))
                else:
                    out.append(hband(X0, X1, yy, td))
                continue
            # one-sided
            if vdouble:
                xs = (CX + s - td / 2) if vside == D else (CX - s - td / 2)
            else:
                xs = CX - tl / 2
            if r == D:
                out.append(hband(xs, X1, yy, td))
            else:
                out.append(hband(X0, 2 * CX - xs, yy, td))
    else:
        # single horizontal arms with a double vertical
        if l and r:
            out.append(hband(X0, X1, CY, tl))
        elif l or r:
            vthrough = u == D and d == D
            if vthrough:
                xs = CX + s if r else CX - s     # near line
            else:
                xs = CX - s - td / 2 if r else CX + s + td / 2   # far line
            if r:
                out.append(hband(xs, X1, CY, tl))
            else:
                out.append(hband(X0, xs, CY, tl))

    # ---- vertical --------------------------------------------------------
    if vdouble:
        through = u == D and d == D
        for xx, hside in ((CX - s, l), (CX + s, r)):
            if through:
                if hside == D:
                    out.append(vband(xx, Y0, CY - s + td / 2, td))
                    out.append(vband(xx, CY + s - td / 2, Y1, td))
                else:
                    out.append(vband(xx, Y0, Y1, td))
                continue
            if hdouble:
                ys = (CY - s + td / 2) if hside == D else (CY + s + td / 2)
            else:
                ys = CY + tl / 2
            if d == D:
                out.append(vband(xx, Y0, ys, td))
            else:
                out.append(vband(xx, 2 * CY - ys, Y1, td))
    else:
        if u and d:
            out.append(vband(CX, Y0, Y1, tl))
        elif u or d:
            hthrough = l == D and r == D
            if hthrough:
                ys = CY - s if d else CY + s
            else:
                ys = CY + s + td / 2 if d else CY - s - td / 2
            if d:
                out.append(vband(CX, Y0, ys, tl))
            else:
                out.append(vband(CX, ys, Y1, tl))
    return out


def dashes(g: G, n, vertical, heavy):
    t = t_heavy(g) if heavy else t_light(g)
    out = []
    if vertical:
        L = (Y1 - Y0) / n
        gap = L * 0.34 + g.W * 0.1
        for i in range(n):
            out.append(vband(CX, Y0 + i * L + gap / 2, Y0 + (i + 1) * L - gap / 2, t))
    else:
        L = (X1 - X0) / n
        gap = L * 0.36 + g.W * 0.1
        for i in range(n):
            out.append(hband(X0 + i * L + gap / 2, X0 + (i + 1) * L - gap / 2, CY, t))
    return out


def _register_line(cp):
    name = unicodedata.name(chr(cp))

    def f(g: G):
        if "DASH" in name:
            n = {"DOUBLE": 2, "TRIPLE": 3, "QUADRUPLE": 4}[name.split()[3]]
            cs = dashes(g, n, name.endswith("VERTICAL"), name.split()[2] == "HEAVY")
        elif "ARC" in name:
            t = t_light(g)
            r = 230 + g.W * 0.1
            c = arc_band(t, r)
            cs = [_mirror(c, "LEFT" in name, "UP" in name)]
        elif "DIAGONAL" in name:
            t = t_light(g)
            a = diag_band((X1, Y1), (X0, Y0), t)
            b = diag_band((X0, Y1), (X1, Y0), t)
            if "CROSS" in name:
                cs = [a, b]
            elif "UPPER RIGHT" in name:
                cs = [a]
            else:
                cs = [b]
        else:
            arms = parse_arms(name)
            if DOUBLE in arms.values():
                cs = lines_double(g, arms)
            else:
                cs = lines_simple(g, arms)
        finish(g, cs)

    glyph(f"uni{cp:04X}", cp)(f)


for _cp in range(0x2500, 0x2580):
    _register_line(_cp)


# ---------------------------------------------------------------------------
# block elements
# ---------------------------------------------------------------------------

def _block(cp, fn):
    def f(g: G):
        finish(g, fn(g))
    glyph(f"uni{cp:04X}", cp)(f)


EH = (Y1 - Y0) / 8      # vertical eighth (150)
EW = (X1 - X0) / 8      # horizontal eighth (75)

_block(0x2580, lambda g: [rect(X0, CY, X1, Y1)])                       # ▀
for _i in range(1, 8):                                                   # ▁..▇
    _block(0x2580 + _i, lambda g, i=_i: [rect(X0, Y0, X1, Y0 + EH * i)])
_block(0x2588, lambda g: [rect(X0, Y0, X1, Y1)])                       # █
for _i in range(7, 0, -1):                                               # ▉..▏
    _block(0x2589 + (7 - _i), lambda g, i=_i: [rect(X0, Y0, X0 + EW * i, Y1)])
_block(0x2590, lambda g: [rect(CX, Y0, X1, Y1)])                       # ▐
_block(0x2594, lambda g: [rect(X0, Y1 - EH, X1, Y1)])                  # ▔
_block(0x2595, lambda g: [rect(X1 - EW, Y0, X1, Y1)])                  # ▕

# quadrants: bits UL, UR, LL, LR
_QUAD = {0x2596: "LL", 0x2597: "LR", 0x2598: "UL", 0x2599: "UL LL LR", 0x259A: "UL LR",
         0x259B: "UL UR LL", 0x259C: "UL UR LR", 0x259D: "UR", 0x259E: "UR LL", 0x259F: "UR LL LR"}


def _quads(spec):
    q = set(spec.split())
    out = []
    # merge full rows / columns into overlapping rectangles (no shared edges)
    if {"UL", "LL"} <= q:
        out.append(rect(X0, Y0, CX, Y1))
    if {"UR", "LR"} <= q:
        out.append(rect(CX, Y0, X1, Y1))
    if {"UL", "UR"} <= q:
        out.append(rect(X0, CY, X1, Y1))
    if {"LL", "LR"} <= q:
        out.append(rect(X0, Y0, X1, CY))
    boxes = {"UL": (X0, CY, CX, Y1), "UR": (CX, CY, X1, Y1), "LL": (X0, Y0, CX, CY), "LR": (CX, Y0, X1, CY)}
    covered = set()
    for a, b in (("UL", "LL"), ("UR", "LR"), ("UL", "UR"), ("LL", "LR")):
        if {a, b} <= q:
            covered |= {a, b}
    for k in q - covered:
        out.append(rect(*boxes[k]))
    return out


for _cp, _spec in _QUAD.items():
    _block(_cp, lambda g, s=_spec: _quads(s))


# shades: square "pixels" on a 100-unit grid that tiles across cells
PIX = 100.0
NCOL = int((X1 - X0) / PIX)      # 6
NROW = int((Y1 - Y0) / PIX)      # 12


def _light_cells():
    """25 % pattern: one pixel in every 2x2, staggered."""
    out = []
    for j in range(0, NROW, 2):
        for i in range(NCOL):
            if i % 2 == (j // 2) % 2:
                out.append((i, j))
    return out


def _shade_light(g):
    return [rect(X0 + i * PIX, Y0 + j * PIX, X0 + (i + 1) * PIX, Y0 + (j + 1) * PIX) for i, j in _light_cells()]


def _shade_medium(g):
    inset = 2.0
    out = []
    for j in range(NROW):
        for i in range(NCOL):
            if (i + j) % 2 == 0:
                out.append(rect(X0 + i * PIX + inset, Y0 + j * PIX + inset,
                                X0 + (i + 1) * PIX - inset, Y0 + (j + 1) * PIX - inset))
    return out


def _shade_dark(g):
    # 75 %: full cell with the 25 % pattern punched out (offset by one row so
    # it reads as the inverse of the light shade)
    out = [rect(X0, Y0, X1, Y1)]
    for i, j in _light_cells():
        j2 = j + 1
        out.append(rect(X0 + i * PIX, Y0 + j2 * PIX, X0 + (i + 1) * PIX, Y0 + (j2 + 1) * PIX, ccw=False))
    return out


_block(0x2591, _shade_light)    # ░
_block(0x2592, _shade_medium)   # ▒
_block(0x2593, _shade_dark)     # ▓
