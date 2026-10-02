"""Bitmap registry for Bloxwap Pixel.

Glyphs are drawn as ASCII art in *blocks*: several glyphs side by side, one
header line naming them and one line per pixel row, each row prefixed with
its row number (row 0 sits on the baseline, row 4 is the top x-height row,
row 6 the top cap row, negative rows are descenders)::

    :     A     B
    6   .###. ####.
    5   #...# #...#
    ...

Header tokens:
    single character      -> encoded glyph for that character
    U+XXXX                -> encoded glyph for that codepoint
    name                  -> unencoded glyph (e.g. ``a.ss01``)
    name=U+XXXX[,U+YYYY]  -> named glyph with explicit codepoints

Row tokens use ``#`` for an "on" pixel and ``.`` for "off".  A token's width
is the glyph's frame width; frames are centred in the 600-unit cell, so the
usual 5-wide frame puts pixel centres at x = 100, 200 … 500 (a 1-pixel gap is
left between neighbouring cells).
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from fontTools import agl

CELL = 100          # one pixel = 100 font units
ADV = 600           # monospaced advance (6 columns)

# names the shared composite tables (ALIASES/RECIPES/SOFT_DOTTED) refer to
SPECIAL_NAMES = {
    0x131: "dotlessi", 0x237: "dotlessj", 0x18F: "Schwa", 0x259: "schwa",
    0x19F: "Obarred", 0x275: "obarred", 0x1E9E: "Germandbls", 0x3BC: "mu",
    0x394: "Delta", 0x3A9: "Omega", 0x2032: "minute", 0x2033: "second",
    0x2019: "quoteright", 0x2018: "quoteleft", 0x201B: "quotereversed",
    0x2212: "minus", 0x2044: "fraction", 0x7C: "bar", 0x21: "exclam",
    0x2D: "hyphen", 0x2F: "slash", 0xB7: "periodcentered", 0x3A: "colon",
    0x27: "quotesingle", 0x3A0: "Pi", 0x3A3: "Sigma", 0x3B9: "iota",
}


def name_for(cp: int) -> str:
    if cp in SPECIAL_NAMES:
        return SPECIAL_NAMES[cp]
    n = agl.UV2AGL.get(cp)
    if n and n.isalnum() and n not in _RESERVED and not n.startswith("afii"):
        return n
    return f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"


# AGL names already claimed by SPECIAL_NAMES for another codepoint
_RESERVED = {v for k, v in SPECIAL_NAMES.items()}
for _k, _v in SPECIAL_NAMES.items():
    if agl.UV2AGL.get(_k) == _v:
        _RESERVED.discard(_v)


@dataclass
class PixelDef:
    name: str
    unicodes: list
    pix: set = field(default_factory=set)      # {(x_centre, row)}
    kind: str = "base"                         # base | mark | space
    anchors: dict = field(default_factory=dict)   # explicit anchors (units)
    comps: list = field(default_factory=list)  # (glyph, dx, dy)
    shapes: object = None                      # callable(s, rond) -> [Contour]  (box drawing)
    shear: bool = True                         # italic shear applies
    advance: int = ADV
    frame: int = 5


REG: dict[str, PixelDef] = {}
ORDER: list[str] = []


def add(d: PixelDef):
    if d.name in REG:
        raise ValueError(f"duplicate pixel glyph {d.name}")
    REG[d.name] = d
    ORDER.append(d.name)
    return d


def _parse_header_token(tok):
    if "=" in tok and len(tok) > 1:
        name, cps = tok.split("=", 1)
        return name, [int(c[2:], 16) for c in cps.split(",")]
    if tok.startswith("U+") and len(tok) > 3:
        cp = int(tok[2:], 16)
        return name_for(cp), [cp]
    if len(tok) == 1:
        cp = ord(tok)
        return name_for(cp), [cp]
    return tok, []


def frame_x0(width: int) -> int:
    """x of the first pixel centre for a frame `width` pixels wide."""
    return (ADV - width * CELL) // 2 + CELL // 2


SKIPPED_DUPES = []


def parse(block: str, kind="base", skip_existing=False, **kw):
    """Parse a block and register its glyphs.  Returns list of names."""
    lines = [l.rstrip() for l in block.strip("\n").splitlines() if l.strip()]
    header = None
    rows = []
    for l in lines:
        s = l.strip()
        if s.startswith("#!"):
            continue
        if s.startswith(":"):
            if header is not None and rows:
                _emit(header, rows, kind, kw, skip_existing)
                rows = []
            header = s[1:].split()
            continue
        parts = s.split()
        rows.append((int(parts[0]), parts[1:]))
    if header is not None:
        _emit(header, rows, kind, kw, skip_existing)


def _emit(header, rows, kind, kw, skip_existing=False):
    for j, tok in enumerate(header):
        name, cps = _parse_header_token(tok)
        width = None
        pix = set()
        for r, toks in rows:
            if len(toks) != len(header):
                raise ValueError(f"row {r} has {len(toks)} tokens, header {len(header)}: {header}")
            t = toks[j]
            if width is None:
                width = len(t)
            elif len(t) != width:
                raise ValueError(f"{name}: inconsistent width in row {r}")
            x0 = frame_x0(len(t))
            for i, ch in enumerate(t):
                if ch == "#":
                    pix.add((x0 + i * CELL, r))
                elif ch not in ".":
                    raise ValueError(f"{name}: bad char {ch!r}")
        if skip_existing and name in REG:
            SKIPPED_DUPES.append(name)
            continue
        add(PixelDef(name, list(cps), pix, kind=kind, frame=width or 5, **kw))


# ---------------------------------------------------------------------------
# derived bitmaps
# ---------------------------------------------------------------------------

def pix_of(name):
    return set(REG[name].pix)


def mirror(pix):
    return {(ADV - x, r) for x, r in pix}


def flip(pix, axis_rows):
    """Vertical flip: row r -> axis_rows - r."""
    return {(x, axis_rows - r) for x, r in pix}


def rot180(pix, axis_rows):
    return {(ADV - x, axis_rows - r) for x, r in pix}


def shift(pix, dx=0, dy=0):
    return {(x + dx * CELL, r + dy) for x, r in pix}


def union(*ps):
    out = set()
    for p in ps:
        out |= set(p)
    return out


def derive(name, cps, pix, **kw):
    if isinstance(cps, int):
        cps = [cps]
    return add(PixelDef(name, list(cps), set(pix), **kw))


def derive_cp(cp, pix, **kw):
    return derive(name_for(cp), [cp], pix, **kw)


def alias(cp, src, dx=0, dy=0):
    """Encoded glyph that is a single component of another glyph."""
    d = PixelDef(name_for(cp), [cp], set(), comps=[(src, dx, dy)])
    return add(d)


def char_name(ch):
    return name_for(ord(ch))


def rows_of(pix):
    return sorted({r for _, r in pix})


def describe(name):
    d = REG[name]
    rs = rows_of(d.pix)
    xs = sorted({x for x, _ in d.pix})
    out = []
    for r in range(max(rs), min(rs) - 1, -1):
        out.append(f"{r:3d} " + "".join("#" if (x, r) in d.pix else "." for x in range(0, ADV + 1, CELL)))
    return "\n".join(out)
