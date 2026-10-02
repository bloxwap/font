"""Arabic script for Bloxwap Sans Arabic / Bloxwap Mono Arabic (pack 'arabic').

Letters are built systematically from rasm skeletons (tools/bwfont/arabic/
rasm.py) x joining forms + dot/mark patterns (table.py).  Joined forms are
fixed-advance glyphs whose join-line stubs reach exactly x = 0 / advance
with butt caps.  Names: uniXXXX (isolated/nominal), uniXXXX.init/.medi/.fina;
lam-alef ligatures uniLLLLAAAA(.fina).  Presentation forms (FB50-FDFF,
FE70-FEFF) are mapped onto the positional glyphs.

OpenType (FEATURE_HOOKS): init/medi/fina, rlig (lam-alef), locl (Persian /
Urdu / Sindhi / Kashmiri digit forms).  mark/mkmk come from the anchors.
"""
from __future__ import annotations

import math
import re
import unicodedata

from ..skeleton import G, glyph, mirror_x, scale_about
from ..features import FEATURE_HOOKS
from ..arabic.core import (AH, D, DESC, DGAP, DIAG, JY, MGAP, MONO, MWF, T, Ctx, apply_decor, dots, finish,
                           gw, ink_box, mk_dalef, mk_damma, mk_dammatan, mk_fatha, mk_fathatan, mk_hamza,
                           mk_madda, mk_meem, mk_noon_small, mk_ring, mk_seen_small, mk_shadda, mk_sukun,
                           mk_tah, mk_v, mk_whamza, mk_yeh_small, move_all, stamp)
from ..arabic.rasm import RASM, lamalef
from ..arabic.table import LETTERS
from .figures import tab

PACK = "arabic"
FAMS = ("sans", "mono")
FORMS = {"D": ("isol", "init", "medi", "fina"), "R": ("isol", "fina"), "U": ("isol",)}


def gname(cp, form="isol"):
    return f"uni{cp:04X}" + ("" if form == "isol" else "." + form)


# ---------------------------------------------------------------------------
# presentation forms -> positional glyphs
# ---------------------------------------------------------------------------

LAMS = [0x0644, 0x06B5, 0x06B6, 0x06B7, 0x06B8]
ALEFS = [0x0627, 0x0622, 0x0623, 0x0625, 0x0671, 0x0672, 0x0673, 0x0675]


def lig_name(lam, alef, fina=False):
    return f"uni{lam:04X}{alef:04X}" + (".fina" if fina else "")


def _presentation_forms():
    out = {}
    tags = {"isolated": "isol", "final": "fina", "initial": "init", "medial": "medi"}
    for cp in list(range(0xFB50, 0xFE00)) + list(range(0xFE70, 0xFF00)):
        try:
            dec = unicodedata.decomposition(chr(cp))
        except ValueError:
            continue
        m = re.match(r"<(isolated|final|initial|medial)> (.*)", dec)
        if not m:
            continue
        form = tags[m.group(1)]
        cps = [int(x, 16) for x in m.group(2).split()]
        if len(cps) == 1 and cps[0] in LETTERS:
            rasm = LETTERS[cps[0]][0]
            if form not in FORMS[RASM[rasm][1]]:
                continue
            out.setdefault(gname(cps[0], form), []).append(cp)
        elif len(cps) == 2 and cps[0] in LAMS and cps[1] in ALEFS and form in ("isol", "fina"):
            out.setdefault(lig_name(cps[0], cps[1], form == "fina"), []).append(cp)
    return out


PRES = _presentation_forms()


# ---------------------------------------------------------------------------
# letters
# ---------------------------------------------------------------------------

def _letter(cp, rasm, decor, form):
    fn = RASM[rasm][0]

    def f(g: G):
        c = Ctx(g, form)
        fn(c)
        toks = decor[form] if isinstance(decor, dict) else decor
        top, bot = apply_decor(c, toks)
        finish(c, top, bot)
    return f


JOINING = {}
for _cp, (_rasm, _decor) in sorted(LETTERS.items()):
    _jt = RASM[_rasm][1]
    JOINING[_cp] = _jt
    for _form in FORMS[_jt]:
        _n = gname(_cp, _form)
        _u = ([_cp] if _form == "isol" else []) + PRES.get(_n, [])
        glyph(_n, *_u, families=FAMS, pack=PACK)(_letter(_cp, _rasm, _decor, _form))


# --- lam-alef ---------------------------------------------------------------

_ALEF_ABOVE = ("madda", "hamza", "wasla", "whamza", "hh")


def _lamalef(lam, alef, form):
    lam_dec = LETTERS[lam][1]
    alef_dec = LETTERS[alef][1]

    def f(g: G):
        c = Ctx(g, form)
        c.lj = False
        lamalef(c)
        tops, bots = [], []
        if lam_dec:
            t, b = apply_decor(c, lam_dec)
            tops.append(t)
            bots.append(b)
        if alef_dec:
            above = [t for t in alef_dec if t in _ALEF_ABOVE]
            below = [t for t in alef_dec if t not in _ALEF_ABOVE]
            c.pt["above"] = c.pt["alef_above"]
            c.pt["below"] = c.pt["alef_below"]
            if "hh" in above:
                ax, ay = c.pt["alef_above"]
                c.pt["hh"] = (ax + g.hw + 70, AH(g) * 0.66)
            t, b = apply_decor(c, above + below)
            tops.append(t)
            bots.append(b)
            c.pt["above"] = c.pt["lam_above"]
        tops = [t for t in tops if t is not None]
        bots = [b for b in bots if b is not None]
        finish(c, max(tops) if tops else None, min(bots) if bots else None)
    return f


LAMALEF = []
for _l in LAMS:
    for _a in ALEFS:
        for _fina in (False, True):
            _n = lig_name(_l, _a, _fina)
            glyph(_n, *PRES.get(_n, []), families=FAMS, pack=PACK)(_lamalef(_l, _a, "fina" if _fina else "isol"))
        LAMALEF.append((_l, _a))


# --- tatweel -----------------------------------------------------------------

@glyph("uni0640", 0x0640, families=FAMS, pack=PACK)
def tatweel(g: G):
    adv = MONO if g.mono else round(gw(g, 280, 0, 0.6))
    jy = JY(g)
    g.line(0, jy, adv, jy, caps=("butt", "butt"))
    g.fixed = True
    g.advance = adv
    g.anchor("top", adv / 2, g.H + MGAP(g) + 20)
    g.anchor("bottom", adv / 2, -MGAP(g) - 10)


# ---------------------------------------------------------------------------
# combining marks
# ---------------------------------------------------------------------------

def _stack_gap(g):
    return 34 + 0.12 * g.grow


def _mark(name, cp, fn, below=False):
    def f(g: G):
        stamp(g, fn, 0, 0, above=not below)
        x0, y0, x1, y1 = ink_box(g)
        if below:
            g.anchor("_bottom", 0, 0)
            g.anchor("bottom", 0, y0 - _stack_gap(g))
        else:
            g.anchor("_top", 0, 0)
            g.anchor("top", 0, y1 + _stack_gap(g))
    glyph(name, *([cp] if cp else []), kind="mark", families=FAMS, pack=PACK)(f)


def _rot(fn):
    def h(g):
        n0, e0 = len(g.strokes), len(g.extra)
        fn(g)
        move_all(g, lambda p: (-p[0], -p[1]), n0, e0)
    return h


def _mir(fn):
    def h(g):
        n0, e0 = len(g.strokes), len(g.extra)
        fn(g)
        move_all(g, lambda p: (-p[0], p[1]), n0, e0)
    return h


def _fatha_dots(g):
    mk_fatha(g)
    d = D(g) * 0.62
    L = 150 + 0.5 * g.grow
    dots(g, "2", 0, L * 0.42 + g.hh * MWF(g) + 26, True, d)


def _rect_zero(g):
    w = MWF(g) * 0.9
    s = 104 + 0.6 * g.grow
    g.oval(-s / 2, 0, s / 2, s * 1.2, k=0.72, w=w)


def _khah_head(g):
    w = MWF(g) * 0.92
    a = 92 + 0.6 * g.grow
    h = 86 + 0.3 * g.grow
    g.pen(-a, 0, w).to(0, h, (0.1, 1), "r", k=0.6).to(a, 0, "r", (0.1, -1), k=0.6).end()


def _zwarakay(g):
    w = MWF(g)
    a = 70 + 0.4 * g.grow
    h = 120 + 0.3 * g.grow
    g.pen(-a, h, w).l(a, h).end()
    g.pen(a, h, w).l(-a, 0).end()
    g.pen(-a, 0, w).l(a, 0).end()


def _ring_small(g):
    w = 0.56
    r = D(g) * 0.56
    g.oval(-r, 0, r, 2 * r, w=w)


def _dot(g):
    g.dot(0, D(g) / 2, D(g))


MARKS = [
    ("uni064B", 0x064B, mk_fathatan, False),
    ("uni064C", 0x064C, mk_dammatan, False),
    ("uni064D", 0x064D, mk_fathatan, True),
    ("uni064E", 0x064E, mk_fatha, False),
    ("uni064F", 0x064F, mk_damma, False),
    ("uni0650", 0x0650, mk_fatha, True),
    ("uni0651", 0x0651, mk_shadda, False),
    ("uni0652", 0x0652, mk_sukun, False),
    ("uni0653", 0x0653, mk_madda, False),
    ("uni0654", 0x0654, lambda g: mk_hamza(g, 0.62), False),
    ("uni0655", 0x0655, lambda g: mk_hamza(g, 0.62), True),
    ("uni0656", 0x0656, mk_dalef, True),
    ("uni0657", 0x0657, _rot(mk_damma), False),
    ("uni0658", 0x0658, lambda g: mk_v(g, True), False),
    ("uni0659", 0x0659, _zwarakay, False),
    ("uni065A", 0x065A, mk_v, False),
    ("uni065B", 0x065B, lambda g: mk_v(g, True), False),
    ("uni065C", 0x065C, _dot, True),
    ("uni065D", 0x065D, _mir(mk_damma), False),
    ("uni065E", 0x065E, _fatha_dots, False),
    ("uni065F", 0x065F, mk_whamza, True),
    ("uni0670", 0x0670, mk_dalef, False),
    ("uni0615", 0x0615, mk_tah, False),
    ("uni0618", 0x0618, lambda g: mk_fatha(g, s=0.72), False),
    ("uni0619", 0x0619, lambda g: mk_damma(g, s=0.72), False),
    ("uni061A", 0x061A, lambda g: mk_fatha(g, s=0.72), True),
    ("uni06DF", 0x06DF, _ring_small, False),
    ("uni06E0", 0x06E0, _rect_zero, False),
    ("uni06E1", 0x06E1, _khah_head, False),
    ("uni06E2", 0x06E2, mk_meem, False),
    ("uni06E3", 0x06E3, mk_seen_small, True),
    ("uni06E4", 0x06E4, lambda g: mk_madda(g, 0.72), False),
    ("uni06E7", 0x06E7, mk_yeh_small, False),
    ("uni06E8", 0x06E8, mk_noon_small, False),
    ("uni06EA", 0x06EA, _ring_small, True),
    ("uni06EB", 0x06EB, _ring_small, False),
    ("uni06EC", 0x06EC, _dot, False),
    ("uni06ED", 0x06ED, mk_meem, True),
]
for _n, _cp, _fn, _below in MARKS:
    _mark(_n, _cp, _fn, _below)


# ---------------------------------------------------------------------------
# digits (tabular, ink centred)
# ---------------------------------------------------------------------------

def DH(g):
    return 640.0


def _cupr(g, xa, xb, top, depth):
    """u-cup hanging from a stem top to the right."""
    g.pen(xa, top - g.hh).v((xa + xb) / 2, top - depth, k=0.6).h(xb, top - g.hh, k=0.6).end()


def d0(g):
    tab(g)
    d = 0.9 * g.W + 70
    g.dot(0, DH(g) * 0.4, d)


def d1(g):
    tab(g)
    h = DH(g)
    g.line(14, g.hh, -14, h - g.hh)


def d2(g):
    tab(g)
    h = DH(g)
    cw = gw(g, 210, 220, 0.9)
    g.line(0, g.hh, 0, h - g.hh)
    _cupr(g, 0, cw - g.hw, h, gw(g, 180, 170, 0.3))


def d3(g):
    tab(g)
    h = DH(g)
    cw = gw(g, 150, 130, 0.7)
    dep = gw(g, 170, 160, 0.3)
    g.line(0, g.hh, 0, h - g.hh)
    _cupr(g, 0, cw, h, dep)
    _cupr(g, cw, 2 * cw, h, dep)


def d4(g):
    tab(g)
    h = DH(g)
    ew = gw(g, 300, 300, 0.9)
    hw, hh = g.hw, g.hh
    (g.pen(ew - hw, h * 0.84).to(ew * 0.52, h - hh, (-0.4, 1), "l", k=0.6)
        .h(hw + ew * 0.08, h * 0.71, k=0.6).v(ew * 0.56, h * 0.52, k=0.6).end())
    (g.pen(ew * 0.56, h * 0.52).to(hw, h * 0.24, (-1, -0.45), "d", k=0.6)
        .v(ew * 0.48, hh, k=0.6).l(ew - hw, hh).end())


def d5(g):
    tab(g)
    ow = gw(g, 310, 300, 1.2)
    oh = gw(g, 430, 420, 0.5)
    g.oval(0, -g.ov, ow, oh)


def d6(g):
    tab(g)
    h = DH(g)
    bl = gw(g, 220, 220, 0.6)
    xs = bl
    g.line(xs, h - g.hh, xs + 4, g.hh)
    g.line(xs, h - g.hh, g.hw, h - g.hh - 40)


def d7(g):
    tab(g)
    h = DH(g)
    vw = gw(g, 380, 380, 0.9)
    g.line(g.hw, h - g.hh, vw / 2, g.hh, DIAG)
    g.line(vw - g.hw, h - g.hh, vw / 2, g.hh, DIAG)


def d8(g):
    tab(g)
    h = DH(g)
    vw = gw(g, 380, 380, 0.9)
    g.line(g.hw, g.hh, vw / 2, h - g.hh, DIAG)
    g.line(vw - g.hw, g.hh, vw / 2, h - g.hh, DIAG)


def d9(g):
    tab(g)
    h = DH(g)
    lw = gw(g, 270, 270, 1.2)
    lh = gw(g, 290, 280, 0.5)
    g.oval(0, h - lh, lw, h)
    g.line(lw - g.hw, h - lh * 0.5, lw - g.hw, g.hh)


def p4(g, urdu=False):
    """Persian four: stem on the right, a reversed-3 attached on its left."""
    tab(g)
    h = DH(g)
    w_ = gw(g, 300, 300, 0.9)
    hw, hh = g.hw, g.hh
    xs = w_ - hw
    g.line(xs, h * 0.78, xs, hh)
    y0, y1, y2 = h * 0.78, h * 0.58, h * 0.36
    if urdu:
        g.oval(hw * 0.2 + w_ * 0.3, y1 - hh, xs + hw, h, w=1.0)
    else:
        (g.pen(xs, y0).to(hw + w_ * 0.18, (y0 + y1) / 2 + 10, (-1, 0.5), "d", k=0.6)
            .to(xs - 10, y1, "d", "r", k=0.6).end())
    (g.pen(xs - 10, y1).to(hw, (y1 + y2) / 2, (-1, 0.3), "d", k=0.6)
        .to(xs, y2, "d", (1, -0.2), k=0.6).end())


def p5(g):
    """Persian five: upside-down heart."""
    tab(g)
    w_ = gw(g, 320, 320, 1.2)
    h_ = gw(g, 440, 430, 0.4)
    cx = w_ / 2
    hw, hh = g.hw, g.hh
    yn = gw(g, 80, 80, 0.4)
    for sgn in (-1, 1):
        n0, e0 = len(g.strokes), len(g.extra)
        (g.pen(cx, h_ - hh).to(hw, h_ * 0.34, (-0.55, -1), "d", k=0.6)
            .v(cx * 0.58, hh, k=0.6).to(cx, yn, "r", (0.35, 1), k=0.6).end())
        if sgn > 0:
            move_all(g, mirror_x(cx), n0, e0)


def u5(g):
    tab(g)
    ow = gw(g, 300, 300, 1.2)
    oh = gw(g, 400, 390, 0.5)
    g.oval(0, -g.ov, ow, oh)
    g.line(ow * 0.3, oh - g.hh, ow * 0.08, oh + 70, DIAG)


def p6(g, urdu=False):
    tab(g)
    h = DH(g)
    w_ = gw(g, 260, 260, 0.7)
    hw, hh = g.hw, g.hh
    xs = w_ - hw
    if urdu:
        r = gw(g, 110, 100, 0.3)
        p = g.pen(hw, hh).l(xs - r, hh).h(xs, hh + r, k=0.6)
    else:
        p = g.pen(xs, hh)
    p.l(xs, h * 0.72).v(w_ * 0.5, h - hh, k=0.6).h(hw, h * 0.72, k=0.6).end()


def u7(g):
    tab(g)
    h = DH(g)
    vw = gw(g, 380, 380, 0.9)
    g.line(vw * 0.18 + g.hw, h - g.hh - 60, vw / 2, g.hh, DIAG)
    g.line(vw - g.hw, h - g.hh, vw / 2, g.hh, DIAG)
    g.pen(vw * 0.18 + g.hw, h - g.hh - 60).to(g.hw, h - g.hh, (-0.3, 1), (-0.6, 1), k=0.6).end()


ARABIC_DIGITS = [d0, d1, d2, d3, d4, d5, d6, d7, d8, d9]
for _i, _f in enumerate(ARABIC_DIGITS):
    glyph(f"uni{0x0660 + _i:04X}", 0x0660 + _i, zone="fig", families=FAMS, pack=PACK)(_f)
_EXT = {4: p4, 5: p5, 6: p6}
for _i in range(10):
    _f = _EXT.get(_i, ARABIC_DIGITS[_i])
    glyph(f"uni{0x06F0 + _i:04X}", 0x06F0 + _i, zone="fig", families=FAMS, pack=PACK)(_f)
glyph("uni06F4.loclURD", zone="fig", families=FAMS, pack=PACK)(lambda g: p4(g, urdu=True))
glyph("uni06F5.loclURD", zone="fig", families=FAMS, pack=PACK)(u5)
glyph("uni06F6.loclURD", zone="fig", families=FAMS, pack=PACK)(lambda g: p6(g, urdu=True))
glyph("uni06F7.loclURD", zone="fig", families=FAMS, pack=PACK)(u7)


# ---------------------------------------------------------------------------
# punctuation
# ---------------------------------------------------------------------------

def _pd(g):
    return g.W * 1.16 + 10


def _turned_comma(g, cx, cy):
    from .punctuation import _comma
    _comma(g, cx, cy, flip=True)


@glyph("uni060C", 0x060C, families=FAMS, pack=PACK)
def ar_comma(g: G):
    _turned_comma(g, 0, _pd(g) / 2)


@glyph("uni061B", 0x061B, families=FAMS, pack=PACK)
def ar_semicolon(g: G):
    d = _pd(g)
    g.dot(0, d / 2, d)
    _turned_comma(g, 0, 330 + 0.3 * g.grow)


@glyph("uni061F", 0x061F, families=FAMS, pack=PACK)
def ar_question(g: G):
    g.include("uni2E2E")


@glyph("uni066A", 0x066A, zone="fig", families=FAMS, pack=PACK)
def ar_percent(g: G):
    w_ = gw(g, 420, 420, 0.8)
    h = DH(g)
    d = 0.9 * g.W + 46
    g.line(g.hw, g.hh, w_ - g.hw, h - g.hh, DIAG)
    g.dot(d / 2, h - d / 2 - 20, d)
    g.dot(w_ - d / 2, d / 2 + 20, d)


@glyph("uni066B", 0x066B, families=FAMS, pack=PACK)
def ar_decimal(g: G):
    L = 170 + 0.3 * g.grow
    g.line(L * 0.32, L * 0.62, -L * 0.18, -L * 0.3, 1.0, 0.7)


@glyph("uni066C", 0x066C, families=FAMS, pack=PACK)
def ar_thousands(g: G):
    from .punctuation import _comma
    _comma(g, 0, 540 + 0.2 * g.grow)


@glyph("uni066D", 0x066D, families=FAMS, pack=PACK)
def ar_star(g: G):
    R = 170 + 0.4 * g.grow
    cy = 330
    w = 0.9
    for i in range(5):
        a = math.radians(90 + 72 * i)
        g.line(0, cy, math.cos(a) * (R - g.hw * w), cy + math.sin(a) * (R - g.hh * w), w)


@glyph("uni06D4", 0x06D4, families=FAMS, pack=PACK)
def ar_fullstop(g: G):
    L = gw(g, 190, 190, 0.5)
    g.line(0, g.hh + 16, L, g.hh + 52, 1.0)


@glyph("uni060D", 0x060D, families=FAMS, pack=PACK)
def ar_datesep(g: G):
    L = 200 + 0.3 * g.grow
    g.line(-L * 0.25, 0 + g.hh, L * 0.25, L, DIAG)


def _ornate_paren(g: G, right=False):
    top, bot = 760, -200
    bw = gw(g, 230, 220, 0.6)
    hw, hh = g.hw, g.hh
    xo, xi = hw, bw - hw
    cy = (top + bot) / 2
    n0, e0 = len(g.strokes), len(g.extra)
    (g.pen(xi, top - hh).to(xo, cy, (-0.55, -1), "d", k=0.6).to(xi, bot + hh, "d", (0.55, -1), k=0.6).end())
    a = 0.6
    (g.pen(xi + 10, cy + 150, a).to(xo + bw * 0.55, cy, (-0.6, -1), "d", k=0.6)
        .to(xi + 10, cy - 150, "d", (0.6, -1), k=0.6).end())
    g.dot(xi + 6, cy, D(g) * 0.8)
    if right:
        move_all(g, mirror_x(bw / 2), n0, e0)


@glyph("uniFD3E", 0xFD3E, families=FAMS, pack=PACK)
def ornate_left(g: G):
    _ornate_paren(g)


@glyph("uniFD3F", 0xFD3F, families=FAMS, pack=PACK)
def ornate_right(g: G):
    _ornate_paren(g, True)


@glyph("uni061C", 0x061C, kind="space", families=FAMS, pack=PACK)
def alm(g: G):
    g.advance = 0


# ---------------------------------------------------------------------------
# OpenType features
# ---------------------------------------------------------------------------

LANGS = ["dflt", "ARA", "FAR", "URD", "SND", "KUR", "PAS", "UYG", "MLY", "KSH"]


def _features(family, outs):
    if family is None or PACK not in getattr(family, "packs", ()):
        return None
    names = set(outs)
    fea = []
    for tag in ("init", "medi", "fina"):
        rules = []
        for cp in sorted(LETTERS):
            a, b = gname(cp), gname(cp, tag)
            if a in names and b in names:
                rules.append(f"  sub {a} by {b};")
        if rules:
            fea.append(f"feature {tag} {{")
            fea += rules
            fea.append(f"}} {tag};")
            fea.append("")
    rl = []
    for lam, alef in LAMALEF:
        li, lm, af = gname(lam, "init"), gname(lam, "medi"), gname(alef, "fina")
        lig, ligf = lig_name(lam, alef), lig_name(lam, alef, True)
        if {li, lm, af, lig, ligf} <= names:
            rl.append(f"  sub {li} {af} by {lig};")
            rl.append(f"  sub {lm} {af} by {ligf};")
    if rl:
        fea.append("feature rlig {")
        fea.append("  lookupflag IgnoreMarks;")
        fea += rl
        fea.append("} rlig;")
        fea.append("")
    far = [("uni0664", "uni06F4"), ("uni0665", "uni06F5"), ("uni0666", "uni06F6")]
    urd = [(f"uni06F{i}", f"uni06F{i}.loclURD") for i in (4, 5, 6, 7)]
    urd += [("uni0664", "uni06F4.loclURD"), ("uni0665", "uni06F5.loclURD"),
            ("uni0666", "uni06F6.loclURD"), ("uni0667", "uni06F7.loclURD")]
    blocks = [("FAR", far), ("URD", urd), ("SND", urd), ("KSH", urd)]
    lines = []
    for lang, pairs in blocks:
        pairs = [(a, b) for a, b in pairs if a in names and b in names]
        if pairs:
            lines.append(f"  language {lang} exclude_dflt;")
            lines += [f"    sub {a} by {b};" for a, b in pairs]
    if lines:
        fea.append("feature locl {")
        fea.append("  script arab;")
        fea += lines
        fea.append("} locl;")
        fea.append("")
    return [("arab", l) for l in LANGS], "\n".join(fea)


FEATURE_HOOKS.append(_features)
