"""Box Drawing (U+2500–257F) and Block Elements (U+2580–259F).

Generated from the Unicode character names so every arm reaches the cell
edge (x 0/600, y -240/960 = the full line height) and glyphs connect across
cells and lines.  Line thickness follows the pixel size (so `wght` works);
lines are square-ended (radius 0) so they join seamlessly.  Shades are drawn
with real pixels on a 6×12 grid so they tile.
"""
from __future__ import annotations

import unicodedata

from .art import PixelDef, add, name_for
from .geom import rrect, poly, ring_sector, pixel

X0, X1 = 0, 600
Y0, Y1 = -240, 960
CX, CY = 300, 350

DIRS = ("up", "right", "down", "left")
U = {"right": (1, 0), "up": (0, 1), "left": (-1, 0), "down": (0, -1)}
V = {"right": (0, 1), "up": (-1, 0), "left": (0, -1), "down": (1, 0)}   # left-hand normal
SIDE_POS = {"right": "up", "up": "left", "left": "down", "down": "right"}
SIDE_NEG = {"right": "down", "up": "right", "left": "up", "down": "left"}
OPP = {"right": "left", "left": "right", "up": "down", "down": "up"}
LEN = {"right": X1 - CX, "left": CX - X0, "up": Y1 - CY, "down": CY - Y0}
WEIGHT = {"LIGHT": 1, "SINGLE": 1, "HEAVY": 2, "DOUBLE": 3}


def _dims(s):
    return {"t1": s, "t2": 1.9 * s, "rail": 0.6 * s, "g": 0.6 * s + 45}


def _local_rect(d, u0, u1, v0, v1):
    ux, uy = U[d]
    vx, vy = V[d]
    pts = [(CX + ux * u + vx * v, CY + uy * u + vy * v) for u in (u0, u1) for v in (v0, v1)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return rrect(min(xs), min(ys), max(xs), max(ys), 0)


def arms_shapes(arms: dict, s: float, dash: int = 0):
    k = _dims(s)

    def hw(d):
        w = arms.get(d, 0)
        if not w:
            return 0
        if w == 3:
            return k["g"] + k["rail"] / 2
        return (k["t1"] if w == 1 else k["t2"]) / 2

    out = []
    for d in DIRS:
        w = arms.get(d)
        if not w:
            continue
        L = LEN[d]
        perp = [p for p in (SIDE_POS[d], SIDE_NEG[d]) if p in arms]
        if w in (1, 2):
            t = k["t1"] if w == 1 else k["t2"]
            if perp:
                start = -max(hw(p) for p in perp)
            elif OPP[d] in arms:
                start = -t / 2
            else:
                start = 0
            if dash:
                # dashes: `dash` segments across the whole cell in this axis
                full = LEN[d] + LEN[OPP[d]]
                slot = full / dash
                gap = min(slot * 0.4, 110)
                lo = -LEN[OPP[d]]
                for i in range(dash):
                    a = lo + i * slot + gap / 2
                    b = lo + (i + 1) * slot - gap / 2
                    out.append(_local_rect(d, a, b, -t / 2, t / 2))
                break
            out.append(_local_rect(d, start, L, -t / 2, t / 2))
        else:
            rail, g = k["rail"], k["g"]
            for sgn, side, other in ((1, SIDE_POS[d], SIDE_NEG[d]), (-1, SIDE_NEG[d], SIDE_POS[d])):
                if side in arms:
                    start = (g - rail / 2) if arms[side] == 3 else hw(side)
                elif OPP[d] in arms:
                    start = -rail / 2
                elif other in arms:
                    start = -hw(other)
                else:
                    start = 0
                out.append(_local_rect(d, start, L, sgn * g - rail / 2, sgn * g + rail / 2))
    return out


def parse_box_name(name: str):
    """'BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY' -> {'down':1, 'right':2}"""
    body = name.replace("BOX DRAWINGS ", "")
    arms = {}
    w_prev = None
    for part in body.split(" AND "):
        words = part.split()
        w = None
        dirs = []
        for wd in words:
            if wd in WEIGHT:
                w = WEIGHT[wd]
            elif wd == "VERTICAL":
                dirs += ["up", "down"]
            elif wd == "HORIZONTAL":
                dirs += ["left", "right"]
            elif wd.lower() in U:
                dirs.append(wd.lower())
            else:
                raise ValueError(name)
        if w is None:
            w = w_prev
        for d in dirs:
            arms[d] = w
        w_prev = w
    return arms


def _arc(cp, s):
    t = s
    R = 200
    name = unicodedata.name(chr(cp))
    o = 1
    if "DOWN AND RIGHT" in name:
        c = (CX + R, CY - R); a0 = 90
        bars = [rrect(CX + R - o, CY - t / 2, X1, CY + t / 2, 0), rrect(CX - t / 2, Y0, CX + t / 2, CY - R + o, 0)]
    elif "DOWN AND LEFT" in name:
        c = (CX - R, CY - R); a0 = 0
        bars = [rrect(X0, CY - t / 2, CX - R + o, CY + t / 2, 0), rrect(CX - t / 2, Y0, CX + t / 2, CY - R + o, 0)]
    elif "UP AND LEFT" in name:
        c = (CX - R, CY + R); a0 = 270
        bars = [rrect(X0, CY - t / 2, CX - R + o, CY + t / 2, 0), rrect(CX - t / 2, CY + R - o, CX + t / 2, Y1, 0)]
    else:  # UP AND RIGHT
        c = (CX + R, CY + R); a0 = 180
        bars = [rrect(CX + R - o, CY - t / 2, X1, CY + t / 2, 0), rrect(CX - t / 2, CY + R - o, CX + t / 2, Y1, 0)]
    return [ring_sector(c[0], c[1], R + t / 2, R - t / 2, a0, a0 + 90)] + bars


def _diag(cp, s):
    t = s
    h = t / 2 * 1.118
    up = [poly([(X0 - h, Y0), (X0 + h, Y0), (X1 + h, Y1), (X1 - h, Y1)])]
    down = [poly([(X1 - h, Y0), (X1 + h, Y0), (X0 + h, Y1), (X0 - h, Y1)])]
    if cp == 0x2571:
        return up
    if cp == 0x2572:
        return down
    return up + down


def box_shapes(cp):
    name = unicodedata.name(chr(cp))
    if "ARC" in name:
        return lambda s, r: _arc(cp, s)
    if "DIAGONAL" in name:
        return lambda s, r: _diag(cp, s)
    dash = 0
    for word, n in (("DOUBLE DASH", 2), ("TRIPLE DASH", 3), ("QUADRUPLE DASH", 4)):
        if word in name:
            dash = n
            name = name.replace(word + " ", "")
    arms = parse_box_name(name)
    return lambda s, r: arms_shapes(arms, s, dash)


# ---------------------------------------------------------------------------
# block elements
# ---------------------------------------------------------------------------

H = Y1 - Y0  # 1200
W = X1 - X0  # 600


def _blk(x0, y0, x1, y1):
    return rrect(X0 + W * x0, Y0 + H * y0, X0 + W * x1, Y0 + H * y1, 0)


def block_shapes(cp):
    o = 0.001  # tiny overlap so adjoining quadrants fuse
    if cp == 0x2580:
        return lambda s, r: [_blk(0, 0.5, 1, 1)]
    if 0x2581 <= cp <= 0x2588:
        f = (cp - 0x2580) / 8
        return lambda s, r: [_blk(0, 0, 1, f)]
    if 0x2589 <= cp <= 0x258F:
        f = (0x2590 - cp) / 8
        return lambda s, r: [_blk(0, 0, f, 1)]
    if cp == 0x2590:
        return lambda s, r: [_blk(0.5, 0, 1, 1)]
    if cp == 0x2594:
        return lambda s, r: [_blk(0, 7 / 8, 1, 1)]
    if cp == 0x2595:
        return lambda s, r: [_blk(7 / 8, 0, 1, 1)]
    if cp in (0x2591, 0x2592, 0x2593):
        def shade(s, r, cp=cp):
            out = []
            for j in range(12):
                for i in range(6):
                    on = {0x2591: i % 2 == 0 and j % 2 == 0,
                          0x2592: (i + j) % 2 == 0,
                          0x2593: not (i % 2 == 1 and j % 2 == 1)}[cp]
                    if on:
                        out.append(pixel(X0 + 50 + 100 * i, Y0 + 50 + 100 * j, s * 1.1, r))
            return out
        return shade
    # quadrants: UL UR LL LR
    Q = {0x2596: "LL", 0x2597: "LR", 0x2598: "UL", 0x2599: "UL LL LR", 0x259A: "UL LR",
         0x259B: "UL UR LL", 0x259C: "UL UR LR", 0x259D: "UR", 0x259E: "UR LL", 0x259F: "UR LL LR"}
    q = Q[cp].split()
    rects = {"UL": (0, 0.5, 0.5 + o, 1), "UR": (0.5 - o, 0.5, 1, 1),
             "LL": (0, 0, 0.5 + o, 0.5 + o), "LR": (0.5 - o, 0, 1, 0.5 + o)}
    return lambda s, r: [_blk(*rects[k]) for k in q]


def register():
    for cp in range(0x2500, 0x2580):
        add(PixelDef(name_for(cp), [cp], set(), shapes=box_shapes(cp), shear=False))
    for cp in range(0x2580, 0x25A0):
        add(PixelDef(name_for(cp), [cp], set(), shapes=block_shapes(cp), shear=False))
