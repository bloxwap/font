#!/usr/bin/env python3
"""Committed web CSS, subsets and FONT_VERSION match the variable WOFF2s.

Regenerates subsets and the stylesheet in a scratch copy and diffs them
against apps/docs/public and apps/docs/lib/font-version.ts.
"""
from __future__ import annotations

import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

import webfonts

REPO = Path(__file__).resolve().parents[3]
PUBLIC = REPO / "apps" / "docs" / "public"
VERSION_TS = REPO / "apps" / "docs" / "lib" / "font-version.ts"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "public"
        shutil.copytree(PUBLIC / "fonts", dest / "fonts")
        for subsets in dest.rglob("subsets"):
            if subsets.is_dir():
                shutil.rmtree(subsets)
        webfonts.write_subsets(dest)
        version = webfonts.font_version(dest)
        webfonts.write_css(dest, version=version)
        errors = []
        if f"export const FONT_VERSION = '{version}';" not in VERSION_TS.read_text(encoding="utf-8"):
            errors.append(f"FONT_VERSION is not {version}")
        committed_css = (PUBLIC / "bloxwap-font.css").read_text(encoding="utf-8")
        fresh_css = (dest / "bloxwap-font.css").read_text(encoding="utf-8")
        if committed_css != fresh_css:
            errors.append("bloxwap-font.css drifted from the committed variable fonts")
        for fresh in sorted((dest / "fonts").rglob("*")):
            if not fresh.is_file():
                continue
            rel = fresh.relative_to(dest / "fonts")
            committed = PUBLIC / "fonts" / rel
            if not committed.is_file() or not filecmp.cmp(fresh, committed, shallow=False):
                errors.append(f"fonts/{rel} drifted")
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
    print(f"check_generated: CSS, subsets and FONT_VERSION match ({version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
