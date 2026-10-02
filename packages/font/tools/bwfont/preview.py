"""Quick PNG previews straight from the generator (no font compile)."""
from __future__ import annotations

import pathops
from PIL import Image, ImageChops, ImageDraw

from .geometry import Contour, flatten


def union(contours):
    """Remove overlaps (verified; see robust.py)."""
    from .robust import robust_union
    return robust_union([c.draw for c in contours])


def path_polys(path, steps=10):
    """Flatten a pathops path into polygons."""
    polys = []
    cur = []
    last = None
    for verb, pts in path:
        if verb == pathops.PathVerb.MOVE:
            if cur:
                polys.append(cur)
            cur = [pts[0]]
            last = pts[0]
        elif verb == pathops.PathVerb.LINE:
            cur.append(pts[0])
            last = pts[0]
        elif verb == pathops.PathVerb.QUAD:
            p0 = last
            p1, p2 = pts
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                cur.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                            mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))
            last = p2
        elif verb == pathops.PathVerb.CUBIC:
            p0 = last
            p1, p2, p3 = pts
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                a, b, c, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
                cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
            last = p3
        elif verb == pathops.PathVerb.CLOSE:
            if cur:
                polys.append(cur)
            cur = []
    if cur:
        polys.append(cur)
    return polys


def render_line(items, size=120, upm=1000, pad=20, asc=960, desc=-260, fg=0, bg=255,
                outlines=False):
    """items: list of (contours, advance).  Returns a PIL image (black on white)."""
    ss = 3
    scale = size / upm * ss
    width = int(sum(a for _, a in items) * scale + 2 * pad * ss) + 1
    height = int((asc - desc) * scale + 2 * pad * ss)
    img = Image.new("L", (width, height), 0)
    x = pad * ss
    for contours, adv in items:
        if contours:
            path = union(contours)
            polys = [p for p in path_polys(path) if len(p) >= 3]
            if polys:
                xs = [px for poly in polys for px, _ in poly]
                gx0 = int(x + min(xs) * scale) - 2
                gx1 = int(x + max(xs) * scale) + 3
                gw = max(1, gx1 - gx0)
                acc = Image.new("1", (gw, height), 0)
                for poly in polys:
                    m = Image.new("1", (gw, height), 0)
                    ImageDraw.Draw(m).polygon(
                        [(x + px * scale - gx0, pad * ss + (asc - py) * scale) for px, py in poly], fill=1)
                    acc = ImageChops.logical_xor(acc, m)
                region = img.crop((gx0, 0, gx0 + gw, height))
                img.paste(ImageChops.lighter(region, acc.convert("L")), (gx0, 0))
        x += adv * scale
    img = img.resize((width // ss, height // ss), Image.LANCZOS)
    return ImageChops.invert(img)


def render_outline(contours, adv, size=600, upm=1000, asc=960, desc=-260, pad=20, lines=()):
    """Large single-glyph view with points shown (for design review)."""
    scale = size / upm
    width = int(max(adv, 300) * scale + 2 * pad)
    height = int((asc - desc) * scale + 2 * pad)
    img = Image.new("RGB", (width, height), (255, 255, 255))
    d = ImageDraw.Draw(img)
    tx = lambda p: (pad + p[0] * scale, pad + (asc - p[1]) * scale)
    for y in lines:
        d.line([tx((0, y)), tx((adv, y))], fill=(200, 220, 255))
    d.line([tx((0, desc)), tx((0, asc))], fill=(255, 200, 200))
    d.line([tx((adv, desc)), tx((adv, asc))], fill=(255, 200, 200))
    path = union(contours)
    for poly in path_polys(path):
        if len(poly) >= 3:
            d.polygon([tx(p) for p in poly], outline=(0, 0, 0))
    for c in contours:
        for p in c.points():
            q = tx(p)
            d.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=(255, 0, 80))
    return img
