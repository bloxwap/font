#!/usr/bin/env python3
"""Release checks for the Arabic, Armenian, Georgian and Hebrew companions.

Checks Unicode repertoire, HarfBuzz shaping/mark attachment, Mono advances
and the combined stylesheet's italic font selection against built fonts.
Run after fonts:build; does not inspect or depend on the skeleton drawings.
"""
from __future__ import annotations

import re
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from bwfont.families import FAMILIES

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT.parent.parent / "apps/docs/public"


def span(a, b):
    return set(range(a, b + 1))


REQUIRED = {
    "arabic": span(0x0621, 0x063A) | span(0x0641, 0x0655)
              | {0x060C, 0x061B, 0x061F, 0x067E, 0x0686, 0x0698, 0x06A9, 0x06CC},
    "armenian": span(0x0531, 0x0556) | span(0x0558, 0x058F) | span(0xFB13, 0xFB17),
    "georgian": span(0x10D0, 0x10FF) | span(0x1C90, 0x1CBA) | span(0x1CBD, 0x1CBF),
    "hebrew": span(0x05B0, 0x05C7) | span(0x05D0, 0x05EA) | span(0x05EF, 0x05F4),
}
SAMPLES = {
    "arabic": "السَّلَامُ عَلَيْكُمْ فارسی اردو",
    "armenian": "Հայաստան, Երևան · ԱԲԳ · և ﬓ ﬔ ﬕ ﬖ ﬗ ֏",
    "georgian": "ქართული ენა · ᲥᲐᲠᲗᲣᲚᲘ",
    "hebrew": "שָׁלוֹם עוֹלָם בְּרֵאשִׁית ײַ",
}


def shape(data, text, weight=400, features=None):
    font = hb.Font(hb.Face(data))
    font.scale = (1000, 1000)
    font.set_variations({"wght": weight})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return buf.glyph_infos, buf.glyph_positions


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def main():
    css = (PUBLIC / "bloxwap-font.css").read_text()
    checked = 0
    for script, required in REQUIRED.items():
        for style in ("sans", "mono"):
            fid = f"{style}-{script}"
            fam = FAMILIES[fid]
            path = ROOT / "fonts" / fam.ps / "variable" / f"{fam.ps}[wght].ttf"
            require(path.is_file(), f"{fid}: missing variable font")
            data = path.read_bytes()
            with TTFont(path) as font:
                cmap = font.getBestCmap()
                missing = required - cmap.keys()
                require(not missing, f"{fid}: missing {', '.join(f'U+{c:04X}' for c in sorted(missing))}")
                require([(a.axisTag, a.minValue, a.maxValue) for a in font["fvar"].axes]
                        == [("wght", 100, 900)], f"{fid}: wrong weight range")
                if style == "mono" and script != "arabic":
                    for cp in required:
                        if chr(cp).isalpha() and cp not in range(0xFB13, 0xFB18):
                            require(font["hmtx"][cmap[cp]][0] == 600,
                                    f"{fid}: U+{cp:04X} does not occupy one cell")
                if script == "hebrew":
                    tags = {r.FeatureTag for r in font["GPOS"].table.FeatureList.FeatureRecord}
                    require({"mark", "mkmk"} <= tags, f"{fid}: missing mark attachment/stacking")
                    # Legacy pointed letters are supported alongside decomposed text.
                    require({0xFB1D, 0xFB1F, 0xFB2A, 0xFB2B, 0xFB2C, 0xFB2D, 0xFB4F} <= cmap.keys(),
                            f"{fid}: missing Hebrew presentation forms")
                    clip_top, clip_bottom = font["OS/2"].usWinAscent, -font["OS/2"].usWinDescent
            for weight in (100, 400, 900):
                infos, positions = shape(data, SAMPLES[script], weight)
                require(all(i.codepoint for i in infos), f"{fid}: .notdef in sample at {weight}")
                if script == "hebrew":
                    for point in span(0x05B0, 0x05BD) | {0x05BF, 0x05C1, 0x05C2, 0x05C4, 0x05C5, 0x05C7}:
                        infos, positions = shape(data, "ש" + chr(point), weight)
                        require(len(infos) == 2 and all(i.codepoint for i in infos),
                                f"{fid}: lost Niqqud U+{point:04X}")
                        marks = [p for p in positions if p.x_advance == 0]
                        require(len(marks) == 1 and (marks[0].x_offset or marks[0].y_offset),
                                f"{fid}: unpositioned Niqqud U+{point:04X} at {weight}")
                    # Multiple anchor classes and stacked bottom marks survive shaping.
                    infos, positions = shape(data, "ש\u05B8\u05BD\u05BC\u05C1", weight)
                    require(len(infos) == 5 and sum(p.x_advance == 0 for p in positions) == 4,
                            f"{fid}: combined points lost or changed text advance")
                    # Measure positioned ink, including final letters with points
                    # below their descenders; sanitizer alone cannot catch clipping.
                    hbfont = hb.Font(hb.Face(data))
                    hbfont.scale = (1000, 1000)
                    hbfont.set_variations({"wght": weight})
                    for letter in span(0x05D0, 0x05EA):
                        for point in span(0x05B0, 0x05BD) | {0x05BF, 0x05C1, 0x05C2, 0x05C7}:
                            infos, positions = shape(data, chr(letter) + chr(point), weight)
                            for info, pos in zip(infos, positions):
                                ext = hbfont.get_glyph_extents(info.codepoint)
                                if ext:
                                    top = pos.y_offset + ext.y_bearing
                                    require(top <= clip_top and top + ext.height >= clip_bottom,
                                            f"{fid}: U+{letter:04X} + U+{point:04X} clips at {weight}")
                if script == "armenian":
                    for text in ("մն", "մե", "մի", "վն", "մխ"):
                        plain_i, plain_p = shape(data, text, weight, {"liga": False})
                        lig_i, lig_p = shape(data, text, weight, {"liga": True})
                        require(len(plain_i) == 2 and len(lig_i) == 1, f"{fid}: broken ligature {text}")
                        if style == "mono":
                            require(sum(p.x_advance for p in plain_p) == sum(p.x_advance for p in lig_p) == 1200,
                                    f"{fid}: ligature {text} changes the grid")
                if script == "arabic":
                    joined, _ = shape(data, "ببب", weight)
                    require(len({i.codepoint for i in joined}) == 3, f"{fid}: Arabic joining failed")
                    joined, _ = shape(data, "لا", weight)
                    require(len(joined) == 1, f"{fid}: lam-alef ligature failed")
            # Confirm each script is served by its own italic (or upright fallback)
            # when addressed through the combined Sans/Mono family name.
            rules = [r for r in re.findall(r"@font-face\s*\{([^}]+)\}", css)
                     if f'font-family: "Bloxwap {style.title()}";' in r
                     and fam.ps + "/" in r and "font-style: italic;" in r]
            require(len(rules) == 1, f"{fid}: missing combined italic rule")
            require(("-Italic" in rules[0]) == fam.italic, f"{fid}: wrong combined italic face")
            if fam.italic:
                italic = path.with_name(f"{fam.ps}-Italic[wght].ttf")
                with TTFont(italic) as font:
                    require(required <= font.getBestCmap().keys(), f"{fid}: incomplete italic repertoire")
                    require(font["post"].italicAngle != 0, f"{fid}: italic angle not set")
            print(f"{fid}: repertoire, shaping, spacing and web faces passed")
            checked += 1
    print(f"checked {checked} companions")


if __name__ == "__main__":
    main()
