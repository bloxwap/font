#!/usr/bin/env python3
"""Render glyphs straight from skeletons with real auto-spacing (no compile).

usage: dev_preview.py OUT.png "Text with /glyphname tokens|second line"
         [--stems 22,84,180] [--family sans|mono] [--slant 9] [--size 90]
         [--outline NAME]   (big single-glyph view with points)

Characters are looked up via the unicodes registered with @glyph; use
/name to reference unencoded glyphs, e.g. "/a.ss01 /zero.zero".
"""
import argparse, importlib, pkgutil, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from PIL import Image
from bwfont.skeleton import GLYPHS, G, params_for, outline
from bwfont.geometry import Plan
from bwfont.spacing import autospace
from bwfont import preview
import bwfont.glyphs as gl
for m in pkgutil.iter_modules(gl.__path__):
    importlib.import_module(f"bwfont.glyphs.{m.name}")

CMAP = {}
for n, gd in GLYPHS.items():
    for u in gd.unicodes:
        CMAP.setdefault(u, n)


def tokens(text):
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "/" and i + 1 < len(text) and text[i + 1] not in " /":
            j = i + 1
            while j < len(text) and text[j] != " ":
                j += 1
            out.append(text[i + 1:j])
            i = j + 1
            continue
        out.append(CMAP.get(ord(ch), ".notdef" if ch != " " else "space"))
        i += 1
    return out


def build(name, stem, fam, slant):
    p = params_for(fam, stem, slant)
    g = G(p, name)
    GLYPHS[name].func(g)
    cs = outline(g, Plan(), name)
    return g, p, cs


def item(name, stem, fam, slant):
    if name not in GLYPHS:
        name = ".notdef"
    g, p, cs = build(name, stem, fam, slant)
    gd = GLYPHS[name]
    if gd.kind == "mark":
        return cs, 0
    if not cs:
        return [], g.advance if g.advance is not None else 250
    lsb, rsb, x0, x1 = autospace(cs, g.zone or gd.zone, p.W, p.xh, p.cap, scale=g.sb.get("scale", 1.0))
    if g.lsb is not None: lsb = g.lsb
    if g.rsb is not None: rsb = g.rsb
    lsb += g.sb.get("l", 0); rsb += g.sb.get("r", 0)
    if p.mono or g.advance is not None:
        adv = p.mono_adv if (p.mono and g.advance is None) else g.advance
        off = lsb + (adv - (lsb + x1 - x0 + rsb)) / 2 - x0
    else:
        adv = lsb + x1 - x0 + rsb
        off = lsb - x0
    return [c.transform(lambda q, o=off: (q[0] + o, q[1])) for c in cs], adv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--stems", default="22,84,180")
    ap.add_argument("--family", default="sans")
    ap.add_argument("--slant", type=float, default=0.0)
    ap.add_argument("--size", type=int, default=90)
    ap.add_argument("--outline", default=None)
    a = ap.parse_args()
    stems = [float(s) for s in a.stems.split(",")]
    if a.outline:
        imgs = []
        for stem in stems:
            g, p, cs = build(a.outline, stem, a.family, a.slant)
            cs2, adv = item(a.outline, stem, a.family, a.slant)
            imgs.append(preview.render_outline(cs2, adv, size=a.size * 5,
                                               lines=(0, p.xh, p.cap, p.asc, p.desc)))
        W = sum(i.width for i in imgs); H = max(i.height for i in imgs)
        out = Image.new("RGB", (W, H), "white"); x = 0
        for i in imgs:
            out.paste(i, (x, 0)); x += i.width
        out.save(a.out)
        return
    rows = []
    for stem in stems:
        for line in a.text.split("|"):
            items = [item(n, stem, a.family, a.slant) for n in tokens(line)]
            rows.append(preview.render_line(items, size=a.size))
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    img = Image.new("L", (W, H), 255)
    y = 0
    for r in rows:
        img.paste(r, (0, y)); y += r.height
    img.save(a.out)


if __name__ == "__main__":
    main()
