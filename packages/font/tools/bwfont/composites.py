"""Composite (accented / aliased) glyph recipes.

A recipe is a list of (glyph name, attach) where attach is one of:
    None            the base, placed at origin
    'top'|'bottom'|'ogonek'|'horn'|'center'|'caron'   anchor attachment
Recipes are derived from Unicode NFD decompositions plus a table of
overrides for orthographic conventions.
"""
from __future__ import annotations

import unicodedata

from fontTools import agl

# combining mark codepoint -> (glyph name, anchor class)
MARKS = {
    0x300: ("gravecomb", "top"),
    0x301: ("acutecomb", "top"),
    0x302: ("circumflexcomb", "top"),
    0x303: ("tildecomb", "top"),
    0x304: ("macroncomb", "top"),
    0x306: ("brevecomb", "top"),
    0x307: ("dotaccentcomb", "top"),
    0x308: ("dieresiscomb", "top"),
    0x309: ("hookabovecomb", "top"),
    0x30A: ("ringcomb", "top"),
    0x30B: ("hungarumlautcomb", "top"),
    0x30C: ("caroncomb", "top"),
    0x30D: ("verticallineabovecomb", "top"),
    0x30F: ("dblgravecomb", "top"),
    0x311: ("invertedbrevecomb", "top"),
    0x312: ("commaturnedabovecomb", "top"),
    0x313: ("commaabovecomb", "top"),
    0x314: ("reversedcommaabovecomb", "top"),
    0x31B: ("horncomb", "horn"),
    0x323: ("dotbelowcomb", "bottom"),
    0x324: ("dieresisbelowcomb", "bottom"),
    0x325: ("ringbelowcomb", "bottom"),
    0x326: ("commaaccentcomb", "bottom"),
    0x327: ("cedillacomb", "bottom"),
    0x328: ("ogonekcomb", "ogonek"),
    0x329: ("verticallinebelowcomb", "bottom"),
    0x32D: ("circumflexbelowcomb", "bottom"),
    0x32E: ("brevebelowcomb", "bottom"),
    0x330: ("tildebelowcomb", "bottom"),
    0x331: ("macronbelowcomb", "bottom"),
    0x332: ("lowlinecomb", "bottom"),
    0x335: ("strokeshortcomb", "center"),
    0x336: ("strokelongcomb", "center"),
    0x338: ("slashlongcomb", "center"),
    0x342: ("perispomenicomb", "top"),
    0x345: ("ypogegrammenicomb", "bottom"),
}

VIET = {
    ("circumflexcomb", "acutecomb"): "circumflexcomb_acutecomb",
    ("circumflexcomb", "gravecomb"): "circumflexcomb_gravecomb",
    ("circumflexcomb", "hookabovecomb"): "circumflexcomb_hookabovecomb",
    ("circumflexcomb", "tildecomb"): "circumflexcomb_tildecomb",
    ("brevecomb", "acutecomb"): "brevecomb_acutecomb",
    ("brevecomb", "gravecomb"): "brevecomb_gravecomb",
    ("brevecomb", "hookabovecomb"): "brevecomb_hookabovecomb",
    ("brevecomb", "tildecomb"): "brevecomb_tildecomb",
}

# Visual aliases: codepoint -> glyph to reuse as a single component.
ALIASES = {}


def _alias_pairs(pairs):
    for cp, name in pairs:
        ALIASES[cp] = name


# Greek capitals that are Latin look-alikes
_alias_pairs([
    (0x391, "A"), (0x392, "B"), (0x395, "E"), (0x396, "Z"), (0x397, "H"),
    (0x399, "I"), (0x39A, "K"), (0x39C, "M"), (0x39D, "N"), (0x39F, "O"),
    (0x3A1, "P"), (0x3A4, "T"), (0x3A5, "Y"), (0x3A7, "X"),
    (0x3BF, "o"), (0x3F2, "c"), (0x3F3, "j"), (0x37F, "J"), (0x3F9, "C"),
])
# Cyrillic look-alikes
_alias_pairs([
    (0x405, "S"), (0x406, "I"), (0x408, "J"), (0x410, "A"), (0x412, "B"),
    (0x415, "E"), (0x41A, "K"), (0x41C, "M"), (0x41D, "H"), (0x41E, "O"),
    (0x420, "P"), (0x421, "C"), (0x422, "T"), (0x425, "X"), (0x4AE, "Y"),
    (0x4C0, "I"), (0x51A, "Q"), (0x51C, "W"),
    (0x430, "a"), (0x435, "e"), (0x43E, "o"), (0x440, "p"), (0x441, "c"),
    (0x443, "y"), (0x445, "x"), (0x455, "s"), (0x456, "i"), (0x458, "j"),
    (0x4BB, "h"), (0x4CF, "l"), (0x51B, "q"), (0x51D, "w"), 
    (0x4D8, "Schwa"), (0x4D9, "schwa"), (0x4E8, "Obarred"), (0x4E9, "obarred"),
])
# Latin-internal look-alikes
_alias_pairs([
    (0x1C0, "bar"), (0x1C3, "exclam"), (0x2BC, "quoteright"), (0x2BB, "quoteleft"),
    (0x2BD, "quotereversed"), (0x2B9, "minute"), (0x2BA, "second"), (0x2C8, "quotesingle"),
    (0x2010, "hyphen"), (0x2011, "hyphen"), (0xAD, "hyphen"),
    (0x2212, "minus"), (0x2215, "slash"), (0x2219, "periodcentered"),
    (0x2236, "colon"), (0x2223, "bar"), (0x2044, "fraction"),
    (0x3BC, "mu"), (0xB5, "mu"), (0x2126, "Omega"), (0x3A9, "Omega"),
    (0x2206, "Delta"), (0x394, "Delta"), (0x220F, "Pi"), (0x3A0, "Pi"),
    (0x2211, "Sigma"), (0x3A3, "Sigma"), (0x212A, "K"), (0x212B, "Aring"),
    (0x2160, "I"), (0x2164, "V"), (0x2169, "X"), (0x216C, "L"), (0x216D, "C"), (0x216E, "D"), (0x216F, "M"),
    (0x2170, "i"), (0x2174, "v"), (0x2179, "x"), (0x217C, "l"), (0x217D, "c"), (0x217E, "d"), (0x217F, "m"),
    (0x1E9E, "Germandbls"), (0x201B, "quotereversed"),
    (0x3B9, "iota"), (0x37E, "semicolon"), (0x387, "periodcentered"),
    (0xFF0D, "minus"),
])

# Explicit recipes: codepoint -> list of (glyph, attach)
RECIPES = {
    0x123: [("g", None), ("commaturnedabovecomb", "top")],                 # ģ
    0x122: [("G", None), ("commaaccentcomb", "bottom")],                    # Ģ
    0x136: [("K", None), ("commaaccentcomb", "bottom")],
    0x137: [("k", None), ("commaaccentcomb", "bottom")],
    0x13B: [("L", None), ("commaaccentcomb", "bottom")],
    0x13C: [("l", None), ("commaaccentcomb", "bottom")],
    0x145: [("N", None), ("commaaccentcomb", "bottom")],
    0x146: [("n", None), ("commaaccentcomb", "bottom")],
    0x156: [("R", None), ("commaaccentcomb", "bottom")],
    0x157: [("r", None), ("commaaccentcomb", "bottom")],
    0x10F: [("d", None), ("caroncomb.alt", "caron")],                       # ď
    0x13E: [("l", None), ("caroncomb.alt", "caron")],                       # ľ
    0x165: [("t", None), ("caroncomb.alt", "caron")],                       # ť
    0x13D: [("L", None), ("caroncomb.alt", "caron")],                       # Ľ
    0x13F: [("L", None), ("periodcentered", "dotright")],                   # Ŀ
    0x140: [("l", None), ("periodcentered", "dotright")],                   # ŀ
    0x149: [("quoteright", "prefix"), ("n", None)],                         # ŉ
    0x1E9E: None,
}

# Greek: tonos on capitals is placed to the left
GREEK_TONOS_CAPS = {0x386: "A", 0x388: "E", 0x389: "H", 0x38A: "I", 0x38C: "O", 0x38E: "Y", 0x38F: "Omega"}

SOFT_DOTTED = {"i": "dotlessi", "j": "dotlessj", "i.cy": "dotlessi", "je.cy": "dotlessj"}


def glyph_name(cp: int) -> str:
    n = agl.UV2AGL.get(cp)
    if n and n.isalnum() and cp < 0x500:
        return n
    return f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"


def recipe_for(cp: int, have, is_case_base):
    """Return a recipe for codepoint cp given the set of available glyph
    names, or None.  `is_case_base(name)` tells if marks should use .case."""
    if cp in ALIASES:
        n = ALIASES[cp]
        return [(n, None)] if n in have else None
    if cp in RECIPES:
        r = RECIPES[cp]
        if r is None:
            return None
        return r if all(n in have for n, _ in r) else None
    if cp in GREEK_TONOS_CAPS:
        base = GREEK_TONOS_CAPS[cp]
        return [(base, None), ("tonoscomb", "tonos_left")] if base in have else None
    ch = chr(cp)
    nfd = unicodedata.normalize("NFD", ch)
    if len(nfd) < 2:
        return _sequence(cp, have)
    base_cp = ord(nfd[0])
    base = name_of(base_cp, have)
    if base is None:
        return None
    marks = []
    for c in nfd[1:]:
        m = MARKS.get(ord(c))
        if m is None:
            return None
        marks.append(m)
    greek = 0x370 <= base_cp <= 0x3FF or 0x1F00 <= base_cp <= 0x1FFF
    cyr = 0x400 <= base_cp <= 0x52F
    # Greek letters take tonos instead of acute
    if greek:
        marks = [("tonoscomb", "top") if m[0] == "acutecomb" else m for m in marks]
    # soft-dotted bases lose their dot under top marks
    if base in SOFT_DOTTED and any(a == "top" for _, a in marks):
        base = SOFT_DOTTED[base]
    case = is_case_base(base)
    greek_cap = greek and chr(base_cp).isupper()
    out = [(base, None)]
    i = 0
    while i < len(marks):
        mname, anchor = marks[i]
        # combined marks: a glyph named m1_m2 replaces the pair
        if i + 1 < len(marks):
            pair = (mname, marks[i + 1][0])
            combo = VIET.get(pair) or f"{pair[0]}_{pair[1]}"
            if combo in have and marks[i + 1][1] == anchor:
                mname = combo
                i += 1
        # script-specific mark shapes
        if cyr and mname + ".cy" in have:
            mname = mname + ".cy"
        if greek and mname + ".gr" in have:
            mname = mname + ".gr"
        if greek_cap and anchor == "top" and not mname.startswith("dieresiscomb"):
            out.append((mname, "tonos_left"))
            i += 1
            continue
        if case and anchor == "top" and mname + ".case" in have:
            mname = mname + ".case"
        if mname not in have:
            return None
        out.append((mname, anchor))
        i += 1
    return out


SEQ_OK = set(range(0x1C4, 0x1CD)) | set(range(0x1F1, 0x1F4)) | set(range(0xFB00, 0xFB07)) | {
    0x203C, 0x2047, 0x2048, 0x2049, 0x2025, 0x2024, 0x2116}


def _sequence(cp, have):
    """Compatibility sequences (DŽ Lj nj ﬁ ‼ …) as side-by-side components."""
    if cp not in SEQ_OK:
        return None
    k = unicodedata.normalize("NFKD", chr(cp))
    if len(k) < 2:
        return None
    parts = []
    for c in k:
        if unicodedata.category(c).startswith("M"):
            m = MARKS.get(ord(c))
            if not m or not parts:
                return None
            base = parts[-1][0]
            # attach to the previous letter (e.g. Ž in Ǆ)
            mname = m[0] + (".case" if c != k[-1] and parts[-1][0][:1].isupper() and m[0] + ".case" in have else "")
            if parts[-1][0][:1].isupper() and m[0] + ".case" in have:
                mname = m[0] + ".case"
            parts.append((mname, "seqmark"))
            continue
        n = name_of(ord(c), have)
        if n is None:
            return None
        parts.append((n, "seq"))
    return parts


_NAME_CACHE = {}


def name_of(cp, have):
    """Glyph name for a codepoint if it exists (defined or composed)."""
    return _NAME_CACHE.get(cp) if _NAME_CACHE.get(cp) in have else None


def register_cmap(cp, name):
    _NAME_CACHE[cp] = name


# Codepoint ranges we try to cover (composites are made wherever possible)
TARGET_RANGES = [
    (0x20, 0x7E), (0xA0, 0xFF), (0x100, 0x17F), (0x180, 0x24F), (0x250, 0x2AF),
    (0x2B0, 0x2FF), (0x300, 0x36F), (0x370, 0x3FF), (0x400, 0x4FF), (0x500, 0x52F),
    (0x1AB0, 0x1AFF), (0x1D00, 0x1DBF), (0x1E00, 0x1EFF), (0x1F00, 0x1FFF), (0x2000, 0x206F),
    (0x2070, 0x209F), (0x20A0, 0x20CF), (0x2100, 0x214F), (0x2150, 0x218F), (0x2190, 0x21FF),
    (0x2200, 0x22FF), (0x2300, 0x23FF), (0x2400, 0x243F), (0x2460, 0x24FF), (0x2500, 0x257F),
    (0x2580, 0x259F), (0x25A0, 0x25FF), (0x2600, 0x26FF), (0x2700, 0x27BF), (0x27C0, 0x27EF),
    (0x27F0, 0x27FF), (0x2900, 0x297F), (0x2C60, 0x2C7F), (0x2DE0, 0x2DFF), (0x2E00, 0x2E7F),
    (0xA640, 0xA69F), (0xA700, 0xA7FF), (0xAB30, 0xAB6F), (0xFB00, 0xFB06), (0xFE20, 0xFE2F),
    (0xFFFC, 0xFFFD), (0x1F100, 0x1F1FF),
]


def target_codepoints():
    for a, b in TARGET_RANGES:
        for cp in range(a, b + 1):
            if unicodedata.category(chr(cp)) not in ("Cn", "Co", "Cs"):
                yield cp
