"""Japanese kana for Bloxwap Sans JP / Mono JP (pack 'kana').

* Hiragana U+3041..3096, U+309D..309F; Katakana U+30A1..30FA, U+30FC..30FF;
  Katakana Phonetic Extensions U+31F0..31FF (small katakana)
* voicing marks: combining U+3099 / U+309A (zero-width marks with a
  `_voice` anchor; every full-size kana has a `voice` anchor) and the
  spacing forms U+309B / U+309C
* Halfwidth Katakana U+FF65..FF9F (advance 500 Sans / 600 Mono)

Shapes live in bwfont/kana/shapes.py (design grid 1000 x 1000) and are
mapped into the em by bwfont/kana/ctx.py: kana are ~90 % of the kanji face,
optically centred on the ideographic em centre; the pen scale is the hanzi
one (han.engine.cjk_weight_factor) so the colour matches the kanji.
Voiced kana (が ぱ ヴ …) are drawn as the base skeleton + the mark at the
upper right (per-glyph offsets in VOICE_OFF keep it clear of the base).
Sans: advance 1000.  Mono: advance 1200, everything drawn +100.

A GSUB 'ccmp' lookup composes base + U+3099/309A (NFD text) into the
precomposed voiced kana.
"""
from __future__ import annotations

import unicodedata

from ..features import FEATURE_HOOKS
from ..kana import ctx as C
from ..kana.shapes import HIRA, KATA
from ..skeleton import G, glyph

PACK = "kana"
FAMS = ("sans", "mono")
SHAPES = {"hira": HIRA, "kata": KATA}

# Unicode (Kunrei) romanisation -> shape key
ROMA = {"si": "shi", "ti": "chi", "tu": "tsu", "hu": "fu"}

# Voiced kana: per (script, shape[, mark]) adjustments, em units
#   VOICE_OFF  mark offset from ctx.mark_centre()
#   VOICE_FIT  (dx, dy): the base is drawn into its box shrunk by this much
#              from the right / top (full amount at Black, 35 % at Thin) so
#              the mark keeps clear of corners and bars in the upper right
VOICE_OFF = {("hira", "iter"): (-130, -90), ("kata", "iter"): (-110, -90)}
VOICE_FIT = {
    ("hira", "ki"): (20, 0), ("hira", "ku"): (20, 0), ("hira", "ke"): (55, 10),
    ("hira", "te"): (70, 30), ("hira", "ha"): (35, 0), ("hira", "ho"): (70, 40),
    ("kata", "ku"): (35, 20), ("kata", "sa"): (35, 0), ("kata", "su"): (35, 20),
    ("kata", "so"): (60, 50), ("kata", "ta"): (35, 20), ("kata", "chi"): (55, 75),
    ("kata", "tsu"): (70, 60), ("kata", "te"): (60, 40), ("kata", "fu"): (55, 40),
    ("kata", "wa"): (55, 40), ("kata", "wo"): (55, 40), ("kata", "shi"): (30, 30),
    ("kata", "u"): (30, 20), ("kata", "we"): (30, 20), ("kata", "ko"): (20, 10),
}


def _off(script, shape, mark):
    return VOICE_OFF.get((script, shape, mark)) or VOICE_OFF.get((script, shape)) or (0.0, 0.0)


def _fit(g, script, shape):
    fx, fy = VOICE_FIT.get((script, shape), (0.0, 0.0))
    r = min(1.0, max(0.0, (g.W * C.wfactor(g) - 21.0) / 96.0))
    f = 0.35 + 0.65 * r
    return fx * f, fy * f


def mark_pos(g, script, shape, mark):
    mx, my = C.mark_centre(g, 100.0 if g.mono else 0.0)
    du, dv = _off(script, shape, mark or "d")
    return mx + du, my + dv


# katakana are drawn a little smaller than hiragana (they are straighter and
# fill their box more); square / wide ones a little smaller still so they
# stay distinct from the kanji 口 二 工 力
KATA_K = 0.95
KATA_EXTRA = {"ro": 0.93, "ni": 0.95, "e": 0.96, "ko": 0.96, "yu": 0.97, "yo": 0.97}


def _box(g, kind, script=None, shape=None):
    x0, y0, x1, y1 = C.FULL
    off = 100.0 if g.mono else 0.0
    if kind in ("full", "small") and script == "kata":
        f = KATA_K * KATA_EXTRA.get(shape, 1.0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        x0, x1 = cx - (cx - x0) * f, cx + (x1 - cx) * f
        y0, y1 = cy - (cy - y0) * f, cy + (y1 - cy) * f
    if kind == "full":
        return (x0 + off, y0, x1 + off, y1)
    if kind == "small":
        w, h = (x1 - x0) * C.SMALL_K, (y1 - y0) * C.SMALL_K
        cx = C.SMALL_CX + off
        b = C.FULL[1]
        return (cx - w / 2, b, cx + w / 2, b + h)
    x0, y0, x1, y1 = C.FULL
    hk = C.HALF_K_MONO if g.mono else C.HALF_K
    cx = 300.0 if g.mono else 250.0
    w = (x1 - x0) * hk
    if kind == "half":
        return (cx - w / 2, y0, cx + w / 2, y1)
    if kind == "halfsmall":
        w2, h2 = w * 0.78, (y1 - y0) * C.SMALL_K
        return (cx - w2 / 2, y0, cx + w2 / 2, y0 + h2)
    raise ValueError(kind)


PEN = {"full": 1.0, "small": 0.9, "half": 0.86, "halfsmall": 0.82}


def _adv(g, kind):
    if kind in ("half", "halfsmall"):
        return 600 if g.mono else 500
    return 1200 if g.mono else 1000


def _draw(g, script, shape, kind="full", mark=None, part="all"):
    """part: 'all' | 'base' | 'mark' (the latter two for QA scripts)."""
    g.fixed = True
    g.advance = _adv(g, kind)
    s = C.wfactor(g) * PEN[kind]
    box = _box(g, kind, script, shape)
    if part in ("all", "base"):
        if mark and kind == "full":
            fx, fy = _fit(g, script, shape)
            box = (box[0], box[1], box[2] - fx, box[3] - fy)
        k = C.K(g, box, s)
        k.voiced = mark
        SHAPES[script][shape](k)
        k.done()
    if kind == "full":
        mx, my = mark_pos(g, script, shape, mark)
        if mark and part in ("all", "mark"):
            k = C.K(g, _box(g, kind), s)
            k.mark_em(mark, mx, my)
            k.done()
        if part == "all":
            g.anchor("voice", mx, my)


# ---------------------------------------------------------------------------
# code point -> spec
# ---------------------------------------------------------------------------

SPEC = {}          # cp -> (script, shape, kind, mark)
VOICED = {}        # cp -> (base cp, mark cp)


def _letter(nm):
    """'HIRAGANA LETTER SMALL KA' -> ('hira', 'ka', small?)"""
    parts = nm.split()
    script = "hira" if parts[0] == "HIRAGANA" else "kata"
    rest = parts[parts.index("LETTER") + 1:]
    small = rest[0] == "SMALL"
    if small:
        rest = rest[1:]
    key = rest[0].lower()
    return script, ROMA.get(key, key), small


SPECIAL = {
    0x309D: ("hira", "iter"), 0x309F: ("hira", "yori"),
    0x30FC: ("kata", "long"), 0x30FD: ("kata", "iter"), 0x30FF: ("kata", "koto"),
}


def _collect():
    cps = list(range(0x3041, 0x3097)) + [0x309D, 0x309E, 0x309F] + \
        list(range(0x30A1, 0x30FB)) + [0x30FC, 0x30FD, 0x30FE, 0x30FF] + list(range(0x31F0, 0x3200))
    for cp in cps:
        if cp in SPECIAL:
            SPEC[cp] = SPECIAL[cp] + ("full", None)
            continue
        nfd = unicodedata.normalize("NFD", chr(cp))
        if len(nfd) == 2:
            VOICED[cp] = (ord(nfd[0]), ord(nfd[1]))
            continue
        script, key, small = _letter(unicodedata.name(chr(cp)))
        SPEC[cp] = (script, key, "small" if small else "full", None)
    for cp, (b, m) in VOICED.items():
        script, key, kind, _ = SPEC[b]
        SPEC[cp] = (script, key, kind, "d" if m == 0x3099 else "h")


_collect()


def _register(cp):
    script, key, kind, mark = SPEC[cp]

    def f(g: G):
        _draw(g, script, key, kind, mark)
    glyph(f"uni{cp:04X}", cp, families=FAMS, pack=PACK)(f)


for _cp in sorted(SPEC):
    _register(_cp)


# ---------------------------------------------------------------------------
# voicing marks
# ---------------------------------------------------------------------------

def _comb(cp, kind):
    def f(g: G):
        g.fixed = True
        g.advance = 0
        adv = _adv(g, "full")
        x0, y0, x1, y1 = _box(g, "full")
        k = C.K(g, (x0 - adv, y0, x1 - adv, y1), C.wfactor(g))
        mx, my = C.mark_centre(g, 100.0 if g.mono else 0.0)
        k.mark_em(kind, mx - adv, my)
        g.anchor("_voice", mx - adv, my)
        k.done()
    glyph(f"uni{cp:04X}", cp, kind="mark", families=FAMS, pack=PACK)(f)


_comb(0x3099, "d")
_comb(0x309A, "h")

# spacing forms: the mark alone, in the upper left of its em
def _spacing(cp, kind, half=False):
    def f(g: G):
        g.fixed = True
        bk = "half" if half else "full"
        g.advance = _adv(g, bk)
        k = C.K(g, _box(g, bk), C.wfactor(g) * (PEN["half"] if half else 1.0))
        mx, my = C.mark_centre(g)
        if half:
            k.mark_em(kind, (300.0 if g.mono else 250.0) - 40.0, my, scale=0.92)
        else:
            k.mark_em(kind, (100.0 if g.mono else 0.0) + 200.0, my)
        k.done()
    glyph(f"uni{cp:04X}", cp, families=FAMS, pack=PACK)(f)


_spacing(0x309B, "d")
_spacing(0x309C, "h")


# ---------------------------------------------------------------------------
# halfwidth katakana
# ---------------------------------------------------------------------------

def _half(cp):
    nm = unicodedata.name(chr(cp))
    if nm == "HALFWIDTH KATAKANA VOICED SOUND MARK":
        return _spacing(cp, "d", half=True)
    if nm == "HALFWIDTH KATAKANA SEMI-VOICED SOUND MARK":
        return _spacing(cp, "h", half=True)
    if nm == "HALFWIDTH KATAKANA MIDDLE DOT":
        def f(g: G):
            g.fixed = True
            g.advance = _adv(g, "half")
            s = C.wfactor(g)
            x = 300.0 if g.mono else 250.0
            g.pen(x - 0.5, C.CY, 2.1).l(x + 0.5, C.CY, 2.1).end(scale=s)
        glyph(f"uni{cp:04X}", cp, families=FAMS, pack=PACK)(f)
        return
    if nm == "HALFWIDTH KATAKANA-HIRAGANA PROLONGED SOUND MARK":
        key, kind = "long", "half"
    else:
        script, key, small = _letter(nm.replace("HALFWIDTH ", ""))
        kind = "halfsmall" if small else "half"

    def f(g: G, key=key, kind=kind):
        _draw(g, "kata", key, kind)
    glyph(f"uni{cp:04X}", cp, families=FAMS, pack=PACK)(f)


for _cp in range(0xFF65, 0xFFA0):
    _half(_cp)


# ---------------------------------------------------------------------------
# GSUB: compose base + combining voicing mark into the precomposed kana
# ---------------------------------------------------------------------------

def _hook(family, outs):
    if "uni3099" not in outs or "uni304C" not in outs:
        return None
    rules = []
    for cp, (b, m) in sorted(VOICED.items()):
        names = (f"uni{b:04X}", f"uni{m:04X}", f"uni{cp:04X}")
        if all(n in outs for n in names):
            rules.append(f"    sub {names[0]} {names[1]} by {names[2]};")
    code = "\n".join(["lookup kana_compose_voiced {"] + rules + ["} kana_compose_voiced;", "",
                      "feature ccmp {", "  lookup kana_compose_voiced;", "} ccmp;"])
    return [("kana", "dflt"), ("kana", "JAN")], code


FEATURE_HOOKS.append(_hook)
