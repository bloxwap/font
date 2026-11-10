#!/usr/bin/env python3
"""Clean-room guard (see packages/font/DESIGN.md).

Generators must not open font files. Every font binary in the repo is a
Bloxwap build (vendor BLXW, family name starts with Bloxwap).
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[3]
TOOLS = REPO / "packages" / "font" / "tools"
SCAN_ROOTS = [TOOLS / "bwfont", TOOLS / "generate.py"]
FORBIDDEN_MODULES = {"fontTools.ttLib", "freetype", "uharfbuzz"}
FORBIDDEN_PREFIXES = ("fontTools.pens",)
FONT_SUFFIXES = (".ttf", ".otf", ".woff", ".woff2", ".ttc")
# preview.py draws skeletons; it does not open font binaries.
ALLOW_FILES = set()


def _modules(node: ast.AST) -> list[str]:
    found = []
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            found.extend(alias.name for alias in child.names)
        elif isinstance(child, ast.ImportFrom) and child.module:
            found.append(child.module)
    return found


def _strings(node: ast.AST) -> list[str]:
    return [child.value for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)]


def scan_source(path: Path) -> list[str]:
    if path.name in ALLOW_FILES:
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    errors = []
    for module in _modules(tree):
        if module in FORBIDDEN_MODULES or module.startswith(FORBIDDEN_PREFIXES):
            errors.append(f"{path}: imports {module}. Generators must not read font files "
                          "(packages/font/DESIGN.md).")
    for literal in _strings(tree):
        if literal.endswith(FONT_SUFFIXES):
            errors.append(f"{path}: font filename {literal!r}. Generators must not read font files "
                          "(packages/font/DESIGN.md).")
    return errors


def scan_tree() -> list[str]:
    errors = []
    for root in SCAN_ROOTS:
        paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
        for path in paths:
            errors.extend(scan_source(path))
    return errors


def tracked_fonts() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "*.ttf", "*.otf", "*.woff", "*.woff2"],
                                  cwd=REPO, text=True)
    errors = []
    for rel in out.splitlines():
        path = REPO / rel
        with TTFont(path, recalcTimestamp=False, lazy=True) as font:
            vend = font["OS/2"].achVendID
            family = font["name"].getDebugName(16) or font["name"].getDebugName(1) or ""
            if vend != "BLXW" or not family.startswith("Bloxwap"):
                errors.append(f"{rel}: vendor {vend!r} family {family!r} is not a Bloxwap build "
                              "(packages/font/DESIGN.md).")
    return errors


def main() -> int:
    errors = scan_tree() + tracked_fonts()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("check_clean_room: generators do not read font files; shipped binaries are Bloxwap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
