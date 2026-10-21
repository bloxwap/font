#!/usr/bin/env python3
"""Web font stylesheet + cache-busting version for the Bloxwap Font website (apps/docs/).

Writes:
    apps/docs/public/fonts/<PS>/variable/subsets/  core variable WOFF2s (--subsets)
    apps/docs/public/bloxwap-font.css   one family name per style ("Bloxwap Sans",
                                   "Bloxwap Mono", "Bloxwap Pixel"). Companion families
                                   are merged into the same family name
                                   with unicode-range, so `font-family: "Bloxwap Sans"`
                                   renders every supported script and browsers
                                   only download the files a page actually needs.
                                   Every companion is also exposed under its own name
                                   ("Bloxwap Sans KR", ...).
    apps/docs/lib/font-version.ts       FONT_VERSION, a content hash of the web fonts, which the
                                   app appends to font/CSS URLs (?v=...) for cache-busting.

Called by tools/postprocess.py (stamp_site) after every build, and by
tools/site_data.py --dev-fonts. Run directly to regenerate:
    .venv/bin/python tools/webfonts.py --subsets
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.unicodedata import script, script_extension

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT.parent.parent / "apps" / "docs"
PUBLIC = DOCS / "public"
VERSION_TS = DOCS / "lib" / "font-version.ts"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bwfont.families import FAMILIES  # noqa: E402

# Combined family -> (base family id, companion ids in priority order). A code point found
# in several companions goes to the first one listed: shared CJK punctuation is served by
# SC (Chinese text uses it constantly; Korean text rarely does).
GROUPS = {
    "sans": ("sans", ["sans-sc", "sans-jp", "sans-kr", "sans-arabic", "sans-hebrew",
                      "sans-armenian", "sans-georgian"]),
    "mono": ("mono", ["mono-sc", "mono-jp", "mono-kr", "mono-arabic", "mono-hebrew",
                      "mono-armenian", "mono-georgian"]),
    "pixel": ("pixel", []),
}

# Keep complete Latin words (including IPA, Vietnamese and combining accents)
# in one shaping font. Script properties cover Latin outside the usual blocks;
# these common ranges cover punctuation, spacing, currency and code operators.
# Script fonts also carry the explicit shared set below. Combining clusters and
# punctuation must remain in the same shaping font as their script letters.
SUBSET_RANGES = {
    "latin": "0000-02FF,2000-206F,2070-209F,20A0-20CF,2113,2116,2122,2E00-2E7F,FEFF,FFFD",
}

# Shared by every text script: ASCII/Latin-1 punctuation and numbers, modifier
# symbols, combining marks, spacing/punctuation, superscripts, currency, and
# encoded outputs of the ASCII arrow ligatures. No letter is shared except the
# Latin-1 Common characters (e.g. the micro sign). Keep this policy explicit so
# coverage tests reject accidental overlap into another script's letters.
SHARED_RANGES = "0000-0040,005B-0060,007B-00BF,00D7,00F7,02B9-02FF,0300-036F,0374,037E,0387,1AB0-1AFF,1DC0-1DFF,2000-206F,2070-209F,20A0-20CF,2113,2116,2122,2190,2192,2194,21D2,2E00-2E7F,FE20-FE2F,FEFF,FFFD"
SHARED_CODEPOINTS = frozenset(cp for cp in subset.parse_unicodes(SHARED_RANGES)
                             if script(cp) in {"Zyyy", "Zinh"})


def core_subsets(cps: set[int]) -> dict[str, set[int]]:
    """Cover the full cmap, with overlap confined to SHARED_CODEPOINTS."""
    greek = {cp for cp in cps if script(cp) == "Grek" or script_extension(cp) == {"Grek"}}
    cyrillic = {cp for cp in cps if script(cp) == "Cyrl" or script_extension(cp) == {"Cyrl"}}
    latin = {cp for cp in cps if script(cp) in {"Latn", "Zinh"}}
    latin |= cps & set(subset.parse_unicodes(SUBSET_RANGES["latin"]))
    latin -= greek | cyrillic
    groups = {"latin": latin, "greek": greek, "cyrillic": cyrillic,
              "other": cps - latin - greek - cyrillic}
    shared = cps & SHARED_CODEPOINTS
    for name in ["latin", "greek", "cyrillic"]:
        groups[name] |= shared
    return {name: mine for name, mine in groups.items() if mine}


def subset_path(source: Path, name: str) -> Path:
    return source.parent / "subsets" / f"{source.stem}.{name}.woff2"


def write_subsets(public: Path = PUBLIC):
    """Subset the shipped WOFF2s without rebuilding, editing or instancing outlines.

    Fixed source timestamps, glyph ordering and fontTools' canonical table order
    make repeat invocations byte-identical. Full web/desktop fonts stay intact.
    """
    for fid in GROUPS:
        for _style, source in _faces(fid, public):
            with TTFont(source, recalcTimestamp=False) as full:
                groups = core_subsets(set(full.getBestCmap()))
            dest = source.parent / "subsets"
            dest.mkdir(exist_ok=True)
            shutil.copyfile(ROOT.parent.parent / "LICENSE", dest / "LICENSE")
            (dest / "package.json").write_text('{"private":true,"license":"OFL-1.1"}\n')
            for name, cps in groups.items():
                options = subset.Options()
                options.layout_features = ["*"]
                options.hinting = True
                options.glyph_names = True
                options.notdef_glyph = True
                options.notdef_outline = True
                options.name_languages = ["*"]
                options.name_legacy = True
                options.recalc_timestamp = False
                options.prune_unicode_ranges = False
                options.prune_codepage_ranges = False
                with TTFont(source, recalcTimestamp=False, recalcBBoxes=False) as font:
                    # '*' retains only IDs below 256 plus referenced IDs in
                    # fontTools. Explicit IDs also preserve unused feature names.
                    options.name_IDs = ["*", *sorted({record.nameID for record in font['name'].names})]
                    options.passthrough_tables = True
                    options.drop_tables = []
                    sub = subset.Subsetter(options=options)
                    sub.populate(unicodes=sorted(cps))
                    sub.subset(font)
                    # OS/2.compile otherwise rewrites first/last character fields.
                    # Carry the source table verbatim, including all metrics and
                    # coverage flags; the exact cmap is recorded by the subset.
                    os2 = DefaultTable("OS/2")
                    os2.data = font.reader["OS/2"]
                    font["OS/2"] = os2
                    font.flavor = "woff2"
                    target = subset_path(source, name)
                    font.save(target)
                print(f"subsets: {target.name}: {target.stat().st_size:,} B ({len(cps)} code points)")
            # Remove obsolete outputs if the source's coverage ever shrinks.
            for old in dest.glob("*.woff2"):
                if old.name.startswith(source.stem + ".") and old not in {subset_path(source, name) for name in groups}:
                    old.unlink()


def _faces(fid: str, public: Path) -> list[tuple[str, Path]]:
    """[(style, woff2 path)] for a family's variable web fonts, upright first."""
    ps = FAMILIES[fid].ps
    d = public / "fonts" / ps / "variable"
    if not d.is_dir():
        return []
    out = [("normal", p) for p in sorted(d.glob(f"{ps}[[]*].woff2"))[:1]]
    out += [("italic", p) for p in sorted(d.glob(f"{ps}-Italic[[]*].woff2"))[:1]]
    return out


def _facts(fid: str, woff2: Path) -> tuple[set[int], tuple[int, int]]:
    # Describe the actual web artifact, independent of any local desktop build.
    f = TTFont(woff2, lazy=True)
    cps = set((f.getBestCmap() or {}).keys())
    wght = (100, 900)
    if "fvar" in f:
        for a in f["fvar"].axes:
            if a.axisTag == "wght":
                wght = (int(a.minValue), int(a.maxValue))
    f.close()
    return cps, wght


def _block_index(cp: int) -> int:
    from fontTools.unicodedata import Blocks
    return bisect.bisect_right(Blocks.RANGES, cp) - 1


def _ranges(mine: set[int], others: set[int]) -> list[tuple[int, int]]:
    """Compress code points to ranges. Two runs are merged across a gap when the gap holds
    none of the other faces' code points and both runs sit in the same Unicode block, so a
    font with 3,500 scattered hanzi becomes one CJK range instead of thousands."""
    runs: list[list[int]] = []
    for cp in sorted(mine):
        if runs and cp == runs[-1][1] + 1:
            runs[-1][1] = cp
        else:
            runs.append([cp, cp])
    merged: list[list[int]] = []
    other_sorted = sorted(others)
    for r in runs:
        if merged:
            prev = merged[-1]
            gap_lo, gap_hi = prev[1] + 1, r[0] - 1
            i = bisect.bisect_left(other_sorted, gap_lo)
            clear = i >= len(other_sorted) or other_sorted[i] > gap_hi
            if clear and _block_index(prev[1]) == _block_index(r[0]):
                prev[1] = r[1]
                continue
        merged.append(list(r))
    return [(a, b) for a, b in merged]


def _urange(ranges: list[tuple[int, int]]) -> str:
    return ", ".join(f"U+{a:X}" if a == b else f"U+{a:X}-{b:X}" for a, b in ranges)


def _url(path: Path, public: Path, version: str) -> str:
    rel = path.relative_to(public).as_posix()
    return f"{quote(rel, safe='/')}?v={version}"


def font_version(public: Path = PUBLIC) -> str:
    h = hashlib.sha1()
    for p in sorted((public / "fonts").rglob("*.woff2")):
        h.update(p.relative_to(public).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:10]


def _face(family: str, url: str, style: str, wght: tuple[int, int], urange: str | None) -> str:
    lines = [
        "@font-face {",
        f'  font-family: "{family}";',
        f'  src: url("{url}") format("woff2");',
        f"  font-weight: {wght[0]} {wght[1]};",
        f"  font-style: {style};",
        "  font-display: swap;",
    ]
    if urange:
        lines.append(f"  unicode-range: {urange};")
    lines.append("}")
    return "\n".join(lines)


def write_css(public: Path = PUBLIC, version: str | None = None) -> str:
    """Write apps/docs/public/bloxwap-font.css and apps/docs/lib/font-version.ts; return the version."""
    version = version or font_version(public)
    facts: dict[str, list[tuple[str, Path, set[int], tuple[int, int]]]] = {}
    for fid in FAMILIES:
        rows = []
        for style, p in _faces(fid, public):
            cps, wght = _facts(fid, p)
            rows.append((style, p, cps, wght))
        if rows:
            facts[fid] = rows

    out = [
        "/*",
        " * Bloxwap Font — https://bloxwap.github.io/font/",
        " * GENERATED by tools/webfonts.py (run by tools/postprocess.py). Do not edit by hand.",
        " * SIL Open Font License 1.1. © 2026 Bloxwap, Inc.",
        " *",
        " * Core subsets and companion scripts share family names via unicode-range,",
        " * so browsers download only the files used by a page's text.",
        " */",
    ]
    standalone: list[str] = []
    for gid, (base, companions) in GROUPS.items():
        if base not in facts:
            continue
        family = FAMILIES[base].name
        present = [c for c in companions if c in facts]
        base_cps = facts[base][0][2]
        # Code points each companion contributes: not in the base, not in a higher-priority companion.
        claimed: dict[str, set[int]] = {}
        taken = set(base_cps)
        for c in present:
            claimed[c] = facts[c][0][2] - taken
            taken |= claimed[c]
        scripts = ", ".join(FAMILIES[c].name.replace(family + " ", "") for c in present if claimed[c])
        out.append("")
        out.append(f"/* {family}" + (f" (+ {scripts} via unicode-range)" if present else "") + " */")
        for style, p, cps, wght in facts[base]:
            others = set().union(*claimed.values()) if claimed else set()
            groups = core_subsets(cps)
            # Later matching faces win for shared characters. Latin therefore
            # supplies common characters unless a script cluster needs its face.
            for name in ["other", "cyrillic", "greek", "latin"]:
                mine = groups[name]
                path = subset_path(p, name)
                if not path.is_file():
                    raise FileNotFoundError(f"{path}: run tools/webfonts.py --subsets first")
                urange = _urange(_ranges(mine, (cps - mine) | others))
                out.append(_face(family, _url(path, public, version), style, wght, urange))
        for c in present:
            mine = claimed[c]
            if not mine:
                continue
            others = (taken - mine)
            style, p, _cps, wght = facts[c][0]
            out.append(_face(family, _url(p, public, version), "normal", wght, _urange(_ranges(mine, others))))
            # Use the companion's italic when available; upright-only scripts
            # retain their own design in an italic Latin paragraph.
            if any(s == "italic" for s, *_ in facts[base]):
                _style, italic_path, _cps, italic_wght = next(
                    (row for row in facts[c] if row[0] == "italic"), facts[c][0])
                out.append(_face(family, _url(italic_path, public, version), "italic", italic_wght,
                                 _urange(_ranges(mine, others))))
        for c in present:
            for style, p, _cps, wght in facts[c]:
                standalone.append(_face(FAMILIES[c].name, _url(p, public, version), style, wght, None))
    if standalone:
        out.append("")
        out.append("/* Companion families under their own names (complete fonts, including Latin). */")
        out.extend(standalone)
    css = "\n".join(out) + "\n"
    (public / "bloxwap-font.css").write_text(css, encoding="utf-8")
    if public.resolve() != PUBLIC.resolve():  # a scratch/test directory: leave the app's constant alone
        return version
    VERSION_TS.parent.mkdir(parents=True, exist_ok=True)
    VERSION_TS.write_text(
        "// GENERATED by tools/webfonts.py (run by tools/postprocess.py). Do not edit by hand.\n"
        "// A content hash of apps/docs/public/fonts/**/*.woff2, appended to font and stylesheet URLs\n"
        "// so browsers never keep stale fonts (or a cached 404) after a release.\n"
        f"export const FONT_VERSION = '{version}';\n",
        encoding="utf-8",
    )
    print(f"webfonts: {len(facts)} families -> {(public / 'bloxwap-font.css').relative_to(ROOT.parent.parent)} (v={version})")
    return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subsets", action="store_true", help="generate core subsets from shipped variable WOFF2s first")
    args = parser.parse_args()
    if args.subsets:
        write_subsets()
    write_css()
