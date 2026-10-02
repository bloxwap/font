#!/usr/bin/env python3
"""Render compiled font UI specimens at every static weight.

Run after building changed families:
  .venv/bin/python tools/readability_preview.py --out /tmp/bloxwap-readability

This is a visual review aid, not an accessibility conformance test. It uses
FreeType via Pillow for Latin, and render.py's HarfBuzz/FreeType for script
samples. Browser and operating-system rasterizers can differ. Script samples
require native-reader review; they do not exhaust a family's repertoire.

Companion scripts and core Greek/Cyrillic at 16/24px, Thin/Regular/Black:
  .venv/bin/python tools/readability_preview.py --out /tmp/review --scripts-only

Actual website variable WOFF2, all named weights, plus Pixel ROND samples:
  .venv/bin/python tools/readability_preview.py --out /tmp/review --variable-only
"""
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

WEIGHTS = ("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold",
           "Bold", "ExtraBold", "Black")
SAMPLES = (
    "Il1  I l 1  0O  0 O  rn m  cl d  minimum  clear  Illinois",
    "aceos  a e c o s  ,.:;!?  '’\"“”  () [] {}  -–—  /\\",
    "ÀÁÂÃÄÅ Ç ÈÉÊË ÌÍÎÏ Ñ ÒÓÔÕÖ ÙÚÛÜ Ý  àáâãäå ç éë ï ñ ö ü ÿ",
)
SCRIPT_SAMPLES = {
    "core": ("el", ("ΑΒΓΔ ΘΟΩ ΙΊΪ · αβγδ εοσς θφψω · Ελλάδα άέήίόύώ ΐΰ",
                     "АБВГД ИЙІЇ · абвгд еос · Россия Україна й ё ї")),
    "Arabic": ("ar", ("السَّلَامُ عَلَيْكُمْ", "بَ بِ بُ بّ بَّ بِّ بُّ · لا لأ لإ لآ · فارسی اردو")),
    "Hebrew": ("he", ("שָׁלוֹם עוֹלָם בְּרֵאשִׁית", "בְּ בָּ בִּ שָׁ שָׂ ײַ")),
    "Armenian": ("hy", ("Հայաստան, Երևան · ԱԲԳ · և", "աբգդեզէըթժ · ֏")),
    "Georgian": ("ka", ("ქართული ენა · ᲥᲐᲠᲗᲣᲚᲘ", "აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ")),
    "JP": ("ja", ("日本語 漢字 東京 学校", "あいうえお がぎぐげご ぱぴぷぺぽ · アイウエオ ガギグゲゴ パピプペポ")),
    "KR": ("ko", ("한국어 서울 대한민국", "가나다라마바사 아자차카타파하 · 각 간 갈 값 곽 괜")),
    "SC": ("zh", ("中文 汉字 北京 上海", "学校 学生 阅读 清晰 · 日目 口回 人入 土士")),
}


def variable_previews(args):
    """Shape the website's variable outlines, preserving their hinting state."""
    from render import render_lines

    with TemporaryDirectory(prefix="bloxwap-variable-review-") as temp:
        for family in ("Sans", "Mono", "Pixel"):
            suffix = "-Italic" if args.italic else ""
            axes = "ROND,wght" if family == "Pixel" else "wght"
            source = args.fonts / f"Bloxwap{family}" / "variable" / f"Bloxwap{family}{suffix}[{axes}].woff2"
            variable = TTFont(source)
            required = {ord(c) for line in SAMPLES for c in line if not c.isspace()}
            missing = required - set(variable.getBestCmap())
            if missing:
                raise ValueError(f"{source}: missing variable specimen characters: "
                                 + ", ".join(f"U+{c:04X}" for c in sorted(missing)))
            variable.flavor = None
            # HarfBuzz reads SFNT, so decompress WOFF2 without adding hinting.
            path = Path(temp) / f"{family}.ttf"
            variable.save(path)
            for size in map(int, args.sizes.split(",")):
                rows = [(weight, render_lines(str(path), SAMPLES, size=size,
                         wght=value, line_gap=1.8))
                        for weight, value in zip(WEIGHTS, range(100, 1000, 100))]
                save_shaped_sheet(args.out / f"{family.lower()}-variable-{size}{suffix.lower()}.png",
                                  f"Bloxwap {family} | website variable WOFF2 | {size}px{suffix}", rows)
            if family == "Pixel":
                for size in (16, 24):
                    rows = []
                    for rond in (0, 50, 100):
                        for weight in (400, 900):
                            rows.append((f"ROND {rond} / weight {weight}",
                                         render_lines(str(path), SAMPLES, size=size,
                                                      wght=weight, variations={"ROND": rond}, line_gap=1.8)))
                    save_shaped_sheet(args.out / f"pixel-variable-rond-{size}{suffix.lower()}.png",
                                      f"Bloxwap Pixel | website variable WOFF2 | ROND samples | {size}px{suffix}", rows)


def save_shaped_sheet(path, title, rows):
    width = max(600, max(row.width for _, row in rows))
    image = Image.new("RGB", (width, 60 + sum(row.height + 24 for _, row in rows)), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 10), title, fill="black")
    draw.text((20, 30), "HarfBuzz + FreeType; browser rasterization may differ. Visual review aid.", fill="#555555")
    y = 60
    for label, row in rows:
        draw.text((20, y), label, fill="#555555")
        image.paste(row, (0, y + 24))
        y += row.height + 24
    image.save(path)
    print(path, flush=True)


def script_previews(args):
    import uharfbuzz as hb
    from render import render_lines, shape

    for script, (language, lines) in SCRIPT_SAMPLES.items():
        families = ["Sans", "Mono", "Pixel"] if script == "core" else ["Sans" + script, "Mono" + script]
        for family in families:
            for size in (16, 24):
                rows = []
                for weight in ("Thin", "Regular", "Black"):
                    path = args.script_fonts / f"Bloxwap{family}" / "ttf" / f"Bloxwap{family}-{weight}.ttf"
                    with TTFont(path) as font:
                        required = {ord(c) for line in lines for c in line if not c.isspace()}
                        missing = required - set(font.getBestCmap())
                    if missing:
                        raise ValueError(f"{path}: missing script specimen characters: "
                                         + ", ".join(f"U+{c:04X}" for c in sorted(missing)))
                    blob = hb.Blob.from_file_path(str(path))
                    for line in lines:
                        infos, _ = shape(blob, str(path), line, size, None, (), language)
                        if any(info.codepoint == 0 for info in infos):
                            raise ValueError(f"{path}: script specimen shaped to .notdef")
                    # Additional line spacing leaves room for stacked above/below marks.
                    rows.append((weight, render_lines(str(path), lines, size=size,
                                                       lang=language, line_gap=2.0)))
                width = max(600, max(image.width for _, image in rows))
                image = Image.new("RGB", (width, 60 + sum(row.height + 24 for _, row in rows)), "white")
                draw = ImageDraw.Draw(image)
                draw.text((20, 10), f"Bloxwap {family} | {script} | {size}px | HarfBuzz + FreeType", fill="black")
                draw.text((20, 30), "Sample only; native-reader review required. Not a conformance test.", fill="#555555")
                y = 60
                for weight, row in rows:
                    draw.text((20, y), weight, fill="#555555")
                    image.paste(row, (0, y + 24))
                    y += row.height + 24
                out = args.out / f"{family.lower()}-{script.lower()}-{size}.png"
                image.save(out)
                print(out, flush=True)


def load_font(path: Path, size: int):
    font = TTFont(path)
    required = {ord(c) for line in SAMPLES for c in line if not c.isspace()}
    missing = required - set(font.getBestCmap())
    if missing:
        raise ValueError(f"{path}: missing specimen characters: "
                         + ", ".join(f"U+{c:04X}" for c in sorted(missing)))
    font.flavor = None
    stream = BytesIO()
    font.save(stream)
    stream.seek(0)
    return ImageFont.truetype(stream, size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, default=Path(__file__).resolve().parents[3]
                        / "apps/docs/public/fonts")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--families", nargs="+", default=["Sans", "Mono", "Pixel"])
    parser.add_argument("--sizes", default="12,16,20,24")
    parser.add_argument("--italic", action="store_true")
    parser.add_argument("--variable", action="store_true", help="also render actual website variable WOFF2 samples")
    parser.add_argument("--variable-only", action="store_true", help="render variable samples instead of static Latin sheets")
    parser.add_argument("--scripts", action="store_true", help="also render representative script samples")
    parser.add_argument("--scripts-only", action="store_true", help="render script samples instead of Latin sheets")
    parser.add_argument("--script-fonts", type=Path, default=Path(__file__).resolve().parents[1] / "fonts",
                        help="directory containing compiled family TTF folders")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.variable or args.variable_only:
        variable_previews(args)
    if args.scripts or args.scripts_only:
        script_previews(args)
    if args.scripts_only or args.variable_only:
        return
    for family in args.families:
        for size in map(int, args.sizes.split(",")):
            rows = []
            for weight in WEIGHTS:
                style = ("Italic" if weight == "Regular" else weight + "Italic") if args.italic else weight
                path = args.fonts / f"Bloxwap{family}" / "woff2" / f"Bloxwap{family}-{style}.woff2"
                rows.append((weight, load_font(path, size)))
            width = max(int(font.getlength(line)) for _, font in rows for line in SAMPLES) + 40
            line_height = max(sum(font.getmetrics()) for _, font in rows) + 8
            group_height = 24 + len(SAMPLES) * line_height + 16
            image = Image.new("RGB", (max(width, 600), 40 + len(rows) * group_height), "white")
            draw = ImageDraw.Draw(image)
            draw.text((20, 10), f"Bloxwap {family} | {size}px | {'italic' if args.italic else 'upright'}", fill="black")
            for row, (weight, font) in enumerate(rows):
                y = 40 + row * group_height
                draw.text((20, y), weight, fill="#555555")
                for index, line in enumerate(SAMPLES):
                    draw.text((20, y + 24 + index * line_height), line, font=font, fill="black")
            out = args.out / f"{family.lower()}-{size}{'-italic' if args.italic else ''}.png"
            image.save(out)
            print(out)


if __name__ == "__main__":
    main()
