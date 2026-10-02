#!/usr/bin/env python3
"""Render text with a compiled font (HarfBuzz shaping + FreeType raster).

usage: render.py FONT OUT.png "text|second line" [--size 64] [--wght 400]
                 [--features ss01,tnum] [--lang TRK] [--wghts 100,400,900]
"""
from __future__ import annotations

import argparse

import freetype
import uharfbuzz as hb
from PIL import Image


def shape(blob_face, font_path, text, size, wght, features, lang, script=None, variations=None):
    face = hb.Face(blob_face)
    font = hb.Font(face)
    font.scale = (size * 64, size * 64)
    settings = dict(variations or {})
    if wght is not None:
        settings["wght"] = wght
    if settings:
        font.set_variations(settings)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if lang:
        buf.language = lang
    if script:
        buf.script = script
    feats = {}
    for f in features:
        if f.startswith("-"):
            feats[f[1:]] = False
        elif f:
            feats[f] = True
    hb.shape(font, buf, feats)
    return buf.glyph_infos, buf.glyph_positions


def render_lines(font_path, lines, size=64, wght=None, features=(), lang=None, pad=24, fg=0, bg=255,
                 line_gap=1.3, variations=None):
    blob = hb.Blob.from_file_path(font_path)
    ft = freetype.Face(font_path)
    ft.set_char_size(size * 64)
    settings = dict(variations or {})
    if wght is not None:
        settings["wght"] = wght
    if settings:
        try:
            axes = ft.get_variation_info().axes
        except freetype.FT_Exception:
            if variations:
                raise
            axes = ()  # Preserve the existing static-font --wght behavior.
        if axes:
            unknown = settings.keys() - {axis.tag for axis in axes}
            if unknown:
                raise ValueError(f"unknown variation axes: {', '.join(sorted(unknown))}")
            ft.set_var_design_coords([settings.get(axis.tag, axis.default) for axis in axes])
    rendered = []
    for line in lines:
        infos, poss = shape(blob, font_path, line, size, wght, features, lang, variations=variations)
        x = 0
        glyphs = []
        for info, pos in zip(infos, poss):
            glyphs.append((info.codepoint, x + pos.x_offset / 64, pos.y_offset / 64))
            x += pos.x_advance / 64
        rendered.append((glyphs, x))
    width = int(max([w for _, w in rendered] + [10]) + 2 * pad)
    lh = int(size * line_gap)
    height = int(lh * len(lines) + 2 * pad)
    img = Image.new("L", (width, height), bg)
    asc = size * 0.96
    for li, (glyphs, _) in enumerate(rendered):
        base = pad + li * lh + asc * 0.95 + (lh - size * 1.2) / 2
        for gid, gx, gy in glyphs:
            ft.load_glyph(gid, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_HINTING)
            ft.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
            bm = ft.glyph.bitmap
            if bm.width == 0 or bm.rows == 0:
                continue
            gimg = Image.frombytes("L", (bm.width, bm.rows), bytes(bm.buffer)) if bm.pitch == bm.width else \
                Image.frombytes("L", (bm.width, bm.rows), bytes(b for r in range(bm.rows) for b in bm.buffer[r * bm.pitch:r * bm.pitch + bm.width]))
            px = int(round(pad + gx + ft.glyph.bitmap_left))
            py = int(round(base - gy - ft.glyph.bitmap_top))
            color = Image.new("L", gimg.size, fg)
            img.paste(color, (px, py), gimg)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("out")
    ap.add_argument("text")
    ap.add_argument("--size", type=int, default=64)
    ap.add_argument("--wght", type=float, default=None)
    ap.add_argument("--wghts", default=None)
    ap.add_argument("--features", default="")
    ap.add_argument("--lang", default=None)
    a = ap.parse_args()
    lines = a.text.split("|")
    feats = [f for f in a.features.split(",") if f]
    if a.wghts:
        imgs = [render_lines(a.font, lines, a.size, float(w), feats, a.lang) for w in a.wghts.split(",")]
        W = max(i.width for i in imgs)
        H = sum(i.height for i in imgs)
        out = Image.new("L", (W, H), 255)
        y = 0
        for i in imgs:
            out.paste(i, (0, y))
            y += i.height
        out.save(a.out)
    else:
        render_lines(a.font, lines, a.size, a.wght, feats, a.lang).save(a.out)


if __name__ == "__main__":
    main()
