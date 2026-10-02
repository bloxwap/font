#!/usr/bin/env python3
"""Check that Unicode input retains its identity independently of OpenType alternates.

Usage: .venv/bin/python tools/check_unicode.py [font ...]
Without paths, inspect upright and italic variable fonts in every built family.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from site_data import FAMILIES, find_variable, gsub_map

# These are intentionally stylistic, not separately encoded Unicode characters.
STYLISTIC = re.compile(r"\.(?:ss\d\d|cv\d\d|zero|pnum|sc|sups|subs|numr|dnom|code)$")


def unicode_errors(font: TTFont) -> list[str]:
    cmap = font.getBestCmap() or {}
    errors = []
    if not cmap:
        return ["No Unicode cmap"]
    names = set(font.getGlyphOrder())
    for table in font['cmap'].tables:
        if not table.isUnicode() or table.format == 14:
            continue
        for cp, glyph in table.cmap.items():
            if not 0 <= cp <= 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
                errors.append(f"Invalid Unicode scalar U+{cp:04X}")
            if cmap.get(cp) != glyph:
                errors.append(f"Inconsistent Unicode mapping U+{cp:04X}: {glyph}")
            if glyph not in names or glyph == '.notdef':
                errors.append(f"U+{cp:04X} maps to missing character {glyph}")
            if STYLISTIC.search(glyph):
                errors.append(f"Stylistic glyph {glyph} is encoded at U+{cp:04X}")
    # Same-script confusables must remain separate logical characters.
    for sample in ('Il1', '0O', 'rnm', 'cld'):
        mapped = [cmap.get(ord(ch)) for ch in sample]
        if None in mapped or len(set(mapped)) != len(mapped):
            errors.append(f"Characters in {sample!r} do not have distinct cmap entries")
    reach, _ = gsub_map(font, cmap)
    for glyph, (text, feature) in reach.items():
        if not text or any(ord(ch) not in cmap for ch in text):
            errors.append(f"{glyph} via {feature} has no valid source Unicode text")
    return sorted(set(errors))


def main() -> int:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        for fid, stem, *_ in FAMILIES:
            upright, italic = find_variable(fid, stem)
            paths.extend(p for p in (upright, italic) if p)
    if not paths:
        print('No fonts found', file=sys.stderr)
        return 1
    failures = 0
    for path in paths:
        with TTFont(path) as font:
            errors = unicode_errors(font)
        failures += len(errors)
        for error in errors:
            print(f'FAIL {path.name}: {error}')
    print(f'Unicode integrity: {len(paths)} fonts checked, {failures} errors')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
