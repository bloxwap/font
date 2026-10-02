"""Automatic sidebearings (HT-Letterspacer-style area measurement)."""
from __future__ import annotations

from .preview import union, path_polys


def polygons(contours):
    if not contours:
        return []
    return [p for p in path_polys(union(contours), steps=8) if len(p) >= 3]


def profile(polys, ys):
    """For each y return (xmin, xmax) of ink, or None."""
    edges = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            a = poly[i]
            b = poly[(i + 1) % n]
            if a[1] != b[1]:
                edges.append((a, b))
    out = []
    for y in ys:
        xs = []
        for a, b in edges:
            y0, y1 = a[1], b[1]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(a[0] + (b[0] - a[0]) * t)
        out.append((min(xs), max(xs)) if xs else None)
    return out


def bbox(polys):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def target_sb(W):
    # (stem, sidebearing) — tighter as weight grows
    pts = [(20, 66), (84, 60), (180, 42)]
    if W <= pts[0][0]:
        return pts[0][1]
    for (a, sa), (b, sb) in zip(pts, pts[1:]):
        if W <= b:
            return sa + (sb - sa) * (W - a) / (b - a)
    return pts[-1][1]


def autospace(contours, zone, W, xh, cap, factor=0.66, scale=1.0):
    """Return (lsb, rsb, xmin, xmax) for the glyph."""
    polys = polygons(contours)
    bb = bbox(polys)
    if bb is None:
        return None
    xmin, ymin, xmax, ymax = bb
    if zone == "uc" or zone == "fig":
        z0, z1 = 0, cap
        S = target_sb(W) * 1.12
    elif zone == "lc":
        z0, z1 = 0, xh
        S = target_sb(W)
    else:
        z0 = max(ymin, -1e9)
        z1 = ymax
        if ymax > xh * 0.6 and ymin < xh * 0.4:
            z0, z1 = max(ymin, 0), min(ymax, cap)
        S = target_sb(W)
    S *= scale
    if z1 - z0 < 20:
        z0, z1 = ymin, ymax
    n = 40
    ys = [z0 + (z1 - z0) * (i + 0.5) / n for i in range(n)]
    prof = profile(polys, ys)
    clip = 0.2 * xh + W * 0.15
    dl = []
    dr = []
    for pr in prof:
        if pr is None:
            dl.append(clip)
            dr.append(clip)
        else:
            dl.append(min(pr[0] - xmin, clip))
            dr.append(min(xmax - pr[1], clip))
    ml = sum(dl) / len(dl)
    mr = sum(dr) / len(dr)
    lo = 6 + W * 0.04
    lsb = max(lo, S - factor * ml)
    rsb = max(lo, S - factor * mr)
    return lsb, rsb, xmin, xmax
