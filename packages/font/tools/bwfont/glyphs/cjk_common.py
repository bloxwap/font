"""CJK common glyphs (pack 'cjk', shared by Bloxwap Sans/Mono KR and SC).

* CJK Symbols & Punctuation (U+3000..303F subset) + U+30FB katakana middle dot
* Fullwidth ASCII U+FF01..FF5E, FF5F..FF60, FFE0..FFE6

Em layout follows the hanzi (bwfont/han/engine.py): ideographic em box
x 0..1000, y -120..880 (centre 500/380); Mono uses a 1200 advance (two Latin
cells) with everything shifted +100.  Punctuation sits in PRC (Simplified
Chinese) positions: 、。，． in the lower-left quarter, ：；！？ left of
centre, opening brackets in the right half, closing brackets in the left.

Fullwidth forms re-use the *skeleton* of the Latin glyph (g.include), so they
are always identical in design and weight to the Latin, without depending on
the Latin glyph's final spacing (make_master spaces glyphs independently, so
a component offset could not know the Latin advance).  Centred forms are
left to the auto-spacer with a fixed advance (it centres the ink optically);
forms that sit off-centre are positioned from their skeleton bounds.
CJK-proper marks use the hanzi pen (han.engine.cjk_weight_factor).
"""
from __future__ import annotations

from ..han.engine import cjk_weight_factor
from ..skeleton import GLYPHS, G, glyph, shift, mirror_x, _transform_stroke

PACK = "cjk"
FAMS = ("sans", "mono")
CY = 380.0            # ideographic em centre

_CMAP = None


def _latin(cp):
    global _CMAP
    if _CMAP is None:
        _CMAP = {}
        for n, gd in GLYPHS.items():
            if gd.pack == "core":
                for u in gd.unicodes:
                    _CMAP.setdefault(u, n)
    return _CMAP[cp]


def _adv(g):
    return 1200 if g.mono else 1000


def _x0(g):
    return 100 if g.mono else 0


# ---------------------------------------------------------------------------
# fullwidth forms
# ---------------------------------------------------------------------------

def _skeleton_box(g, strokes):
    pts = [p for st in strokes for sg in st.segs for p in sg.pts]
    if not pts:
        return None
    rx = max((g.hw * st.scale * max(st.widths) for st in strokes), default=0)
    ry = max((g.hh * st.scale * max(st.widths) for st in strokes), default=0)
    return (min(p[0] for p in pts) - rx, min(p[1] for p in pts) - ry,
            max(p[0] for p in pts) + rx, max(p[1] for p in pts) + ry)


def _include(g, name, T=None):
    sub = G(g.p, name)
    GLYPHS[name].func(sub)
    strokes = [_transform_stroke(s, T) if T else s for s in sub.strokes]
    extra = [c.transform(T) if T else c for c in sub.extra]
    return strokes, extra


# placement: 'C' centred (auto), 'BL' bottom-left (、。，．), 'L' left of centre
# (：；！？), 'O' opening bracket (right half), 'E' closing bracket (left half)
PLACE = {0xFF0C: "BL", 0xFF0E: "BL", 0xFF1A: "L", 0xFF1B: "L", 0xFF01: "L", 0xFF1F: "L",
         0xFF08: "O", 0xFF3B: "O", 0xFF5B: "O", 0xFF09: "E", 0xFF3D: "E", 0xFF5D: "E",
         0xFF5F: "O", 0xFF60: "E"}


def _fullwidth(cp, src, double=False):
    mode = PLACE.get(cp, "C")

    def f(g: G):
        name = _latin(src)
        strokes, extra = _include(g, name)
        if double:      # ｟ ｠: two nested parentheses
            d = (100 + 0.75 * g.W) * (1 if src == 0x28 else -1)
            s2, e2 = _include(g, name, shift(d, 0))
            strokes += s2
            extra += e2
        if mode == "C":
            g.strokes += strokes
            g.extra += extra
            g.advance = _adv(g)
            return
        bb = _skeleton_box(g, strokes)
        if bb is None:
            ex = [p for c in extra for p in c.points()]
            bb = (min(p[0] for p in ex), min(p[1] for p in ex), max(p[0] for p in ex), max(p[1] for p in ex))
        else:
            ex = [p for c in extra for p in c.points()]
            if ex:
                bb = (min(bb[0], min(p[0] for p in ex)), bb[1], max(bb[2], max(p[0] for p in ex)), bb[3])
        if mode in ("BL", "L"):
            dx = 150 - bb[0]
        elif mode == "O":
            dx = 860 - bb[2]
        else:
            dx = 140 - bb[0]
        dx += _x0(g)
        T = shift(dx, 0)
        g.strokes += [_transform_stroke(s, T) for s in strokes]
        g.extra += [c.transform(T) for c in extra]
        g.fixed = True
        g.advance = _adv(g)
    glyph(f"uni{cp:04X}", cp, families=FAMS, pack=PACK)(f)


for _cp in range(0xFF01, 0xFF5F):
    _fullwidth(_cp, _cp - 0xFEE0)
_fullwidth(0xFF5F, 0x28, double=True)
_fullwidth(0xFF60, 0x29, double=True)
for _cp, _src in ((0xFFE0, 0xA2), (0xFFE1, 0xA3), (0xFFE2, 0xAC), (0xFFE3, 0xAF),
                  (0xFFE4, 0xA6), (0xFFE5, 0xA5), (0xFFE6, 0x20A9)):
    _fullwidth(_cp, _src)


# ---------------------------------------------------------------------------
# CJK symbols & punctuation (hanzi pen)
# ---------------------------------------------------------------------------

def cjk(cp, name=None):
    """Register a CJK mark drawn in sans em coordinates (x 0..1000)."""
    def deco(fn):
        def f(g: G):
            g.fixed = True
            g.advance = _adv(g)
            s = cjk_weight_factor(g.W)
            if g.mono:
                g.transform(shift(100, 0))
            fn(g, s)
            g.transform(None)
        glyph(name or f"uni{cp:04X}", cp, families=FAMS, pack=PACK)(f)
        return fn
    return deco


def L(g, s, a, b, w=1.0, w1=None):
    g.pen(a[0], a[1], w).l(b[0], b[1], w if w1 is None else w1).end(scale=s)


def ring(g, s, x0, y0, x1, y1, k=0.56):
    hx, hy = g.hw * s, g.hh * s
    a, b, c, d = x0 + hx, y0 + hy, x1 - hx, y1 - hy
    cx, cy = (a + c) / 2, (b + d) / 2
    g.pen(cx, d).h(a, cy, k).v(cx, b, k).h(c, cy, k).v(cx, d, k).close(scale=s)


def dot(g, s, x, y, w=2.1):
    g.pen(x - 0.5, y, w).l(x + 0.5, y, w).end(scale=s)


@cjk(0x3000)
def ideographic_space(g, s):
    pass


@cjk(0x3001)
def ideographic_comma(g, s):
    g.pen(160, 150, 1.0).l(250, 50, 1.3).end(scale=s)


@cjk(0x3002)
def ideographic_full_stop(g, s):
    r = 88 + 0.62 * g.W * s
    ring(g, s, 205 - r, 85 - r, 205 + r, 85 + r)


@cjk(0x3003)
def ditto(g, s):
    for x in (370, 560):
        L(g, s, (x, 620), (x + 80, 440), 1.0, 1.25)


@cjk(0x3005)
def iteration_mark(g, s):
    L(g, s, (420, 780), (210, 470), 0.94)
    L(g, s, (340, 600), (760, 600))
    (g.pen(760, 600).to(330, -20, (-0.25, -1), (-0.8, -0.6), k=0.6).end(scale=s))
    L(g, s, (440, 380), (600, 250), 0.94)


@cjk(0x3006)
def closing_mark(g, s):
    (g.pen(230, 620).to(690, 720, (1, 0.25), (1, 0)).end(scale=s))
    (g.pen(690, 720).to(170, 30, (-0.35, -1), (-0.75, -0.66), k=0.6).end(scale=s))
    L(g, s, (330, 470), (820, 40), 0.94)


@cjk(0x3007)
def ideographic_zero(g, s):
    ring(g, s, 100, -30, 900, 790)


def _angle(g, s, vx, ax, top=820, bot=-60):
    L(g, s, (ax, top), (vx, CY), 0.94)
    L(g, s, (vx, CY), (ax, bot), 0.94)


def _mirror_pair(cp, draw):
    @cjk(cp)
    def o(g, s):
        draw(g, s)

    def c(g: G):
        g.fixed = True
        g.advance = _adv(g)
        s = cjk_weight_factor(g.W)
        off = 100 if g.mono else 0
        g.transform(lambda p: (1000 - p[0] + off, 2 * CY - p[1]))   # point reflection: 」 is 「 turned
        draw(g, s)
        g.transform(None)
    glyph(f"uni{cp + 1:04X}", cp + 1, families=FAMS, pack=PACK)(c)


def _br_angle(g, s):
    _angle(g, s, 560, 800)


def _br_dangle(g, s):
    _angle(g, s, 460, 700)
    _angle(g, s, 640, 880)


def _br_corner(g, s):
    x, top = 560, 810
    L(g, s, (x, top), (x, 300))
    L(g, s, (x, top), (880, top))


def _br_wcorner(g, s):
    x0, x1, xr = 520, 640, 900
    t0, t1, b = 820, 700, 230
    L(g, s, (x0, t0), (xr, t0))
    L(g, s, (x0, t0), (x0, b))
    L(g, s, (x0, b), (x1, b))
    L(g, s, (x1, b), (x1, t1))
    L(g, s, (x1, t1), (xr, t1))
    L(g, s, (xr, t1), (xr, t0))


def _br_lent(g, s):
    g.pen(860, 800, 1.3).l(620, 800, 1.6).end(scale=s)
    g.pen(860, -40, 1.3).l(620, -40, 1.6).end(scale=s)
    x = 620                     # outer edge straight, inner side swells (lens)
    xm = x + g.hw * s * (2.7 - 1.6)
    (g.pen(x, 800, 1.6).to(xm, CY, (0.25, -1), (0, -1), w=2.7)
        .to(x, -40, (0, -1), (-0.25, -1), w=1.6).end(scale=s))


def _br_tort(g, s):
    L(g, s, (840, 820), (650, 680))
    L(g, s, (650, 680), (650, 80))
    L(g, s, (650, 80), (840, -60))


def _br_wlent(g, s):
    L(g, s, (880, 810), (600, 810))
    L(g, s, (600, 810), (600, -50))
    L(g, s, (600, -50), (880, -50))
    (g.pen(880, 810).to(740, CY, (-0.45, -1), (0, -1)).to(880, -50, (0, -1), (0.45, -1)).end(scale=s))


def _br_wtort(g, s):
    _br_tort(g, s)
    L(g, s, (760, 600), (760, 160))
    L(g, s, (760, 600), (840, 660))
    L(g, s, (760, 160), (840, 100))


def _br_wsquare(g, s):
    L(g, s, (600, 810), (880, 810))
    L(g, s, (600, 810), (600, -50))
    L(g, s, (600, -50), (880, -50))
    L(g, s, (720, 810), (720, -50))


for _cp, _fn in ((0x3008, _br_angle), (0x300A, _br_dangle), (0x300C, _br_corner),
                 (0x300E, _br_wcorner), (0x3010, _br_lent), (0x3014, _br_tort),
                 (0x3016, _br_wlent), (0x3018, _br_wtort), (0x301A, _br_wsquare)):
    _mirror_pair(_cp, _fn)


@cjk(0x3012)
def postal_mark(g, s):
    L(g, s, (180, 760), (820, 760))
    L(g, s, (180, 540), (820, 540))
    L(g, s, (500, 540), (500, -40))


@cjk(0x3013)
def geta_mark(g, s):
    L(g, s, (170, 560), (830, 560), 2.6)
    L(g, s, (170, 200), (830, 200), 2.6)


def _wave(g, s, x0, x1, n):
    amp = 70
    step = (x1 - x0) / n
    p = g.pen(x0, CY - amp * 0.6)
    p.to(x0 + step * 0.5, CY + amp, (0.55, 1), "r")
    for i in range(n - 1):
        y = CY - amp if i % 2 == 0 else CY + amp
        p.to(x0 + step * (i + 1.5), y, "r", "r", k=0.42)
    p.to(x1, CY + (amp * 0.6 if n % 2 == 0 else -amp * 0.6), "r",
         (0.55, 1) if n % 2 == 0 else (0.55, -1))
    p.end(scale=s)


@cjk(0x301C)
def wave_dash(g, s):
    _wave(g, s, 110, 890, 2)


@cjk(0x3030)
def wavy_dash(g, s):
    _wave(g, s, 60, 940, 3)


@cjk(0x301D)
def rev_double_prime(g, s):
    for x in (250, 380):
        L(g, s, (x, 800), (x + 60, 640), 1.2, 0.9)


@cjk(0x301E)
def double_prime(g, s):
    for x in (620, 750):
        L(g, s, (x + 60, 800), (x, 640), 1.2, 0.9)


@cjk(0x301F)
def low_double_prime(g, s):
    for x in (620, 750):
        L(g, s, (x + 60, 120), (x, -40), 1.2, 0.9)


@cjk(0x3021)
def hangzhou1(g, s):
    L(g, s, (500, 800), (500, -40))


@cjk(0x3022)
def hangzhou2(g, s):
    for x in (400, 600):
        L(g, s, (x, 800), (x, -40))


@cjk(0x3023)
def hangzhou3(g, s):
    for x in (320, 500, 680):
        L(g, s, (x, 800), (x, -40))


@cjk(0x3038)
def hangzhou10(g, s):
    L(g, s, (500, 800), (500, -40))
    L(g, s, (120, 440), (880, 440))


@cjk(0x3039)
def hangzhou20(g, s):
    for x in (340, 660):
        L(g, s, (x, 800), (x, -40))
    L(g, s, (100, 440), (900, 440))


@cjk(0x303A)
def hangzhou30(g, s):
    for x in (240, 500, 760):
        L(g, s, (x, 800), (x, -40))
    L(g, s, (90, 440), (910, 440))


@cjk(0x30FB)
def katakana_middle_dot(g, s):
    dot(g, s, 500, CY)
