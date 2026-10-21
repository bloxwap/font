"""Compare optimized overlap validation with the original math (SIL OFL-1.1)."""
import unittest
from unittest.mock import patch

import numpy as np
import pathops

from bwfont import robust as R


# Deliberately retain the old implementations as independent references.
def reference_flatten(path: pathops.Path, steps=8):
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


def reference_winding(polys, pts):
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



class RobustTests(unittest.TestCase):
    def assert_path_math(self, path):
        old, new = reference_flatten(path), R._flatten_path(path)
        self.assertEqual(len(old), len(new))
        for a, b in zip(old, new):
            np.testing.assert_array_equal(a, b)
        if old:
            pts = R._samples(old)
            np.testing.assert_array_equal(reference_winding(old, pts), R._winding(new, pts))

    def test_random_bezier_paths(self):
        rng = np.random.default_rng(21)
        for _ in range(100):
            path = pathops.Path()
            pen = path.getPen()
            for _ in range(3):
                points = iter(map(tuple, rng.uniform(-1000, 1000, (13, 2))))
                pen.moveTo(next(points))
                pen.lineTo(next(points))
                pen.qCurveTo(next(points), next(points))
                for _ in range(3):
                    pen.curveTo(next(points), next(points), next(points))
                pen.closePath()
            self.assert_path_math(path)
            for steps in (1, 3, 7, 16):
                for a, b in zip(reference_flatten(path, steps), R._flatten_path(path, steps)):
                    np.testing.assert_array_equal(a, b)

    def test_real_sans_mono_and_pixel_paths(self):
        from bwfont.build import load_glyph_modules
        from bwfont.geometry import Plan
        from bwfont.skeleton import G, GLYPHS, outline, params_for
        from bwfont.pixel import art
        from bwfont.pixel.build import register_all
        from bwfont.pixel.geom import pixel

        load_glyph_modules()
        for family in ("sans", "mono"):
            for stem in (22, 84, 180):
                for slant in (0, 9):
                    for name in ("A", "a", "g", "zero", "uni259A", "uni259E"):
                        g = G(params_for(family, stem, slant), name)
                        GLYPHS[name].func(g)
                        cs = outline(g, Plan(), name)
                        self.assert_path_math(R._build([c.draw for c in cs], 0))
        register_all()
        for name in ("A", "a", "g", "zero"):
            for size in (42, 78, 104):
                for rond in (0, .5, 1):
                    cs = [pixel(x, row * 100 + 50, size, rond)
                          for x, row in art.REG[name].pix]
                    self.assert_path_math(R._build([c.draw for c in cs], 0))

    def test_random_winding_and_boundary_rules(self):
        rng = np.random.default_rng(22)
        for n in (3, 20, 100, 500):
            polys = [rng.uniform(-1000, 1000, (n, 2)) for _ in range(3)]
            for pts in (rng.uniform(-1100, 1100, (400, 2)), R._samples(polys)):
                np.testing.assert_array_equal(reference_winding(polys, pts), R._winding(polys, pts))
        square = np.array(((0., 0.), (10., 0.), (10., 10.), (0., 10.)))
        values = np.array((-1., 0., np.nextafter(0., 1.), 5.,
                           np.nextafter(10., 0.), 10., np.nextafter(10., 11.), 11.))
        xs, ys = np.meshgrid(values, values)
        pts = np.column_stack((xs.ravel(), ys.ravel()))
        for polys in ([], [square], [square[::-1]], [square, square[::-1]],
                      [square, square + 5], [square, square * .5 + 2]):
            np.testing.assert_array_equal(reference_winding(polys, pts), R._winding(polys, pts))
        np.testing.assert_array_equal(R._winding([square], np.empty((0, 2))), [])

    def test_reference_winding_is_not_repeated_on_retry(self):
        def square(pen):
            pen.moveTo((0, 0)); pen.lineTo((10, 0))
            pen.lineTo((10, 10)); pen.lineTo((0, 10)); pen.closePath()

        with patch.object(R, "_ok", side_effect=(False, False, True)) as verify:
            with patch.object(R, "_winding", wraps=R._winding) as winding:
                R.robust_union([square, square])
        self.assertEqual(verify.call_count, 3)
        self.assertEqual(winding.call_count, 1)

    def test_memo_uses_content_and_returns_independent_paths(self):
        def square(pen):
            pen.moveTo((0, 0)); pen.lineTo((10, 0))
            pen.lineTo((10, 10)); pen.lineTo((0, 10)); pen.closePath()

        memo = {}
        with patch.object(R, "_union", wraps=R._union) as union:
            a = R.robust_union([square, square], memo=memo)
            expected = tuple(a)
            a.reset()
            b = R.robust_union([square, square], memo=memo)
            self.assertEqual(tuple(b), expected)
            self.assertEqual(union.call_count, 1)
            R.robust_union([square], memo=memo)
            self.assertEqual(union.call_count, 2)


if __name__ == "__main__":
    unittest.main()
