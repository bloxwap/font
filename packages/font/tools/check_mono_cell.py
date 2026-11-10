#!/usr/bin/env python3
"""Fail when a Mono or Pixel glyph leaves the 600-unit cell (SIL OFL-1.1).

Every encoded advance is 0 or a positive multiple of 600. CJK ideographs and
ligatures use 1200, 1800, and so on. Zero is allowed only for Mn/Me/Cf.
Mono and Pixel set isFixedPitch only because that grid holds.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[3]
PUBLIC = REPO / "apps" / "docs" / "public" / "fonts"
CELL = 600
MARKS = {"Mn", "Me", "Cf"}


def family_of(path: Path) -> str | None:
    for part in path.parts:
        if part.startswith("Bloxwap"):
            return part
    return None


def check_font(path: Path) -> list[str]:
    family = family_of(path)
    if family is None or ("Mono" not in family and "Pixel" not in family):
        return []
    errors = []
    with TTFont(path, recalcTimestamp=False, lazy=True) as font:
        fixed = bool(font["post"].isFixedPitch)
        bad = []
        for cp, name in (font.getBestCmap() or {}).items():
            adv = font["hmtx"][name][0]
            cat = unicodedata.category(chr(cp))
            if adv == 0:
                if cat not in MARKS:
                    bad.append(f"{name} U+{cp:04X} advance 0 ({cat})")
                continue
            if adv % CELL != 0:
                bad.append(f"{name} U+{cp:04X} advance {adv}")
        if bad:
            errors.append(f"{family}/{path.name}: {len(bad)} glyphs outside the {CELL}-unit cell, "
                          f"e.g. {', '.join(bad[:4])}")
        if not fixed:
            errors.append(f"{family}/{path.name}: Mono/Pixel must set post.isFixedPitch")
        elif bad:
            errors.append(f"{family}/{path.name}: isFixedPitch is set while glyphs leave the cell")
    return errors


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv] or [PUBLIC]
    files = []
    for root in roots:
        if root.is_file():
            files.append(root)
        else:
            files.extend(p for p in root.rglob("*") if p.suffix in {".ttf", ".otf", ".woff", ".woff2"})
    errors = []
    checked = 0
    for path in sorted(files):
        found = check_font(path)
        if family_of(path) and ("Mono" in family_of(path) or "Pixel" in family_of(path)):
            checked += 1
        errors.extend(found)
    if checked == 0:
        print("check_mono_cell: no Mono or Pixel fonts found", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"check_mono_cell: {checked} Mono/Pixel fonts fit the {CELL}-unit cell")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
