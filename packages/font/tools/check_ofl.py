#!/usr/bin/env python3
"""OFL notice and Reserved Font Name on every shipped font (SIL OFL-1.1).

Name ID 0 must carry the Reserved Font Name from LICENSE. Name ID 13/14 and
fsType 0 travel with the binary. Every variable folder and subset folder
ships the same LICENSE text as the repository root.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from bwfont.meta import LICENSE, RFN, copyright_notice

REPO = LICENSE.parent
PUBLIC = REPO / "apps" / "docs" / "public"
OFL13 = "This Font Software is licensed under the SIL Open Font License, Version 1.1"
OFL14 = "https://openfontlicense.org"


def check_font(path: Path, notice: str) -> list[str]:
    errors = []
    with TTFont(path, recalcTimestamp=False, lazy=True) as font:
        name = font["name"]
        copy = name.getDebugName(0) or ""
        lic = name.getDebugName(13) or ""
        url = name.getDebugName(14) or ""
        if copy != notice:
            errors.append(f"{path}: name ID 0 is {copy!r}, expected {notice!r}")
        if not lic.startswith(OFL13):
            errors.append(f"{path}: name ID 13 does not start with the OFL notice")
        if url != OFL14:
            errors.append(f"{path}: name ID 14 is {url!r}")
        if font["OS/2"].fsType != 0:
            errors.append(f"{path}: OS/2.fsType is {font['OS/2'].fsType}, expected 0")
        vend = font["OS/2"].achVendID
        if vend != "BLXW":
            errors.append(f"{path}: vendor ID {vend!r}")
    return errors


def check_tree(root: Path, notice: str) -> list[str]:
    errors = []
    license_bytes = LICENSE.read_bytes()
    ofl = PUBLIC / "OFL.txt"
    if not ofl.is_file() or ofl.read_bytes() != license_bytes:
        errors.append(f"{ofl}: must match LICENSE")
    fonts = root if root.name == "fonts" else root / "fonts"
    if fonts.is_dir():
        for family in sorted(p for p in fonts.iterdir() if p.is_dir()):
            variable = family / "variable"
            copy = variable / "LICENSE"
            if not copy.is_file() or copy.read_bytes() != license_bytes:
                errors.append(f"{copy}: every variable folder needs LICENSE")
            subsets = variable / "subsets"
            if subsets.is_dir():
                sub = subsets / "LICENSE"
                if not sub.is_file() or sub.read_bytes() != license_bytes:
                    errors.append(f"{sub}: subset folder LICENSE drifted")
            for path in sorted(variable.rglob("*")):
                if path.suffix in {".ttf", ".otf", ".woff", ".woff2"}:
                    errors.extend(check_font(path, notice))
    og = REPO / "apps" / "docs" / "assets" / "og"
    for path in sorted(og.glob("*.ttf")):
        errors.extend(check_font(path, notice))
    return errors


def main(argv: list[str]) -> int:
    notice = copyright_notice()
    roots = [Path(a) for a in argv] or [PUBLIC]
    errors = []
    for root in roots:
        errors.extend(check_tree(root if root.name != "fonts" else root.parent, notice))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("check_ofl: Reserved Font Name and OFL records match LICENSE")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
