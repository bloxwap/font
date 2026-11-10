#!/usr/bin/env python3
"""Write the OFL copyright, source date and named weight class into shipped binaries.

Used for families whose outlines did not change. Mono rebuilds already carry
these records from the generator. Saves with bounding boxes left as they are.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.misc.timeTools import timestampNow
from fontTools.ttLib import TTFont

from bwfont.meta import copyright_notice
from check_static_weight import weight_of_filename
from toolchain import ensure_source_date_epoch

REPO = Path(__file__).resolve().parents[3]


def stamp(path: Path, notice: str) -> None:
    font = TTFont(path, recalcTimestamp=False, recalcBBoxes=False)
    stamp_time = timestampNow()
    font["head"].created = stamp_time
    font["head"].modified = stamp_time
    for record in font["name"].names:
        if record.nameID == 0:
            font["name"].setName(notice, 0, record.platformID, record.platEncID, record.langID)
    if "fvar" not in font:
        weight = weight_of_filename(path.name)
        if weight is not None:
            font["OS/2"].usWeightClass = weight
    font["OS/2"].fsType = 0
    font.save(path, reorderTables=False)
    font.close()


def main(argv: list[str]) -> int:
    ensure_source_date_epoch()
    notice = copyright_notice()
    roots = [Path(a) for a in argv] or [
        REPO / "apps/docs/public/fonts",
        REPO / "apps/docs/assets/og",
    ]
    count = 0
    for root in roots:
        files = [root] if root.is_file() else sorted(
            p for p in root.rglob("*") if p.suffix in {".ttf", ".otf", ".woff", ".woff2"} and "subsets" not in p.parts)
        for path in files:
            stamp(path, notice)
            count += 1
            print(path)
    print(f"stamped {count} fonts")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
