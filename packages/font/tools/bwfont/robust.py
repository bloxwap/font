"""Verified overlap removal.

skia-pathops occasionally returns a *wrong* union (silently dropping a
region) when contours have near-coincident curves — which our stroked
design produces at every corner (two round caps around the same point).
`robust_union` validates the result against the original nonzero fill by
sampling winding numbers on a grid and retries with tiny perturbations.
"""
from __future__ import annotations

import numpy as np
import pathops

GRID = 20


def _flatten_path(path: pathops.Path, steps=8):
    """pathops.Path -> list of polygons (numpy arrays)."""
    polys, cur, last = [], [], None
    for verb, pts in path:
        if verb == pathops.PathVerb.MOVE:
            if len(cur) > 2:
                polys.append(np.array(cur))
            cur = [pts[0]]
            last = pts[0]
        elif verb == pathops.PathVerb.LINE:
            cur.append(pts[0])
            last = pts[0]
        elif verb == pathops.PathVerb.QUAD:
            p0, (p1, p2) = last, pts
            t = np.linspace(0, 1, steps + 1)[1:, None]
            seg = (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)
            cur.extend(map(tuple, seg))
            last = p2
        elif verb == pathops.PathVerb.CUBIC:
            p0, (p1, p2, p3) = last, pts
            t = np.linspace(0, 1, steps + 1)[1:, None]
            seg = ((1 - t) ** 3 * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(p1)
                   + 3 * (1 - t) * t ** 2 * np.array(p2) + t ** 3 * np.array(p3))
            cur.extend(map(tuple, seg))
            last = p3
        elif verb == pathops.PathVerb.CLOSE:
            if len(cur) > 2:
                polys.append(np.array(cur))
            cur = []
    if len(cur) > 2:
        polys.append(np.array(cur))
    return polys


def _winding(polys, pts):
    """Nonzero winding number of `pts` (N,2) w.r.t. polygons."""
    if not polys:
        return np.zeros(len(pts), dtype=int)
    a = np.concatenate([p for p in polys])
    b = np.concatenate([np.roll(p, -1, axis=0) for p in polys])
    x0, y0, x1, y1 = a[:, 0][None], a[:, 1][None], b[:, 0][None], b[:, 1][None]
    px, py = pts[:, 0][:, None], pts[:, 1][:, None]
    cr = (x1 - x0) * (py - y0) - (px - x0) * (y1 - y0)
    up = (y0 <= py) & (y1 > py) & (cr > 0)
    dn = (y1 <= py) & (y0 > py) & (cr < 0)
    return (up.sum(axis=1) - dn.sum(axis=1)).astype(int)


def _samples(polys):
    allp = np.concatenate(polys)
    x0, y0 = allp.min(axis=0)
    x1, y1 = allp.max(axis=0)
    # offset grid so samples rarely sit on boundaries
    xs = np.linspace(x0, x1, GRID + 2)[1:-1] + 0.3137
    ys = np.linspace(y0, y1, GRID + 2)[1:-1] + 0.2719
    gx, gy = np.meshgrid(xs, ys)
    return np.stack([gx.ravel(), gy.ravel()], axis=1)


def _ok(orig_polys, result: pathops.Path, pts):
    want = _winding(orig_polys, pts) != 0
    got = _winding(_flatten_path(result), pts) != 0
    bad = int((want != got).sum())
    return bad <= max(2, len(pts) // 100)


def _build(draw_fns, jitter):
    path = pathops.Path()
    pen = path.getPen()
    for i, draw in enumerate(draw_fns):
        if jitter:
            dx = jitter * (((i * 7919) % 13) / 13.0 - 0.5)
            dy = jitter * (((i * 104729) % 17) / 17.0 - 0.5)
            draw(_ShiftPen(pen, dx, dy))
        else:
            draw(pen)
    return path


class _ShiftPen:
    def __init__(self, pen, dx, dy):
        self.pen, self.dx, self.dy = pen, dx, dy

    def _t(self, p):
        return (p[0] + self.dx, p[1] + self.dy)

    def moveTo(self, p):
        self.pen.moveTo(self._t(p))

    def lineTo(self, p):
        self.pen.lineTo(self._t(p))

    def curveTo(self, *ps):
        self.pen.curveTo(*[self._t(p) for p in ps])

    def qCurveTo(self, *ps):
        self.pen.qCurveTo(*[self._t(p) if p is not None else None for p in ps])

    def closePath(self):
        self.pen.closePath()

    def endPath(self):
        self.pen.endPath()


def robust_union(draw_fns):
    """draw_fns: list of callables drawing one contour each into a segment
    pen.  Returns a simplified pathops.Path whose fill equals the nonzero
    fill of the input."""
    orig = _build(draw_fns, 0)
    orig_polys = _flatten_path(orig)
    if not orig_polys:
        return orig
    pts = _samples(orig_polys)
    last = None
    for jitter in (0, 0.02, 0.08, 0.25, 0.6, 1.2, 2.0, 3.0):
        p = _build(draw_fns, jitter)
        try:
            p.simplify(fix_winding=True, keep_starting_points=False)
        except pathops.PathOpsError:
            continue
        last = p
        if len(draw_fns) < 2 or _ok(orig_polys, p, pts):
            return p
    # drop contours that are degenerate on their own (collapsed counters)
    keep = []
    for draw in draw_fns:
        one = _build([draw], 0)
        try:
            one.simplify(fix_winding=False)
            keep.append(draw)
        except pathops.PathOpsError:
            pass
    if 0 < len(keep) < len(draw_fns):
        for jitter in (0, 0.02, 0.25, 1.0):
            p = _build(keep, jitter)
            try:
                p.simplify(fix_winding=True, keep_starting_points=False)
                return p
            except pathops.PathOpsError:
                continue
    import logging
    logging.getLogger("bwfont").warning("robust_union: could not verify union; using best effort")
    return last if last is not None else orig
