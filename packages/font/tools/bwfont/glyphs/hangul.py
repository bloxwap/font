"""Hangul for Bloxwap Sans KR / Mono KR (pack 'hangul').

* positioned jamo parts (unencoded, fixed):  ko.L.* / ko.V.* / ko.T.*
  drawn once per layout variant (see bwfont/hangul/jamo.py)
* 11,172 precomposed syllables U+AC00..D7A3 = components [L, V, (T)]
* Hangul Compatibility Jamo U+3131..318E (standalone, centred, full width)
* conjoining Hangul Jamo (modern subset U+1100..1112, 1161..1175, 11A8..11C2)
  as components of the positioned parts, plus a GSUB 'ccmp' lookup that
  composes L V (T) sequences (NFD text) into the precomposed syllables.

Sans: advance 1000.  Mono: advance 1200 (two Latin cells), every part is
drawn 100 units to the right so syllables simply stack their components at 0.
"""
from __future__ import annotations

from ..features import FEATURE_HOOKS
from ..hangul import jamo as K
from ..skeleton import GLYPHS, G, glyph, shift, _transform_stroke

PACK = "hangul"
FAMS = ("sans", "mono")

L_LIST = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "ng", "j", "jj", "c",
          "k", "t", "p", "h"]
V_LIST = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u",
          "wo", "we", "wi", "yu", "eu", "ui", "i"]
T_LIST = [None, "g", "kk", "gs", "n", "nj", "nh", "d", "r", "rg", "rm", "rb", "rs", "rt", "rp",
          "rh", "m", "b", "bs", "s", "ss", "ng", "j", "c", "k", "t", "p", "h"]

# U+3131.. compatibility consonants, U+3165.. archaic ones
COMPAT_C = ["g", "kk", "gs", "n", "nj", "nh", "d", "tt", "r", "rg", "rm", "rb", "rs", "rt", "rp",
            "rh", "m", "b", "pp", "bs", "s", "ss", "ng", "j", "jj", "c", "k", "t", "p", "h"]
COMPAT_OLD = ["nn", "nd", "ns", "nz", "rgs", "rd", "rbs", "rz", "rqh", "mb", "ms", "mz", "mw",
              "bg", "bd", "bsg", "bsd", "bj", "bt", "bw", "ppw", "sg", "sn", "sd", "sb", "sj",
              "z", "ngng", "yng", "yngs", "yngz", "pw", "hh", "qh",
              "yo-ya", "yo-yae", "yo-i", "yu-yeo", "yu-ye", "yu-i", "araea", "araeae"]


def _setup(g: G):
    g.fixed = True
    g.advance = 1200 if g.mono else 1000
    if g.mono:
        g.transform(shift(100, 0))


def _part(name, draw):
    def f(g: G):
        _setup(g)
        draw(g)
        g.transform(None)
    glyph(name, families=FAMS, pack=PACK)(f)
    return name


def _encoded(name, cp, draw=None, comps=None):
    def f(g: G):
        _setup(g)
        if draw is not None:
            draw(g)
        g.transform(None)
        if comps:
            g.components = [(c, 0, 0) for c in comps]
    glyph(name, cp, families=FAMS, pack=PACK)(f)


# ---------------------------------------------------------------------------
# positioned parts
# ---------------------------------------------------------------------------

def lname(cons, vowel, final):
    return f"ko.L.{cons}.{K.lctx(vowel)}{final}"


def vname(vowel, final):
    return f"ko.V.{vowel}.{final}"


def tname(cons, vowel):
    return f"ko.T.{cons}.{K.tctx(vowel)}"


def _draw_L(cons, vowel, final):
    def d(g):
        lay = K.layout(vowel, final)
        K.draw_cons(g, cons, lay["L"], sweep=K.sweep_for(vowel, final))
    return d


def _draw_V(vowel, final):
    return lambda g: K.draw_vowel(g, vowel, final)


def _draw_T(cons, vowel):
    def d(g):
        K.draw_cons(g, cons, K.final_box(cons, vowel))
    return d


_done = set()
for _v in V_LIST:
    for _f in (0, 1):
        for _c in L_LIST:
            n = lname(_c, _v, _f)
            if n not in _done:
                _done.add(n)
                _part(n, _draw_L(_c, _v, _f))
        _part(vname(_v, _f), _draw_V(_v, _f))
    for _c in T_LIST[1:]:
        n = tname(_c, _v)
        if n not in _done:
            _done.add(n)
            _part(n, _draw_T(_c, _v))

# ---------------------------------------------------------------------------
# precomposed syllables
# ---------------------------------------------------------------------------

def syllable_parts(cp):
    i = cp - 0xAC00
    l, v, t = i // 588, (i % 588) // 28, i % 28
    L, V, T = L_LIST[l], V_LIST[v], T_LIST[t]
    f = 1 if T else 0
    out = [lname(L, V, f), vname(V, f)]
    if T:
        out.append(tname(T, V))
    return out


for _cp in range(0xAC00, 0xD7A4):
    _encoded(f"uni{_cp:04X}", _cp, comps=syllable_parts(_cp))

# ---------------------------------------------------------------------------
# conjoining jamo (modern subset): positioned parts
# ---------------------------------------------------------------------------

for _i, _c in enumerate(L_LIST):
    _encoded(f"uni{0x1100 + _i:04X}", 0x1100 + _i, comps=[lname(_c, "a", 0)])
for _i, _v in enumerate(V_LIST):
    _encoded(f"uni{0x1161 + _i:04X}", 0x1161 + _i, comps=[vname(_v, 0)])
for _i, _c in enumerate(T_LIST[1:]):
    _encoded(f"uni{0x11A8 + _i:04X}", 0x11A8 + _i, comps=[tname(_c, "a")])

# ---------------------------------------------------------------------------
# compatibility jamo
# ---------------------------------------------------------------------------

def _compat_cons(cons):
    return lambda g: K.draw_cons(g, cons, K.compat_cons_box(cons))


def _compat_vowel(vowel):
    return lambda g: K.draw_compat_vowel(g, vowel)


def _araea(with_i):
    def d(g):
        s = K.wf(g)
        j = K.J(g, (0, 0, 1000, 1000), s)
        if with_i:
            j.dot(410, K.EM_CY, w=1.9)
            x = 590
            g.pen(x, K.EM_CY + 380 - g.hh * s).l(x, K.EM_CY - 380 + g.hh * s).end(scale=s)
        else:
            j.dot(500, K.EM_CY, w=1.9)
    return d


for _i, _c in enumerate(COMPAT_C):
    _encoded(f"uni{0x3131 + _i:04X}", 0x3131 + _i, draw=_compat_cons(_c))
for _i, _v in enumerate(V_LIST):
    _encoded(f"uni{0x314F + _i:04X}", 0x314F + _i, draw=_compat_vowel(_v))
_encoded("uni3164", 0x3164)          # HANGUL FILLER: blank full-width
for _i, _x in enumerate(COMPAT_OLD):
    _cp = 0x3165 + _i
    if _x == "araea":
        _encoded(f"uni{_cp:04X}", _cp, draw=_araea(False))
    elif _x == "araeae":
        _encoded(f"uni{_cp:04X}", _cp, draw=_araea(True))
    elif _x in K.VOWELS:
        _encoded(f"uni{_cp:04X}", _cp, draw=_compat_vowel(_x))
    else:
        _encoded(f"uni{_cp:04X}", _cp, draw=_compat_cons(_x))

# ---------------------------------------------------------------------------
# enclosed: parenthesized ㈀..㈜ (U+3200..321C), circled ㉠..㉻ (U+3260..327B)
# ---------------------------------------------------------------------------

ENC_CONS = ["g", "n", "d", "r", "m", "b", "s", "ng", "j", "c", "k", "t", "p", "h"]
ENC_SYL = [0xAC00, 0xB098, 0xB2E4, 0xB77C, 0xB9C8, 0xBC14, 0xC0AC, 0xC544, 0xC790, 0xCC28,
           0xCE74, 0xD0C0, 0xD30C, 0xD558]


def _strokes_of(g, name, dx=0.0, dy=0.0):
    """Skeleton strokes of a glyph incl. its components (as built for g's master)."""
    sub = G(g.p, name)
    GLYPHS[name].func(sub)
    out = [_transform_stroke(st, shift(dx, dy)) if (dx or dy) else st for st in sub.strokes]
    for cn, cdx, cdy in sub.components:
        out += _strokes_of(g, cn, dx + cdx, dy + cdy)
    return out


def _enclosed(src, circled):
    def d(g):
        s = K.wf(g)
        cx = 600 if g.mono else 500
        k = 0.56 if circled else 0.62
        T = lambda p: (cx + (p[0] - cx) * k, K.EM_CY + (p[1] - K.EM_CY) * k)
        for st in _strokes_of(g, src):
            st2 = _transform_stroke(st, T)
            st2.scale *= 0.84
            g.strokes.append(st2)
        g.transform(None)
        if circled:
            j = K.J(g, (0, 0, 1, 1), s)
            j.ring(cx - 430, K.EM_CY - 430, cx + 430, K.EM_CY + 430, k=0.555)
        else:
            for pn, x in (("parenleft", cx - 350), ("parenright", cx + 350)):
                sub = G(g.p, pn)
                GLYPHS[pn].func(sub)
                pts = [q for st in sub.strokes for sg in st.segs for q in sg.pts]
                mx = (min(q[0] for q in pts) + max(q[0] for q in pts)) / 2
                my = (min(q[1] for q in pts) + max(q[1] for q in pts)) / 2
                for st in sub.strokes:
                    st2 = _transform_stroke(st, lambda q: (x + (q[0] - mx) * 0.9, K.EM_CY + (q[1] - my) * 0.9))
                    st2.scale *= s
                    g.strokes.append(st2)
    return d


for _i, _c in enumerate(ENC_CONS):
    _src = f"uni{0x3131 + COMPAT_C.index(_c):04X}"
    _encoded(f"uni{0x3200 + _i:04X}", 0x3200 + _i, draw=_enclosed(_src, False))
    _encoded(f"uni{0x3260 + _i:04X}", 0x3260 + _i, draw=_enclosed(_src, True))
for _i, _cp in enumerate(ENC_SYL):
    _encoded(f"uni{0x320E + _i:04X}", 0x320E + _i, draw=_enclosed(f"uni{_cp:04X}", False))
    _encoded(f"uni{0x326E + _i:04X}", 0x326E + _i, draw=_enclosed(f"uni{_cp:04X}", True))
_encoded("uni321C", 0x321C, draw=_enclosed("uniC8FC", False))     # ㈜ (주)

# ---------------------------------------------------------------------------
# GSUB: compose conjoining jamo (NFD) into precomposed syllables
# ---------------------------------------------------------------------------

def _hook(family, outs):
    if "uniAC00" not in outs or "uni1100" not in outs:
        return None
    lv, lvt = [], []
    for l in range(19):
        for v in range(21):
            s = 0xAC00 + (l * 21 + v) * 28
            lv.append(f"    sub uni{0x1100 + l:04X} uni{0x1161 + v:04X} by uni{s:04X};")
            for t in range(1, 28):
                lvt.append(f"    sub uni{s:04X} uni{0x11A7 + t:04X} by uni{s + t:04X};")
    code = "\n".join(
        ["lookup ko_compose_lv {"] + lv + ["} ko_compose_lv;", "",
         "lookup ko_compose_lvt {"] + lvt + ["} ko_compose_lvt;", "",
         "feature ccmp {",
         "  lookup ko_compose_lv;",
         "  lookup ko_compose_lvt;",
         "} ccmp;"])
    return [("hang", "dflt"), ("hang", "KOR")], code


FEATURE_HOOKS.append(_hook)
