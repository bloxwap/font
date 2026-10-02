"""Greek skeletons: capitals that differ from Latin, lowercase, symbols,
spacing accents and Greek mark combinations.

Latin look-alike capitals (Α Β Ε Ζ Η Ι Κ Μ Ν Ο Ρ Τ Υ Χ) and ο are aliases
(see composites.py); accented letters are composed from NFD.
"""
from __future__ import annotations

from ..skeleton import glyph, G, GLYPHS, mirror_x, shift, _transform_stroke
from .latin_lower import EPS, arch, bowl_left, c_shape, rot180

DIAG = 0.92      # diagonal width factor
MW = 0.9         # mark weight (matches marks.py)


# ---------------------------------------------------------------------------
# local helpers
# ---------------------------------------------------------------------------

def _tail(p, g: G, cx, xr, ybot, depth=None, hook=None):
    """Continue path `p` (currently travelling down on the left side of a
    bowl) round the baseline and into a descender hook (ζ ξ ς)."""
    depth = (g.desc + g.hh + 34) if depth is None else depth
    hook = (86 + g.grow * 0.25) if hook is None else hook
    p.v(cx, ybot, k=0.6)
    p.h(xr, (ybot + depth) * 0.5 - 6, k=0.6, k2=0.6)
    p.v(xr - hook, depth, k=0.58)
    return p


def _put(g: G, name, dx=0.0, dy=0.0):
    """Draw another glyph's skeleton shifted by (dx, dy) — dots included."""
    sub = G(g.p, name)
    GLYPHS[name].func(sub)
    T = shift(dx, dy)
    for s in sub.strokes:
        g._add(_transform_stroke(s, T))
    for c in sub.extra:
        g.extra.append(c.transform(T))
    return sub


def _cup(g: G, x0, x1, top, bot, side=0.48, w=1.0):
    """υ-like cup: arms from `top` (ink) down to a round bottom at `bot` (ink)."""
    cx = (x0 + x1) / 2
    l, r = x0 + g.hw * w, x1 - g.hw * w
    ys = bot + (top - bot) * side
    (g.pen(l, top - g.hh * w, w)
        .l(l, ys)
        .v(cx, bot + g.hh * w, k=0.6)
        .h(r, ys, k=0.6)
        .l(r, top - g.hh * w)
        .end())


def _rloop(g: G, l, b, r, t, ly0, ly1, xt, xb, yr=None, k=None, kl=None, w=1.0):
    """Closed round loop on the skeleton box l..r, b..t whose LEFT side runs
    straight along a stem's centre-line from ly0 up to ly1 (draw the stem over
    it, EPS to its left).  xt / xb: x of the top / bottom extremes; yr: y of
    the right extreme; kl: tension of the two corners at the stem.  One
    smooth closed stroke, so the counter is a clean round (cf. loop())."""
    yr = (b + t) / 2 if yr is None else yr
    kl = k if kl is None else kl
    (g.pen(l, ly1, w)
        .v(xt, t, k=kl, k2=k)
        .h(r, yr, k=k)
        .v(xb, b, k=k)
        .h(l, ly0, k=k, k2=kl)
        .close())


def _ms(g: G):
    """Stroke factor for crowded three-stem letters in Mono."""
    return 0.86 if g.mono else 1.0


# ---------------------------------------------------------------------------
# capitals
# ---------------------------------------------------------------------------

@glyph("Gamma", 0x393, zone="uc")
def Gamma(g: G):
    bw = g.wd(420, 420)
    g.stem(0, 0, g.cap)
    g.bar(0, bw, g.cap - g.hh)


@glyph("Delta", 0x394, zone="uc")
def Delta(g: G):
    bw = g.wd(630, 500, grow=0.8)
    cx = bw / 2
    r = g.hw * DIAG + g.W * 0.22       # keep the caps off the bar's end caps
    g.line(r, g.hh, cx, g.cap - g.hh * DIAG, DIAG)
    g.line(bw - r, g.hh, cx, g.cap - g.hh * DIAG, DIAG)
    g.bar(0, bw, g.hh)


@glyph("Theta", 0x398, zone="uc")
def Theta(g: G):
    bw = g.wd(650, 480, grow=0.8)
    g.oval(0, -g.ov, bw, g.cap + g.ov)
    g.bar(bw * 0.3 - g.grow * 0.15, bw * 0.7 + g.grow * 0.15, g.cap / 2)


@glyph("uni03F4", 0x3F4, zone="uc")
def Theta_symbol(g: G):
    bw = g.wd(650, 480, grow=0.8)
    g.oval(0, -g.ov, bw, g.cap + g.ov)
    g.bar(g.hw, bw - g.hw, g.cap / 2)


@glyph("Lambda", 0x39B, zone="uc")
def Lambda(g: G):
    bw = g.wd(600, 490)
    cx = bw / 2
    r = g.hw * DIAG
    g.line(r, g.hh, cx, g.cap - g.hh * DIAG, DIAG)
    g.line(bw - r, g.hh, cx, g.cap - g.hh * DIAG, DIAG)


@glyph("Xi", 0x39E, zone="uc")
def Xi(g: G):
    bw = g.wd(510, 460)
    g.bar(6, bw - 6, g.cap - g.hh)
    g.bar(bw * 0.13, bw * 0.87, g.cap * 0.5 - 4)
    g.bar(0, bw, g.hh)


@glyph("Pi", 0x3A0, zone="uc")
def Pi(g: G):
    bw = g.wd(540, 460)
    g.bar(0, bw, g.cap - g.hh)
    g.stem(0, 0, g.cap)
    g.stem(bw - g.W, 0, g.cap)


@glyph("Sigma", 0x3A3, zone="uc")
def Sigma(g: G):
    bw = g.wd(520, 460)
    r = g.hw * 1.05
    vx = bw * 0.54 + g.grow * 0.1
    vy = g.cap * 0.5
    g.bar(0, bw - 6, g.cap - g.hh)
    g.bar(0, bw, g.hh)
    g.line(r, g.cap - g.hh, vx, vy, DIAG)
    g.line(vx, vy, r, g.hh, DIAG)


@glyph("Phi", 0x3A6, zone="uc")
def Phi(g: G):
    bw = g.wd(700, 510, grow=0.8)
    cx = bw / 2
    w = _ms(g)
    g.oval(0, g.cap * 0.13, bw, g.cap * 0.87, w=w)
    g.vstem(cx, 0, g.cap, w=w)


@glyph("Psi", 0x3A8, zone="uc")
def Psi(g: G):
    bw = g.wd(660, 510, grow=0.8)
    cx = bw / 2
    w = _ms(g)
    _cup(g, 0, bw, g.cap, g.cap * 0.24, side=0.5, w=w)
    g.vstem(cx, 0, g.cap, w=w)


@glyph("Omega", 0x3A9, zone="uc")
def Omega(g: G):
    bw = g.wd(660, 500, grow=0.8)
    cx = bw / 2
    xe = bw * 0.33
    d = (0.42, 1)
    (g.pen(xe, g.hh)
        .to(g.hw, g.cap * 0.52, (-d[0], d[1]), "u", k=0.6)
        .v(cx, g.cap + g.ov - g.hh, k=0.58)
        .h(bw - g.hw, g.cap * 0.52, k=0.58)
        .to(bw - xe, g.hh, "d", (-d[0], -d[1]), k=0.6)
        .end())
    # feet end exactly where the legs end, so the caps coincide (clean round corner)
    g.bar(0, xe + g.hw, g.hh)
    g.bar(bw - xe - g.hw, bw, g.hh)


@glyph("uni03DC", 0x3DC, zone="uc")
def Digamma(g: G):
    bw = g.wd(410, 420)
    g.stem(0, 0, g.cap)
    g.bar(0, bw, g.cap - g.hh)
    g.bar(0, bw * 0.88, g.cap * 0.5 - 6)


# ---------------------------------------------------------------------------
# lowercase
# ---------------------------------------------------------------------------

@glyph("alpha", 0x3B1, zone="lc")
def alpha(g: G):
    bw = g.wd(520, 476)
    bowl = g.wd(440, 404, grow=0.7)
    xs = bowl - g.hw
    top = g.xh + g.ov
    bowl_left(g, xs, 0, -g.ov, top)
    # right stroke: straight down, kicking out to the right at the foot
    (g.pen(xs, g.xh - g.hh)
        .l(xs, 128 + g.grow * 0.2)
        .v(xs + 84 + g.grow * 0.25, g.hh - g.ov * 0.3, k=0.6)
        .l(bw - g.hw * 0.7, g.hh - g.ov * 0.3)
        .end())
    g.anchor("top", (bowl - g.hw * 0.4) / 2, g.xh)


@glyph("beta", 0x3B2, zone="lc")
def beta(g: G):
    bw = g.wd(470, 450, grow=0.8)
    xs = g.hw
    l = xs + EPS                       # loops ride the stem's centre-line
    tu = g.asc + g.ov - g.hh           # skeleton top of the upper bowl
    bl = -g.ov + g.hh                  # skeleton bottom of the lower bowl
    wy = g.xh * 0.80 - g.grow * 0.1    # waist (skeleton)
    ru = bw - 40 - g.hw                # upper bowl right (skeleton)
    rb = bw - g.hw                     # lower bowl right (skeleton)
    rc = g.hw * 1.6 + 8                # waist corners: above the pen radius, small
                                       # enough that the two corners meet in the stem
    # upper bowl: round shoulder off the stem, small round corner at the waist
    _rloop(g, l, wy, ru, tu, wy + rc, tu - (tu - wy) * 0.40,
           xt=l + (ru - l) * 0.5, xb=l + rc, yr=(wy + tu) / 2 + 4, kl=0.58)
    # lower bowl: small round corner at the waist, wide round bottom into the stem
    _rloop(g, l, bl, rb, wy, bl + (wy - bl) * 0.42, wy - rc,
           xt=l + rc, xb=l + (rb - l) * 0.48, yr=(bl + wy) / 2 - 6)
    g.line(xs, g.desc + g.hh, xs, tu - (tu - wy) * 0.40)


@glyph("gamma", 0x3B3, zone="lc")
def gamma(g: G):
    bw = g.wd(456, 466)
    cx = bw / 2
    r = g.hw * 0.94
    yt = g.xh - g.hh
    yv = 44 + g.grow * 0.1
    # left arm runs into the tail's centre-line
    g.line(r, yt, cx, yv - 18, DIAG)
    # right arm bends into a vertical descender tail
    x0 = bw - r
    d = (cx - x0, yv - yt)
    tp = 0.80
    (g.pen(x0, yt, DIAG)
        .l(x0 + d[0] * tp, yt + d[1] * tp)
        .to(cx, yv - 70, d, "d", k=0.62, w=1.0)
        .l(cx, g.desc + g.hh + 10)
        .end())


@glyph("delta", 0x3B4, zone="lc")
def delta(g: G):
    bw = g.wd(476, 470)
    cx = bw / 2
    g.oval(0, -g.ov, bw, g.xh + g.ov)
    ty = g.xh + g.ov - g.hh
    xl = bw * 0.22 + g.grow * 0.1
    # neck leaves the bowl's top tangentially, swings left and up, then
    # hooks right at the ascender
    (g.pen(cx + 16, ty)
        .h(xl, g.xh + 100 + g.grow * 0.25, k=0.6)
        .v(xl + 150 + g.grow * 0.2, g.asc + g.ov * 0.5 - g.hh, k=0.6)
        .to(bw - g.hw - 26, g.asc - 64 - g.grow * 0.2, "r", (0.42, -1), k=0.62)
        .end())


@glyph("epsilon", 0x3B5, zone="lc")
def epsilon(g: G):
    bw = g.wd(420, 436)
    top = g.xh + g.ov
    bot = -g.ov
    cx = bw / 2
    wy = g.xh * 0.53
    wx = cx + 14
    lu = g.hw + 30 + g.grow * 0.1
    ll = g.hw
    (g.pen(bw - g.hw - 10, g.xh * 0.80)
        .to(cx + 6, top - g.hh, (-0.4, 1), "l", k=0.62)
        .h(lu, (top - g.hh + wy) / 2 + 4, k=0.58)
        .v(wx, wy, k=0.58)
        .end())
    (g.pen(wx, wy)
        .h(ll, (wy + bot + g.hh) / 2 - 4, k=0.58)
        .v(cx + 6, bot + g.hh, k=0.58)
        .to(bw - g.hw - 4, g.xh * 0.21, "r", (0.4, 1), k=0.62)
        .end())


@glyph("uni03F5", 0x3F5, zone="lc")
def epsilon_lunate(g: G):
    bw = g.wd(430, 446)
    c_shape(g, 0, bw, -g.ov, g.xh + g.ov, t_top=0.78, t_bot=0.22)
    g.bar(g.hw, bw * 0.78, g.xh * 0.5)


@glyph("zeta", 0x3B6, zone="lc")
def zeta(g: G):
    bw = g.wd(420, 440)
    cx = bw / 2
    ty = g.asc - g.hh
    g.bar(26, bw, ty)
    x0 = bw - g.hw * 1.05 - 6
    px, py = g.hw + 70 + g.grow * 0.2, g.xh * 0.62
    d = (px - x0, py - ty)
    p = g.pen(x0, ty).l(px, py, w=DIAG)
    p.to(g.hw, g.xh * 0.2, d, "d", k=0.6, w=1.0)
    _tail(p, g, cx + 10, bw - g.hw, g.hh + 4)
    p.end()


@glyph("xi", 0x3BE, zone="lc")
def xi(g: G):
    bw = g.wd(420, 440)
    cx = bw / 2
    ty = g.asc - g.hh
    g.bar(26, bw, ty)
    wy = g.xh * 0.80
    wx = cx + 20
    (g.pen(cx + 40, ty)
        .h(g.hw + 46 + g.grow * 0.1, (ty + wy) / 2, k=0.6)
        .v(wx, wy, k=0.6)
        .end())
    p = g.pen(wx, wy).h(g.hw, wy * 0.52, k=0.6)
    _tail(p, g, cx + 10, bw - g.hw, g.hh + 4)
    p.end()


@glyph("eta", 0x3B7, zone="lc")
def eta(g: G):
    bw = g.wd(436, 456)
    g.stem(0, 0, g.xh)
    arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, g.desc)


@glyph("theta", 0x3B8, zone="lc")
def theta(g: G):
    bw = g.wd(470, 466)
    g.oval(0, -g.ov, bw, g.asc + g.ov)
    g.bar(g.hw, bw - g.hw, g.asc * 0.5 - 6)


@glyph("theta1", 0x3D1, zone="lc")
def theta_symbol(g: G):
    bw = g.wd(500, 470)
    xr = bw * 0.68 + g.grow * 0.25
    xl = g.hw + 6
    xll = bw * 0.30 - g.grow * 0.25
    top = g.asc + g.ov
    ty = g.xh * 0.6
    (g.pen(xl, g.xh - g.hh - 40)
        .l(xl, g.xh * 0.42)
        .v((xl + xr) / 2, -g.ov + g.hh, k=0.6)
        .h(xr, g.xh * 0.42, k=0.6)
        .l(xr, g.asc - 180)
        .v((xr + xll) / 2, top - g.hh, k=0.58)
        .h(xll, g.asc - 180, k=0.58)
        .v(xll + 130, ty, k=0.6)
        .l(xr + 130 + g.grow * 0.4, ty)      # a real tail at every weight, never a bump
        .end())


@glyph("iota", 0x3B9, zone="lc")
def iota(g: G):
    if g.mono:
        bw = g.wd(0, 420)
        xs = bw * 0.44
        g.bar(bw * 0.08, xs + g.hw, g.xh - g.hh)
    else:
        bw = g.wd(196, grow=0.7)
        xs = g.hw
    (g.pen(xs, g.xh - g.hh)
        .l(xs, 120 + g.grow * 0.2)
        .v(xs + 92 + g.grow * 0.3, g.hh - g.ov * 0.3, k=0.6)
        .l(bw - g.hw * 0.7, g.hh - g.ov * 0.3)
        .end())
    g.anchor("top", xs, g.xh)


@glyph("kappa", 0x3BA, zone="lc")
def kappa(g: G):
    bw = g.wd(420, 450)
    g.stem(0, 0, g.xh)
    jx = g.W + 6
    jy = g.xh * 0.40
    g.line(jx, jy, bw - g.hw * 1.1, g.xh - g.hh, w0=0.9, w1=DIAG)
    g.line(jx + 70 + g.grow * 0.2, jy + 66, bw - g.hw * 1.05, g.hh, w0=DIAG, w1=DIAG)


@glyph("uni03F0", 0x3F0, zone="lc")
def kappa_symbol(g: G):
    bw = g.wd(470, 466)
    r = g.hw * DIAG
    y0, y1 = g.xh - g.hh, g.hh
    x1 = bw - r
    # round hook: rises on the left, over a round top, then flows tangentially
    # into the long diagonal.  The hook is an OPEN curl ending in a plain
    # round terminal: its leg shortens with weight so the terminal always
    # stays clear of the crossing diagonal (no closed blob counter in Black).
    xp = r + bw * 0.22 + g.grow * 0.4
    xq = xp + 60 + g.grow * 0.25
    yq = y0 - 96 - g.grow * 0.1
    d = (x1 - xq, y1 - yq)
    wt = 0.88                                     # slightly lighter terminal
    (g.pen(g.hw * wt, y0 - 150 + g.grow * 0.75, wt)
        .v(xp, y0, k=0.58, w=1.0)
        .to(xq, yq, "r", d, k=0.58, w=DIAG)
        .l(x1, y1, w=DIAG)
        .end())
    g.line(bw - r, y0, r, y1, DIAG)


@glyph("lambda", 0x3BB, zone="lc")
def lambda_(g: G):
    bw = g.wd(470, 470)
    r = g.hw * DIAG
    x0, y0 = g.hw + 34, g.asc - g.hh
    x1, y1 = bw - r, g.hh
    g.line(x0, y0, x1, y1, DIAG)
    yj = g.xh * 0.60
    xj = x0 + (x1 - x0) * (y0 - yj) / (y0 - y1)
    g.line(r, g.hh, xj, yj, DIAG)


@glyph("mu", 0x3BC, 0xB5, zone="lc")
def mu(g: G):
    bw = g.wd(436, 456)
    g.transform(rot180(bw / 2, g.xh / 2))
    g.stem(0, 0, g.xh)
    arch(g, g.hw, bw - g.hw, g.xh + g.ov * 0.4, 0)
    g.transform(None)
    g.stem(0, g.desc, g.xh * 0.5)


@glyph("nu", 0x3BD, zone="lc")
def nu(g: G):
    bw = g.wd(440, 460)
    r = g.hw * 0.94
    vx, vy = bw * 0.46, g.hh
    g.line(r, g.xh - g.hh, vx, vy, DIAG)
    (g.pen(vx, vy, DIAG)
        .to(bw - g.hw, g.xh - g.hh, (0.42, 1), "u", k=0.62, w=1.0)
        .end())


@glyph("pi", 0x3C0, zone="lc")
def pi(g: G):
    bw = g.wd(530, 470)
    ty = g.xh - g.hh
    g.bar(0, bw, ty)
    g.stem(54 - g.grow * 0.15, 0, g.xh)          # legs move out with weight: open counter
    xs = bw - 64 + g.grow * 0.15 - g.hw
    (g.pen(xs, ty)
        .l(xs, 110 + g.grow * 0.2)
        .v(xs + 60 + g.grow * 0.2, g.hh - g.ov * 0.3, k=0.6)
        .l(xs + 64 + g.grow * 0.2, g.hh - g.ov * 0.3)
        .end())


@glyph("omega1", 0x3D6, zone="lc")
def pi_symbol(g: G):
    bw = g.wd(700, 520, grow=1.0)
    s = 0.86 if g.mono else 1.0
    ty = g.xh - g.hh
    g.bar(0, bw, ty)
    cx = bw / 2
    xa = (18 if g.mono else 50) + g.hw * s    # Mono: less overhang keeps the lobes open
    g.transform(None)
    for tx in (None, mirror_x(cx)):
        g.transform(tx)
        (g.pen(xa, ty, s)
            .l(xa, g.xh * 0.44)
            .v((xa + cx) / 2, -g.ov + g.hh * s, k=0.6)
            .h(cx, g.xh * 0.36, k=0.6)
            .l(cx, g.xh * 0.56)
            .end())
    g.transform(None)


@glyph("rho", 0x3C1, zone="lc")
def rho(g: G):
    bw = g.wd(476, 470)
    g.oval(0, -g.ov, bw, g.xh + g.ov)
    g.stem(0, g.desc, g.xh * 0.5)


@glyph("uni03F1", 0x3F1, zone="lc")
def rho_symbol(g: G):
    bw = g.wd(476, 470)
    g.oval(0, -g.ov, bw, g.xh + g.ov)
    xs = g.hw
    (g.pen(xs, g.xh * 0.5)
        .l(xs, -40)
        .v(xs + 120 + g.grow * 0.3, g.desc + 50 + g.hh, k=0.6)
        .l(bw * 0.78, g.desc + 50 + g.hh)
        .end())


@glyph("sigma", 0x3C3, zone="lc")
def sigma(g: G):
    bw = g.wd(510, 476)
    bo = g.wd(470, 430)
    g.oval(0, -g.ov, bo, g.xh, k=0.6)
    g.bar(bo / 2, bw, g.xh - g.hh)


@glyph("sigma1", 0x3C2, zone="lc")
def sigma_final(g: G):
    bw = g.wd(420, 440)
    top = g.xh + g.ov
    cx = bw / 2
    p = (g.pen(bw - g.hw - 8, g.xh * 0.79)
         .to(cx + 6, top - g.hh, (-0.36, 1), "l", k=0.62)
         .h(g.hw, g.xh * 0.46, k=0.58))
    _tail(p, g, cx + 10, bw - g.hw, g.hh + 4)
    p.end()


@glyph("tau", 0x3C4, zone="lc")
def tau(g: G):
    bw = g.wd(420, 450)
    ty = g.xh - g.hh
    g.bar(0, bw, ty)
    xs = bw * 0.44
    (g.pen(xs, ty)
        .l(xs, 128 + g.grow * 0.2)
        .v(xs + 100 + g.grow * 0.3, g.hh - g.ov * 0.3, k=0.6)
        .l(bw - g.hw * 0.7 - 20, g.hh - g.ov * 0.3)
        .end())


@glyph("upsilon", 0x3C5, zone="lc")
def upsilon(g: G):
    bw = g.wd(446, 456)
    _cup(g, 0, bw, g.xh, -g.ov)


@glyph("phi", 0x3C6, zone="lc")
def phi(g: G):
    bw = g.wd(580, 510)
    cx = bw / 2
    w = _ms(g)
    l, r = g.hw * w, bw - g.hw * w
    ym = g.xh * 0.5
    (g.pen(l, g.xh - g.hh * w - 30, w)
        .l(l, g.xh * 0.46)
        .v(cx, -g.ov + g.hh * w, k=0.6)
        .h(r, ym, k=0.6)
        .v((cx + r) / 2, g.xh + g.ov - g.hh * w, k=0.6)
        .h(cx, g.xh * 0.6, k=0.6)
        .l(cx, g.desc + g.hh * w)
        .end())


@glyph("phi1", 0x3D5, zone="lc")
def phi_symbol(g: G):
    bw = g.wd(560, 500)
    w = _ms(g)
    g.oval(0, -g.ov, bw, g.xh + g.ov, w=w)
    g.vstem(bw / 2, g.desc, g.asc, w=w)


@glyph("chi", 0x3C7, zone="lc")
def chi(g: G):
    bw = g.wd(470, 470)
    r = g.hw * DIAG
    g.line(r, g.xh - g.hh, bw - r, g.desc + g.hh, DIAG)
    g.line(bw - r, g.xh - g.hh, r, g.desc + g.hh, DIAG)


@glyph("psi", 0x3C8, zone="lc")
def psi(g: G):
    bw = g.wd(560, 510)
    w = _ms(g)
    _cup(g, 0, bw, g.xh, -g.ov, w=w)
    g.vstem(bw / 2, g.desc, g.asc, w=w)


@glyph("omega", 0x3C9, zone="lc")
def omega(g: G):
    bw = g.wd(660, 520, grow=1.0)
    s = 0.86 if g.mono else 1.0
    cx = bw / 2
    xa = g.hw * s
    for tx in (None, mirror_x(cx)):
        g.transform(tx)
        (g.pen(xa, g.xh - g.hh * s, s)
            .l(xa, g.xh * 0.46)
            .v((xa + cx) / 2, -g.ov + g.hh * s, k=0.6)
            .h(cx, g.xh * 0.36, k=0.6)
            .l(cx, g.xh * 0.58)
            .end())
    g.transform(None)


@glyph("uni03DD", 0x3DD, zone="lc")
def digamma(g: G):
    bw = g.wd(380, 420)
    g.stem(0, g.desc, g.xh)
    g.bar(0, bw, g.xh - g.hh)
    g.bar(0, bw * 0.86, (g.xh + g.desc) * 0.5 - 6)


# ---------------------------------------------------------------------------
# Greek marks
# ---------------------------------------------------------------------------
#
# Breathings for Greek bases (picked automatically through the `.gr`
# suffix): comma-shaped with the head on top — psili like ’ (tail curling
# down-left), dasia its mirror image (tail curling down-right).

def _dotd(g: G):
    return g.W * 1.08 + 18


def _breathing(g: G, sign):
    """Comma with its round head on top and a lighter tail curling away."""
    y0 = g.xh + 56 + g.grow * 0.12
    h = 168 + g.grow * 0.5
    d = _dotd(g) * 0.94
    yc = y0 + h - d / 2
    g.dot(sign * 4, yc, d)
    wt = 0.66
    (g.pen(sign * (4 + d * 0.22), yc, wt)
        .to(-sign * (30 + g.grow * 0.35), y0 + g.hh * wt, (0, -1), (-sign * 0.6, -1), k=0.6)
        .end())
    g.anchor("_top", 0, g.xh)
    g.anchor("top", 0, y0 + h)


@glyph("commaabovecomb.gr", kind="mark")
def psili(g: G):
    _breathing(g, 1)


@glyph("reversedcommaabovecomb.gr", kind="mark")
def dasia(g: G):
    _breathing(g, -1)


def _sub(g: G, name):
    sub = G(g.p, name)
    GLYPHS[name].func(sub)
    return sub


def _xext(g: G, sub: G):
    """Approximate ink x-extent of a sub-glyph's skeleton + dots."""
    xs = []
    for st in sub.strokes:
        r = g.hw * max(st.widths) * st.scale
        for sg in st.segs:
            for pt in sg.pts:
                xs += [pt[0] - r, pt[0] + r]
    for c in sub.extra:
        xs += [pt[0] for pt in c.points()]
    return min(xs), max(xs)


def _mark_anchors(g: G, top):
    g.anchor("_top", 0, g.xh)
    g.anchor("top", 0, top)


def _side_by_side(first, second):
    """Breathing (or dialytika) on the left, accent on the right, the pair
    centred on x=0 with a weight-aware gap."""
    def f(g: G):
        a, b = _sub(g, first), _sub(g, second)
        a0, a1 = _xext(g, a)
        b0, b1 = _xext(g, b)
        gap = 26 + g.grow * 0.12
        da = -gap / 2 - a1
        db = gap / 2 - b0
        c = (a0 + da + b1 + db) / 2
        _put(g, first, da - c, 0)
        _put(g, second, db - c, 0)
        _mark_anchors(g, max(a.anchors["top"][1], b.anchors["top"][1]))
    return f


def _between(inner, lift=10):
    """Dialytika with `inner` (tonos / varia) standing between the dots."""
    def f(g: G):
        b = _sub(g, inner)
        b0, b1 = _xext(g, b)
        cx = -(b0 + b1) / 2
        half = (b1 - b0) / 2
        d = _dotd(g)
        y0 = g.xh + 60 + g.grow * 0.12
        sp = half + 22 + g.grow * 0.08 + d / 2
        g.dot(-sp, y0 + d / 2, d)
        g.dot(sp, y0 + d / 2, d)
        _put(g, inner, cx, lift)
        _mark_anchors(g, max(y0 + d, b.anchors["top"][1] + lift))
    return f


def _stacked(lower, upper, gap=30):
    """`upper` centred above `lower` (perispomeni over breathing/dialytika)."""
    def f(g: G):
        a = _put(g, lower)
        b = _sub(g, upper)
        base = g.xh + 56 + g.grow * 0.12 + 6        # tilde's ink bottom
        dy = a.anchors["top"][1] - base + gap
        _put(g, upper, 0, dy)
        _mark_anchors(g, b.anchors["top"][1] + dy)
    return f


for _br in ("commaabovecomb", "reversedcommaabovecomb"):
    glyph(f"{_br}_tonoscomb", kind="mark")(_side_by_side(_br + ".gr", "tonoscomb"))
    glyph(f"{_br}_gravecomb", kind="mark")(_side_by_side(_br + ".gr", "gravecomb"))
    glyph(f"{_br}_perispomenicomb", kind="mark")(_stacked(_br + ".gr", "perispomenicomb"))

glyph("dieresiscomb_tonoscomb", kind="mark")(_between("tonoscomb"))
glyph("dieresiscomb_gravecomb", kind="mark")(_between("gravecomb"))
glyph("dieresiscomb_perispomenicomb", kind="mark")(_stacked("dieresiscomb", "perispomenicomb", gap=26))


# ---------------------------------------------------------------------------
# spacing accents / punctuation
# ---------------------------------------------------------------------------

def _tonos_line(g: G, y0, h, dx=0.0):
    r = g.hh * MW
    g.line(dx - 28, y0 + r, dx + 30, y0 + h - r, MW)


def _spacing(name, cp, mark):
    def f(g: G):
        _put(g, mark)
        g.sb = {"l": 24, "r": 24}
    glyph(name, cp)(f)


_spacing("tonos", 0x384, "tonoscomb")
_spacing("dieresistonos", 0x385, "dieresiscomb_tonoscomb")
_spacing("uni1FBD", 0x1FBD, "commaabovecomb.gr")                 # koronis
_spacing("uni1FBF", 0x1FBF, "commaabovecomb.gr")                 # psili
_spacing("uni1FFE", 0x1FFE, "reversedcommaabovecomb.gr")         # dasia
_spacing("uni1FC0", 0x1FC0, "perispomenicomb")
_spacing("uni1FC1", 0x1FC1, "dieresiscomb_perispomenicomb")
_spacing("uni1FCD", 0x1FCD, "commaabovecomb_gravecomb")
_spacing("uni1FCE", 0x1FCE, "commaabovecomb_tonoscomb")
_spacing("uni1FCF", 0x1FCF, "commaabovecomb_perispomenicomb")
_spacing("uni1FDD", 0x1FDD, "reversedcommaabovecomb_gravecomb")
_spacing("uni1FDE", 0x1FDE, "reversedcommaabovecomb_tonoscomb")
_spacing("uni1FDF", 0x1FDF, "reversedcommaabovecomb_perispomenicomb")
_spacing("uni1FED", 0x1FED, "dieresiscomb_gravecomb")
_spacing("uni1FEE", 0x1FEE, "dieresiscomb_tonoscomb")
_spacing("uni1FEF", 0x1FEF, "gravecomb")                         # varia
_spacing("uni1FFD", 0x1FFD, "tonoscomb")                         # oxia


@glyph("uni0374", 0x374)
def keraia(g: G):
    g.sb = {"l": 16, "r": 16}
    _tonos_line(g, g.cap - 170 - g.grow * 0.25, 170 + g.grow * 0.25)


@glyph("uni0375", 0x375)
def lowerkeraia(g: G):
    g.sb = {"l": 16, "r": 16}
    _tonos_line(g, -190 - g.grow * 0.25, 170 + g.grow * 0.25)
