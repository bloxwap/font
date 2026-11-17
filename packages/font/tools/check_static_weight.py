#!/usr/bin/env python3
"""Named static instances use usWeightClass 100–900 (SIL OFL-1.1)."""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from bwfont.build import WEIGHTS

TIERS = {name: weight for weight, name, _stem in WEIGHTS}


def weight_of_filename(name: str) -> int | None:
    stem = Path(name).stem
    if "[" in stem or "Variable" in stem:
        return None
    italic = stem.endswith("Italic")
    if italic:
        stem = stem[: -len("Italic")]
    if stem.endswith("-"):
        stem = stem[:-1]
    if "-" not in stem:
        # BloxwapSans-Italic names the Regular italic face.
        return TIERS["Regular"] if italic else None
    return TIERS.get(stem.split("-")[-1])


def check_file(path: Path) -> str | None:
    expected = weight_of_filename(path.name)
    if expected is None:
        return None
    with TTFont(path, recalcTimestamp=False, lazy=True) as font:
        if "fvar" in font:
            return None
        actual = font["OS/2"].usWeightClass
    if actual != expected:
        return f"{path}: usWeightClass {actual}, expected {expected} ({path.name})"
    return None


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv]
    if not roots:
        print("usage: check_static_weight.py FONT_OR_DIR ...", file=sys.stderr)
        return 2
    files = []
    for root in roots:
        if root.is_file():
            files.append(root)
        else:
            files.extend(p for p in root.rglob("*") if p.suffix in {".ttf", ".otf", ".woff", ".woff2"})
    errors = [msg for path in sorted(files) if (msg := check_file(path))]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"check_static_weight: {len(files)} files use named usWeightClass tiers")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
