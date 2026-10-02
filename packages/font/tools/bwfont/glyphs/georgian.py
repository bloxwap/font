"""Rounded Georgian Mkhedruli and Mtavruli, built from original skeletons.

Mkhedruli uses Latin x-height, ascender and descender zones. Mtavruli fits
each complete skeleton between baseline and cap height; the pen is applied
after the fit, preserving the weight and roundness rather than scaling ink.
Includes historic letters, the modern Mingrelian/Svan additions and signs.
"""
from __future__ import annotations

from ..skeleton import G, glyph, derive, GLYPHS, _transform_stroke
from ..features import FEATURE_HOOKS
from .latin_lower import LEAD
from .armenian import cross, qv, oval_cross

PACK = "georgian"
BOUNDS = {}


def u(cp):
    return f"uni{cp:04X}"


def geo(cp, width=478, mono=476, bottom=0, top=540):
    """Draw in our letter's own ink box, with weight-aware centre lines."""
    BOUNDS[cp] = (bottom, top)
    def deco(fn):
        def f(g: G):
            bw = g.wd(width, mono, 0.65)
            c = C(g, bw)
            fn(c)
        f.__name__ = fn.__name__
        glyph(u(cp), cp, pack=PACK, zone="lc")(f)
        return f
    return deco


class C:
    """Skeleton coordinates in a weight-aware body and Latin height grid."""
    def __init__(self, g, bw):
        self.g, self.bw = g, bw
        self.left, self.right = g.hw, bw - g.hw

    def x(self, v):
        return self.left + (self.right - self.left) * v

    def y(self, v):
        return self.g.hh + (self.g.xh - self.g.H) * v

    def pt(self, x, y):
        return (self.x(x), self.y(y))

    def unpt(self, p):
        """Inverse of pt(): absolute skeleton point -> letter coordinates."""
        return ((p[0] - self.left) / (self.right - self.left),
                (p[1] - self.g.hh) / (self.g.xh - self.g.H))

    def obox(self, x0=0, y0=0, x1=1, y1=1):
        """Absolute skeleton box of self.oval(x0, y0, x1, y1)."""
        return (self.x(x0), self.y(y0), self.x(x1), self.y(y1))

    def path(self, x, y, w=1):
        return Path(self, self.g.pen(self.x(x), self.y(y), w))

    def line(self, x0, y0, x1, y1, w=1):
        self.g.line(self.x(x0), self.y(y0), self.x(x1), self.y(y1), w)

    def oval(self, x0=0, y0=0, x1=1, y1=1, w=1):
        self.g.ovalc(self.x(x0), self.y(y0), self.x(x1), self.y(y1), w=w)


class Path:
    def __init__(self, c, p):
        self.c, self.p = c, p

    def l(self, x, y, w=None):
        self.p.l(self.c.x(x), self.c.y(y), w)
        return self

    def h(self, x, y, w=None, k=None):
        self.p.h(self.c.x(x), self.c.y(y), w=w, k=k)
        return self

    def v(self, x, y, w=None, k=None):
        self.p.v(self.c.x(x), self.c.y(y), w=w, k=k)
        return self

    def to(self, x, y, d0, d1, w=None, k=None):
        self.p.to(self.c.x(x), self.c.y(y), d0, d1, w=w, k=k)
        return self

    def end(self):
        self.p.end()


@geo(0x10D0, 430, 450)
def an(c):
    c.path(0.46, 1).to(1, 0.42, (0.5, -1), "d").v(0.5, 0).h(0, 0.28).end()


@geo(0x10D1, top=760)
def ban(c):
    c.oval(0, 0, 1, 0.74)
    # the ascender leaves the bowl at its widest point, tangent
    c.line(0, 0.37, 0, 1.44)
    c.line(0, 1.44, 0.68, 1.44)


@geo(0x10D2, bottom=-210)
def gan(c):
    # A round bowl crossed by the diagonal, which ends on the bowl's centre-line
    # (its cap buried in the stroke: no knot or knob in the counter).
    c.oval(0, -0.44, 1, 0.38)
    P = c.unpt(oval_cross(c.g, c.obox(0, -0.44, 1, 0.38), "bl", c.pt(0.84, 0.72), c.pt(0.24, -0.02)))
    c.path(0, 0.66).v(0.46, 1).h(0.84, 0.72).to(*P, "d", (-0.5, -1)).end()


@geo(0x10D3, 660, 500)
def don(c):
    w = 0.88 if c.g.mono else 1
    c.oval(0, 0.08, 0.5, 1, w)
    c.oval(0.5, 0.08, 1, 1, w)
    c.line(0.2, 0.03, 0.95, -0.06, w)


@geo(0x10D4, 430, 450, bottom=-210)
def en(c):
    c.path(0, 0.65).v(0.46, 1).h(1, 0.7).l(1, -0.08).v(0.48, -0.44).h(0, -0.08).end()


@geo(0x10D5, 420, 440, bottom=-210)
def vin(c):
    c.path(0.1, 0.95).to(0.44, 1, "r", "r").h(0.9, 0.66).v(0.36, 0.34).end()
    c.path(0.36, 0.34).h(1, -0.04).v(0.48, -0.44).h(0, -0.1).end()


@geo(0x10D6, 590, 490, top=760)
def zen(c):
    w = 0.9 if c.g.mono else 1
    c.oval(0, 0.66, 0.47, 1.44, w)
    c.oval(0.5, 0, 1, 0.78, w)
    c.path(0.235, 0.66, w).to(1, 1.36, "r", "r").end()


@geo(0x10D7, 650, 500)
def tan(c):
    w = 0.88 if c.g.mono else 1
    c.oval(0, 0, 0.5, 1, w)
    c.oval(0.5, 0, 1, 1, w)


@geo(0x10D8, 420, 450)
def in_(c):
    c.path(0, 0.18).l(0, 0.55).v(0.5, 1).h(1, 0.55).l(1, 0.18).end()


@geo(0x10D9, 410, 440, bottom=-210)
def kan(c):
    c.path(0.5, 1).h(0.9, 0.69).v(0.4, 0.38).end()
    c.path(0.4, 0.38).h(1, -0.02).v(0.46, -0.44).h(0, -0.1).end()


@geo(0x10DA, 780, 510)
def las(c):
    w = 0.82 if c.g.mono else 0.94
    # the first leg and the foot share a straight run, so the turn is clean
    for a, b in ((0, 0.34), (0.34, 0.67), (0.67, 1)):
        c.path(a, 0.5 if a == 0 else 0.33, w).l(a, 0.65).v((a + b) / 2, 1).h(b, 0.64).l(b, 0.3).end()
    c.path(0, 0.5, w).l(0, 0.36).v(0.42, 0).to(1, -0.04, "r", "r").end()


@geo(0x10DB, top=760)
def man(c):
    c.oval(0, 0, 1, 0.83)
    c.path(1, 0.415).l(1, 1.1).v(0.5, 1.44).h(0.08, 1.14).end()


@geo(0x10DC, 450, 456, top=760)
def nar(c):
    c.oval(0, 0, 1, 0.8)
    c.path(0, 0.4).l(0, 1.13).v(0.35, 1.44).to(0.94, 1.32, "r", "r").end()


@geo(0x10DD, 650, 500)
def on(c):
    w = 0.88 if c.g.mono else 1
    c.path(0, 0.12, w).l(0, 0.58).v(0.25, 1).h(0.5, 0.58).l(0.5, 0.12).end()
    c.path(0.5, 0.58, w).v(0.75, 1).h(1, 0.58).l(1, 0.12).end()


@geo(0x10DE, 410, 440, top=760)
def par(c):
    c.path(0.48, 1.44).h(0.86, 1.14).v(0.35, 0.83).end()
    c.path(0.35, 0.83).h(1, 0.42).v(0.5, 0).h(0, 0.25).end()


@geo(0x10DF, 480, 470, bottom=-210)
def zhar(c):
    c.oval(0, 0.46, 0.5, 1)
    c.path(1, 1).l(1, -0.02).v(0.5, -0.44).h(0, -0.15).end()


@geo(0x10E0, 500, 470, top=760)
def rae(c):
    c.path(0, 0.1).l(0, 0.54).v(0.5, 1).h(1, 0.56).l(1, 0.1).end()
    P = cross(qv(c.g, c.pt(0, 0.54), c.pt(0.5, 1)), c.pt(0, 0.74), c.pt(1, 0.74))
    c.path(*c.unpt(P)).to(0.72, 1.44, "u", (0.65, 1)).end()


@geo(0x10E1, 450, 456, top=760)
def san(c):
    c.path(0, 1.44).l(0, 0.45).v(0.5, 0).h(1, 0.37).to(0.62, 0.86, "u", (-0.5, 1)).end()


@geo(0x10E2, 620, 490, top=760)
def tar(c):
    c.oval(0, 0, 1, 0.96)
    c.oval(0.25, 0.87, 0.75, 1.44, 0.9)
    c.oval(0.28, 0.12, 0.72, 0.91, 0.9)


@geo(0x10E3, 550, 480, bottom=-210)
def un(c):
    c.oval(0, 0.45, 0.42, 1, 0.9)
    c.path(0.42, 0.725).v(0.68, 1).h(1, 0.66).l(1, -0.08).v(0.5, -0.44).h(0, -0.13).end()


@geo(0x10E4, 600, 490, bottom=-210)
def phar(c):
    w = 0.9 if c.g.mono else 1
    c.oval(0, 0.3, 0.5, 1, w)
    c.oval(0.5, 0.3, 1, 1, w)
    c.path(0.75, 0.3, w).h(1, -0.05).v(0.5, -0.44).h(0, -0.12).end()


@geo(0x10E5, 460, 460, bottom=-210, top=760)
def khar(c):
    c.oval(0, 0, 1, 0.78)
    c.path(1, -0.44).l(1, 1.14).v(0.55, 1.44).h(0.16, 1.15).end()


@geo(0x10E6, 650, 500)
def ghan(c):
    w = 0.88 if c.g.mono else 1
    for a, b in ((0, 0.5), (0.5, 1)):
        c.path(a, 0.45 if a == 0 else 0.27, w).l(a, 0.62).v((a + b) / 2, 1).h(b, 0.63).v((a + b) / 2, 0.15).end()
    c.path(0, 0.45, w).l(0, 0.27).v(0.42, 0).to(1, -0.04, "r", "r").end()


@geo(0x10E7, 450, 456, bottom=-210)
def qar(c):
    c.path(0, 1).l(0, 0.63).v(0.5, 0.3).h(1, 0.63).l(1, 1).end()
    c.path(1, 0.7).l(1, -0.03).v(0.46, -0.44).h(0, -0.12).end()


@geo(0x10E8, 600, 490, top=760)
def shin(c):
    w = 0.9 if c.g.mono else 1
    c.oval(0, 0.82, 0.5, 1.44, w)
    c.oval(0.5, 0.82, 1, 1.44, w)
    c.path(1, 1.13, w).l(1, 0.45).v(0.5, 0).h(0, 0.3).end()


@geo(0x10E9, 450, 456, top=760)
def chin(c):
    c.path(0, 0).l(0, 1.1).v(0.5, 1.44).h(1, 1.16).end()
    c.path(0, 0.5 - 0.11, LEAD).l(0, 0.5, 1).v(0.52, 0.96).h(1, 0.55).l(1, 0).end()


@geo(0x10EA, 480, 470, top=760)
def can(c):
    c.path(0.35, 1.44).to(0, 0.94, (-0.4, -1), "d").l(0, 0.45).v(0.5, 0).h(1, 0.38).v(0.53, 0.72).end()
    c.path(0.53, 0.72).h(0.92, 1.02).to(0.64, 1.38, "u", (-0.6, 1)).end()


@geo(0x10EB, 470, 470, top=760)
def jil(c):
    c.oval(0, 0, 1, 0.82)
    c.path(1, 0.41).l(1, 1.12).v(0.5, 1.44).h(0.16, 1.18).end()


@geo(0x10EC, 530, 480, top=760)
def cil(c):
    c.path(0, 1.44).l(0, 0.83).end()
    c.path(0.5, 0.86).v(0.25, 1.13).h(0, 0.83).to(0.5, 0, "d", (0.6, -1)).end()
    c.path(0.5, 0).to(1, 0.83, (0.6, 1), "u").v(0.75, 1.13).h(0.5, 0.86).end()


@geo(0x10ED, 580, 490, bottom=-210, top=760)
def char(c):
    c.oval(0.18, 0.95, 0.78, 1.44, 0.85)
    c.line(0, 0.94, 1, -0.44, 0.9)
    c.line(1, 0.9, 0, -0.44, 0.9)
    c.path(0, -0.1, 0.85).v(0.26, -0.4).h(0.5, -0.12).end()
    c.path(0.5, -0.12, 0.85).v(0.75, -0.4).h(1, -0.1).end()


@geo(0x10EE, 470, 470, top=760)
def xan(c):
    c.oval(0, 0, 1, 0.83)
    c.line(0, 0.415, 0, 1.44)
    c.path(0, 0.83).to(1, 1.44, "r", (0.5, 1)).end()


@geo(0x10EF, 540, 480, bottom=-210, top=760)
def jhan(c):
    c.line(0.05, 1.3, 0.95, -0.3, 0.92)
    c.line(0.95, 1.2, 0.05, -0.44, 0.92)
    c.path(0.05, 1.3, 0.85).v(0.5, 1.44).h(0.95, 1.2).end()
    c.path(0.05, -0.44, 0.85).to(0.88, -0.28, "r", "r").end()


@geo(0x10F0, 420, 450, top=760)
def hae(c):
    c.path(0, 1.44).to(0.45, 1.22, "d", "r").h(0.92, 0.88).v(0.35, 0.61).end()
    c.path(0.35, 0.61).h(1, 0.3).v(0.5, 0).h(0, 0.21).end()


# Archaic letters and additions retain distinct skeletons.
@geo(0x10F1, 540, 480, top=760)
def he(c):
    c.oval(0, 0.62, 0.5, 1.44, 0.9)
    c.path(0.5, 1.18).h(1, 0.82).v(0.3, 0.65).end()
    c.path(0, 1.03).l(0, 0.4).v(0.5, 0).h(1, 0.32).v(0.35, 0.6).end()


@geo(0x10F2, 500, 470)
def hie(c):
    c.oval(0.1, 0.14, 0.9, 1)
    c.line(0, 0, 1, 0)


@geo(0x10F3, 420, 450, bottom=-210)
def we(c):
    vin(c.g)


@geo(0x10F4, 420, 450, top=760)
def har(c):
    par(c.g)


@geo(0x10F5, 470, 470, top=760)
def hoe(c):
    c.oval(0, 0, 1, 0.73)
    c.oval(0, 0.73, 1, 1.44)
    c.line(0, 0.64, 1, 0.64)


@geo(0x10F6, 610, 490, bottom=-210, top=760)
def fi(c):
    c.oval(0, 0, 1, 1)
    c.line(0.5, -0.44, 0.5, 1.44)


@geo(0x10F7, 460, 460, top=760)
def yn(c):
    c.path(0.25, 1.44).to(0.82, 1.08, "r", "d").to(0, 0.33, "d", "d").v(0.5, 0).h(1, 0.34).end()


@geo(0x10F8, 450, 456, bottom=-210)
def elifi(c):
    c.path(0, 1).l(0, -0.06).v(0.5, -0.44).h(1, -0.08).to(0.53, 0.44, "u", "l").end()
    c.path(0, 0.42).h(0.95, 0.76).to(0.66, 1, "u", "l").end()


@geo(0x10F9, 480, 470, bottom=-210)
def turned_gan(c):
    c.oval(0, 0, 1, 1)
    c.path(0.45, 0).to(0.75, -0.44, "d", "d").end()
    c.path(0.45, 0).to(0.18, -0.44, "d", "d").end()


@geo(0x10FA, 430, 450)
def ain(c):
    c.path(0.93, 0.93).to(0.5, 1, "l", "l").h(0, 0.5).v(0.5, 0.08).to(1, 0.2, "r", "r").end()


@geo(0x10FD, 460, 460, top=760)
def aen(c):
    c.path(0.9, 1.15).to(0.5, 1.44, "u", "l").h(0.1, 1.06).to(0.8, 0.48, "d", "d").v(0.45, 0).h(0, 0.25).end()


@geo(0x10FE, 480, 470, top=760)
def hard_sign(c):
    c.oval(0, 0, 1, 1)
    P = c.unpt(oval_cross(c.g, c.obox(), "tr", c.pt(0.76, 0.83), c.pt(0.08, 1.44)))
    c.line(*P, 0.08, 1.44, 0.92)
    c.path(0.08, 1.44).to(1, 1.37, "r", "r").end()


@geo(0x10FF, 470, 470, top=760)
def labial_sign(c):
    c.oval(0, 0, 1, 1.44)


def _mtavruli(cp):
    """Fit the full Mkhedruli centre-line extent; keep the pen unchanged."""
    def f(g):
        sub = G(g.p, u(cp))
        GLYPHS[u(cp)].func(sub)
        pts = [p for s in sub.strokes for seg in s.segs for p in seg.pts]
        low, high = min(p[1] for p in pts), max(p[1] for p in pts)
        sy = (g.cap - g.H) / (high - low)
        tx = lambda p: (p[0], g.hh + (p[1] - low) * sy)
        g.strokes += [_transform_stroke(s, tx) for s in sub.strokes]
        g.extra += [c.transform(tx) for c in sub.extra]
    glyph(u(cp + 0xBC0), cp + 0xBC0, pack=PACK, zone="uc")(f)


for _cp in BOUNDS:
    _mtavruli(_cp)


# Modifier nar is a reduced letter, not another case pair.
derive(u(0x10FC), 0x10FC, src=u(0x10DC), sx=0.64, sy=0.54,
       dy=390, wscale=0.75, pack=PACK)


@glyph(u(0x10FB), 0x10FB, pack=PACK)
def paragraph_separator(g):
    d = g.W * 0.92 + 18
    for x, y in ((0, g.xh * 0.7), (-d * 0.86, g.xh * 0.3), (d * 0.86, g.xh * 0.3)):
        g.dot(x, y, d)


def _features(family, outs):
    if family is None or PACK not in family.packs:
        return None
    return [("geor", "dflt"), ("geor", "KAT")], ""


FEATURE_HOOKS.append(_features)
