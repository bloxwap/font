"""Rasm (letter skeletons) x joining forms.

Each function draws one body in local coordinates for `c.form` in
('isol', 'init', 'medi', 'fina') and fills the Ctx (see core.py).
Style: rounded geometric naskh-kufi; round caps everywhere except the
butt-capped join stubs added by core.finish().
"""
from __future__ import annotations

import math

from .core import (AH, D, DESC, DGAP, DIAG, JS, JY, KH, LW, ST, T, Ctx, gw, mk_hamza, stamp)

JOIN = 0.52


# ---------------------------------------------------------------------------
# shared constructions
# ---------------------------------------------------------------------------

def bowl(g, xr, xl, yr, yl, bottom, wr=1.0, round_=0.9):
    """Deep U bowl (noon, lam, seen, qaf ...): right arm from (xr, yr) down,
    round bottom, left arm up to (xl, yl).  All skeleton coordinates."""
    xc = (xr + xl) / 2
    r = (xr - xl) / 2
    ya = bottom + g.hh + r * round_
    p = g.pen(xr, yr, wr)
    p.l(xr, ya, w=1.0).v(xc, bottom + g.hh, k=0.6).h(xl, ya, k=0.6).l(xl, yl)
    p.end()
    return xc


def boat_tail(g, x_from, xl, tip_y, lc):
    """Flat baseline from x_from leftwards, curving up to a tip at xl."""
    jy = JY(g)
    g.pen(x_from, jy).l(xl + lc, jy).h(xl, tip_y - g.hh, k=0.6).end()


def cup(g, xa, xb, top):
    """u-shaped cup between two teeth (seen), bottom on the join line."""
    g.pen(xa, top - g.hh).v((xa + xb) / 2, JY(g), k=0.6).h(xb, top - g.hh, k=0.6).end()


def c_bowl(g, start, d0, xl, xm, xe, bottom, ye, ymid=None):
    """Big descending C bowl (hah, ain): from `start` (direction d0) to the
    leftmost point, round bottom, ending up-right at (xe, ye)."""
    x0, y0 = start
    ymid = (y0 + bottom) / 2 if ymid is None else ymid
    (g.pen(x0, y0)
        .to(xl, ymid, d0, "d", k=0.6)
        .v(xm, bottom + g.hh, k=0.6)
        .to(xe, ye, "r", (0.5, 1), k=0.62)
        .end())


# ---------------------------------------------------------------------------
# alef
# ---------------------------------------------------------------------------

def r_alef(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    top = AH(g)
    if c.form == "fina":
        rc = hw + 26 + g.grow * 0.1
        g.pen(rc, jy).h(0, jy + rc, k=0.6).l(0, top - hh).end()
        c.rx = rc
        c.jr = JS(g) * 0.8
    else:
        g.vstem(0, 0, top)
        c.sbr = gw(g, 62, 0, 0.3)
    c.sbl = gw(g, 62, 0, 0.3)
    c.pt["above"] = (0, top + DGAP(g) * 0.7)
    c.pt["below"] = (0, -DGAP(g) * 0.7)
    c.pt["hh"] = (hw + 64 + g.grow * 0.4, top * 0.6)
    c.top = (0, top)
    c.bot = (0, 0)


# ---------------------------------------------------------------------------
# beh / noon / yeh teeth (initial & medial) and their final shapes
# ---------------------------------------------------------------------------

def tooth(c: Ctx, h=None):
    g = c.g
    h = T(g) if h is None else h
    g.vstem(0, 0, h)
    c.lx = c.rx = 0
    c.sbr = gw(g, 50, 0, 0.3)
    c.pt["above"] = (0, h + DGAP(g))
    c.pt["below"] = (0, -DGAP(g))
    c.pt["hh"] = (g.hw + 60 + g.grow * 0.4, h * 0.62)
    c.top = (0, h)
    c.bot = (0, 0)


def r_beh(c: Ctx):
    g = c.g
    if c.form in ("init", "medi"):
        return tooth(c)
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    bw = gw(g, 520, 440, 1.0)
    tipR, tipL = 0.76 * t, 0.64 * t
    xr, xl = bw - hw, hw
    rr = hw * 0.35 + 16
    lc = bw * 0.38
    (g.pen(xr, tipR - hh).l(xr, jy + rr).v(xr - rr, jy, k=0.6)
        .l(xl + lc, jy).h(xl, tipL - hh, k=0.6).end())
    c.rx = xr
    c.jr = JS(g)
    xc = bw * 0.5
    c.pt["above"] = (xc, g.H + DGAP(g) * 0.75)
    c.pt["below"] = (xc, -DGAP(g))
    c.pt["hh"] = (xr + hw + 50, tipR * 0.7)
    c.top = (xc, tipL)
    c.bot = (xc, 0)


def r_noon(c: Ctx):
    g = c.g
    if c.form in ("init", "medi"):
        return tooth(c)
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    nw = gw(g, 400, 360, 0.8)
    bottom = DESC(g)
    tip = 0.62 * t
    xr, xl = nw - hw, hw
    xc = nw / 2
    if c.form == "isol":
        bowl(g, xr, xl, tip - hh, tip - hh, bottom)
    else:
        r = (xr - xl) / 2
        ya = bottom + hh + r * 0.9
        rx0 = xr + gw(g, 30, 20, 0.3)
        (g.pen(rx0, jy).to(xc, bottom + hh, "l", "l", k=0.62)
            .h(xl, ya, k=0.6).l(xl, tip - hh).end())
        c.rx = rx0
        c.jr = JS(g)
    c.pt["above"] = (xc, g.H * 0.5 + 6)
    c.pt["below"] = (xc, bottom - DGAP(g))
    c.pt["ring"] = (xc, bottom - D(g) * 0.15)
    c.top = (xc, tip)
    c.bot = (xc, bottom)


def r_yeh(c: Ctx):
    """Yeh family (ى ي ی): tooth in init/medi; S-shaped returning tail."""
    g = c.g
    if c.form in ("init", "medi"):
        return tooth(c)
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    yw = gw(g, 560, 480, 1.0)
    bottom = DESC(g) - 0.15 * g.grow
    xR = yw - hw
    lc = 0.28 * yw
    tipy = 0.08 * t
    if c.form == "isol":
        yt = 0.82 * t
        p = g.pen(0.80 * yw, yt - hh)
        p.to(0.47 * yw, (yt + jy) / 2 + 6, (-1, 0.15), "d", k=0.6)
        p.v(0.66 * yw, jy, k=0.6)
        p.h(xR, (jy + bottom) / 2 - 8, k=0.6)
        c.pt["above"] = (0.64 * yw, yt + DGAP(g))
        c.top = (0.64 * yw, yt)
    else:
        rx0 = 0.66 * yw
        y1 = -36 - 0.45 * g.grow
        ym = -104 - 0.75 * g.grow
        p = g.pen(rx0, jy)
        p.to(0.46 * yw, y1, "l", "d", k=0.6)
        p.v(0.64 * yw, ym, k=0.6)
        p.h(xR, (ym + bottom) / 2, k=0.6)
        c.rx = rx0
        c.jr = JS(g) + xR + hw - rx0
        c.pt["above"] = (0.56 * yw, g.H + DGAP(g))
        c.top = (0.56 * yw, g.H)
    p.v(0.55 * yw, bottom + hh, k=0.6).l(xl_ := hw + lc, bottom + hh).h(hw, tipy - hh, k=0.6)
    p.end()
    c.pt["below"] = (0.34 * yw, -DGAP(g) * 0.55)
    c.pt["hh"] = (yw + 30, 0.6 * t)
    c.bot = (0.5 * yw, bottom)


def r_yehbarree(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    bw = gw(g, 640, 500, 1.1)
    yb = jy - 34 - 0.15 * g.grow
    xr = bw - hw
    lc = 0.2 * bw
    tip = 0.62 * t
    if c.form == "isol":
        top = 0.72 * t
        p = g.pen(xr, top - hh).to(xr - gw(g, 150, 120, 0.3), yb, (-0.25, -1), "l", k=0.6)
    else:
        p = g.pen(xr, jy).to(xr - gw(g, 130, 110, 0.3), yb, "l", "l", k=0.6)
        c.rx = xr
        c.jr = JS(g)
    p.l(hw + lc, yb).h(hw, tip - hh, k=0.6).end()
    c.pt["above"] = (bw * 0.55, g.H + DGAP(g) * 0.8)
    c.pt["below"] = (bw * 0.5, yb - hh - DGAP(g))
    c.top = (bw * 0.55, tip)
    c.bot = (bw * 0.5, yb - hh)


# ---------------------------------------------------------------------------
# reh, dal
# ---------------------------------------------------------------------------

def r_reh(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    rw = gw(g, 236, 220, 0.6)
    bottom = DESC(g) * 0.94
    rt = 0.6 * t
    if c.form == "isol":
        g.pen(rw - hw, rt - hh).to(hw, bottom + hh, (-0.16, -1), (-1, -0.45), k=0.6).end()
        c.pt["above"] = (rw - hw - 10, rt + DGAP(g))
        c.top = (rw - hw, rt)
        c.sbr = gw(g, 40, 0, 0.3)
    else:
        rx0 = rw - hw
        g.pen(rx0, jy).to(hw, bottom + hh, (-0.42, -1), (-1, -0.5), k=0.6).end()
        c.rx = rx0
        c.jr = JS(g)
        c.pt["above"] = (rx0 - 6, g.H + DGAP(g))
        c.top = (rx0, g.H)
    c.sbl = gw(g, 30, 0, 0.2)
    c.pt["below"] = (rw * 0.78, -DGAP(g) * 0.6)
    c.pt["ring"] = (rw * 0.62, bottom * 0.62)
    c.pt["bar"] = (rw * 0.46, bottom * 0.42)
    c.bot = (rw * 0.4, bottom)


def r_dal(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    dw = gw(g, 300, 280, 0.75)
    dt = gw(g, 330, 320, 0.3)
    xt = 0.30 * dw
    xr = dw - hw
    rc = 0.28 * dw
    (g.pen(xt, dt - hh).to(xr, jy + rc, (0.62, -1), "d", k=0.6)
        .v(xr - rc, jy, k=0.6).l(hw, jy).end())
    if c.form == "fina":
        c.rx = xr - rc
        c.jr = rc + hw + JS(g) * 0.6
    c.pt["above"] = (xt + 0.1 * dw, dt + DGAP(g))
    c.pt["below"] = (dw * 0.5, -DGAP(g))
    c.pt["ring"] = (xr - rc * 0.4, -D(g) * 0.35)
    c.top = (xt + 0.1 * dw, dt)
    c.bot = (dw * 0.5, 0)


# ---------------------------------------------------------------------------
# jeem / hah / khah
# ---------------------------------------------------------------------------

def r_hah(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    ht = gw(g, 340, 330, 0.35)
    hbw = gw(g, 270, 236, 0.75)          # head bar ink length
    bul = gw(g, 140, 120, 0.6)            # bulge of the ) curve
    xa = 0.0
    xr = xa + hbw - g.W
    ytop = ht - hh
    joined_right = c.form in ("medi", "fina")
    if joined_right:
        ramp = gw(g, 84, 56, 0.45)
        (g.pen(xr + ramp, jy).to(xr - 16, ytop, "l", "l", k=0.62).l(xa, ytop).end())
        c.rx = xr + ramp
        c.jr = JS(g) * 0.6
    else:
        g.line(xa, ytop, xr, ytop)
    if c.form in ("init", "medi"):
        (g.pen(xa, ytop).to(xa + bul, jy + (ytop - jy) * 0.42, (0.72, -1), "d", k=0.6)
            .v(xa - 6, jy, k=0.6).end())
        c.lx = xa - 6
        c.jl = JS(g)
        c.pt["below"] = (xa + bul * 0.45, -DGAP(g))
        c.bot = (xa + bul * 0.45, 0)
    else:
        bottom = DESC(g) - 20 - 0.1 * g.grow
        xl = xa - gw(g, 130, 100, 0.55)
        yk = jy + 24 + 0.2 * g.grow
        xm = xa + gw(g, 30, 20, 0.2)
        xe = xa + gw(g, 210, 170, 0.5)
        ye = bottom + gw(g, 100, 90, 0.3)
        (g.pen(xa, ytop).to(xa + bul * 0.25, yk, (0.72, -1), "l", k=0.62)
            .h(xl + hw, (yk + bottom) / 2, k=0.6)
            .v(xm, bottom + hh, k=0.6)
            .to(xe, ye, "r", (0.5, 1), k=0.62).end())
        c.pt["below"] = (xm - 6, yk - hh - DGAP(g) * 0.75)
        c.bot = (xm, bottom)
    c.pt["above"] = (xa + hbw * 0.42, ht + DGAP(g))
    c.top = (xa + hbw * 0.42, ht)


# ---------------------------------------------------------------------------
# seen, sad, tah
# ---------------------------------------------------------------------------

def r_seen(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    st = ST(g)
    sp = gw(g, 150, 116, 0.9)
    t1, t2, t3 = 2 * sp, sp, 0.0
    cup(g, t1, t2, st)
    cup(g, t2, t3, st)
    if c.form in ("init", "medi"):
        c.lx = sp / 2
        c.jl = sp / 2 + JS(g)
    else:
        bw = gw(g, 340, 280, 0.6)
        xl = t3 - (bw - g.W)
        bowl(g, t3, xl, st - hh, 0.55 * T(g) - hh, DESC(g))
    if c.rj:
        c.rx = 1.5 * sp
        c.jr = sp / 2 + JS(g)
    c.sbr = gw(g, 46, 0, 0.3)
    c.pt["above"] = (t2, st + DGAP(g))
    c.pt["below"] = (t2, -DGAP(g))
    c.top = (t2, st)
    c.bot = (t2, 0 if c.form in ("init", "medi") else DESC(g))


def r_sad(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    sw = gw(g, 330, 270, 1.4)
    sh = gw(g, 250, 230, 0.65)
    stt = ST(g) * 0.95
    x0 = hw + gw(g, 24, 16, 0.25)
    g.oval(x0, 0, x0 + sw, sh, w=LW)
    g.line(0, jy, x0 + sw * 0.5, jy)
    if c.form in ("init", "medi"):
        g.vstem(0, 0, stt)
        c.lx = 0
        c.jl = JS(g)
    else:
        bw = gw(g, 330, 260, 0.6)
        bowl(g, 0, -(bw - g.W), stt - hh, 0.55 * T(g) - hh, DESC(g))
    if c.rj:
        c.rx = x0 + sw * 0.5
        c.jr = sw * 0.5 + JS(g) * 0.5
    c.pt["above"] = (x0 + sw * 0.5, sh + DGAP(g))
    c.pt["below"] = (x0 + sw * 0.5, -DGAP(g)) if c.form in ("init", "medi") else (-gw(g, 130, 100, 0.3), DESC(g) - DGAP(g))
    c.top = (x0 + sw * 0.5, sh)
    c.bot = (x0 + sw * 0.5, 0)


def r_tah(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    tw = gw(g, 340, 290, 1.4)
    th = gw(g, 250, 230, 0.65)
    g.oval(0, 0, tw, th, w=LW)
    xs = tw * 0.32
    g.vstem(xs, th - g.H * LW, AH(g) - 20)
    if c.lj:
        c.lx = tw * 0.5
        c.jl = tw * 0.5 + JS(g) * 0.5
    if c.rj:
        c.rx = tw * 0.5
        c.jr = tw * 0.5 + JS(g) * 0.5
    c.pt["above"] = (xs + (tw - xs) * 0.52, th + DGAP(g))
    c.pt["below"] = (tw * 0.5, -DGAP(g))
    c.top = (xs + (tw - xs) * 0.52, th)
    c.bot = (tw * 0.5, 0)


# ---------------------------------------------------------------------------
# ain
# ---------------------------------------------------------------------------

def _ain_head(g, aw, ah, end):
    hw = g.hw
    hh = g.hh
    (g.pen(aw - hw, ah * 0.70).to(aw * 0.5, ah - hh, (-0.5, 1), "l", k=0.6)
        .h(hw, ah * 0.52, k=0.6).v(end[0], end[1], k=0.6).end())


def _ain_tri(g, mw, mh):
    jy, hh, hw = JY(g), g.hh, g.hw
    a = (hw, mh - hh)
    b = (mw - hw, mh - hh)
    v = (mw / 2, jy)
    g.line(a[0], a[1], b[0], b[1])
    g.line(a[0], a[1], v[0], v[1], DIAG)
    g.line(b[0], b[1], v[0], v[1], DIAG)
    return v


def r_ain(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    aw = gw(g, 256, 236, 0.9)
    ah = gw(g, 330, 310, 0.35)
    mw = gw(g, 224, 210, 1.5)
    mh = gw(g, 250, 232, 0.6)
    bottom = DESC(g) - 20 - 0.1 * g.grow
    if c.form == "init":
        _ain_head(g, aw, ah, (aw * 0.58, jy))
        c.lx = aw * 0.58
        c.jl = aw * 0.58 + JS(g) * 0.6
        cx, top = aw * 0.5, ah
    elif c.form == "medi":
        v = _ain_tri(g, mw, mh)
        c.lx = c.rx = v[0]
        c.jl = c.jr = mw / 2 + JS(g) * 0.5
        cx, top = mw / 2, mh
    elif c.form == "fina":
        v = _ain_tri(g, mw, mh)
        xl = v[0] - gw(g, 170, 140, 0.5)
        c_bowl(g, v, (-1, -0.7), xl + hw, v[0] - 4, v[0] + gw(g, 130, 110, 0.4), bottom,
               bottom + gw(g, 96, 86, 0.3))
        c.rx = v[0]
        c.jr = mw / 2 + JS(g) * 0.5
        cx, top = mw / 2, mh
    else:
        J = (aw * 0.58, jy + 28 + 0.2 * g.grow)
        _ain_head(g, aw, ah, J)
        xl = J[0] - gw(g, 190, 150, 0.5)
        c_bowl(g, J, (-1, -0.8), xl + hw, J[0] - 4, J[0] + gw(g, 140, 110, 0.4), bottom,
               bottom + gw(g, 96, 86, 0.3))
        cx, top = aw * 0.5, ah
    c.pt["above"] = (cx, top + DGAP(g))
    c.pt["below"] = (cx, -DGAP(g)) if c.form in ("init", "medi") else (cx, bottom - DGAP(g))
    c.top = (cx, top)
    c.bot = (cx, 0 if c.form in ("init", "medi") else bottom)


# ---------------------------------------------------------------------------
# feh, qaf
# ---------------------------------------------------------------------------

def _loop_dims(g):
    return gw(g, 240, 220, 1.6), gw(g, 250, 235, 0.75)


def r_feh(c: Ctx, qaf=False):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    fw, fh = _loop_dims(g)
    t = T(g)
    if c.form in ("init", "medi"):
        g.oval(0, 0, fw, fh, w=LW)
        lc = fw * 0.5
        c.lx = c.rx = lc
        c.jl = fw * 0.5 + JS(g)
        c.jr = fw * 0.5 + JS(g) * 0.6
        c.pt["below"] = (lc, -DGAP(g))
        c.bot = (lc, 0)
    elif not qaf:
        bw = gw(g, 600, 500, 1.4)
        x0 = bw - fw
        g.oval(x0, 0, bw, fh, w=LW)
        lc = x0 + fw * 0.5
        boat_tail(g, lc, hw, 0.64 * t, bw * 0.3)
        c.rx = lc
        c.jr = fw * 0.5 + JS(g) * 0.6
        c.pt["below"] = (bw * 0.42, -DGAP(g))
        c.bot = (bw * 0.42, 0)
    else:
        qw = gw(g, 380, 330, 0.7)
        xa = qw - hw
        x0 = xa - hw * LW
        g.oval(x0, 0, x0 + fw, fh, w=LW)
        bowl(g, xa, hw, fh * 0.5, 0.55 * t - hh, DESC(g), wr=LW)
        lc = x0 + fw * 0.5
        c.rx = lc
        c.jr = fw * 0.5 + JS(g) * 0.6
        c.pt["below"] = ((xa + hw) / 2, DESC(g) - DGAP(g))
        c.bot = ((xa + hw) / 2, DESC(g))
    c.pt["above"] = (lc, fh + DGAP(g))
    c.top = (lc, fh)


def r_qaf(c: Ctx):
    return r_feh(c, qaf=True)


# ---------------------------------------------------------------------------
# kaf, keheh, gaf, swash kaf
# ---------------------------------------------------------------------------

def _kaf_diag(g, xb, dx, top=None):
    jy, hh = JY(g), g.hh
    top = KH(g) if top is None else top
    xt = xb - dx
    g.line(xt, top - hh * DIAG, xb, jy, DIAG)
    return xt


def _gaf_bar(g, xb, xt, top=None):
    jy, hh = JY(g), g.hh
    top = KH(g) if top is None else top
    y0 = top - hh * DIAG
    ux, uy = xb - xt, jy - y0
    L = math.hypot(ux, uy)
    u = (ux / L, uy / L)            # down-right
    n = (-u[1], u[0])               # up-right
    off = g.W * 0.94 + 60 + 0.25 * g.grow
    ln = 0.36 * L
    p0 = (xt + n[0] * off - u[0] * 18, y0 + n[1] * off - u[1] * 18)
    p1 = (p0[0] + u[0] * ln, p0[1] + u[1] * ln)
    g.line(p0[0], p0[1], p1[0], p1[1], DIAG)
    return p0[1] + hh


def r_kafinit(c: Ctx, gaf=False):
    """Shared initial/medial kaf, keheh, gaf: a slanted stroke to the join."""
    g = c.g
    dx = gw(g, 220, 170, 0.5)
    xb = 0.0
    xt = _kaf_diag(g, xb, dx)
    ktop = KH(g)
    if gaf:
        ktop = _gaf_bar(g, xb, xt)
    c.lx = xb
    c.jl = dx + JS(g) * 0.5
    c.rx = xb
    c.pt["above"] = (xt + dx * 0.5 + (90 if gaf else 40), ktop + DGAP(g) * 0.6)
    c.pt["below"] = (xb - dx * 0.5, -DGAP(g))
    c.top = c.pt["above"][0], ktop
    c.bot = (xb - dx * 0.5, 0)


def r_keheh(c: Ctx, gaf=False):
    g = c.g
    if c.form in ("init", "medi"):
        return r_kafinit(c, gaf)
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    kw = gw(g, 520, 460, 0.9)
    xb = kw - hw
    dx = gw(g, 250, 200, 0.5)
    xt = _kaf_diag(g, xb, dx)
    ktop = KH(g)
    if gaf:
        ktop = _gaf_bar(g, xb, xt)
    boat_tail(g, xb, hw, 0.62 * t, kw * 0.32)
    c.rx = xb
    c.pt["above"] = (xt + dx * 0.5 + (90 if gaf else 40), ktop + DGAP(g) * 0.6)
    c.pt["below"] = (kw * 0.5, -DGAP(g))
    c.pt["ring"] = (kw * 0.62, -D(g) * 0.45)
    c.top = c.pt["above"][0], ktop
    c.bot = (kw * 0.5, 0)


def r_gaf(c: Ctx):
    return r_keheh(c, gaf=True)


def r_kaf(c: Ctx):
    """Arabic kaf: upright stem with a boat and the small inner hamza."""
    g = c.g
    if c.form in ("init", "medi"):
        return r_kafinit(c)
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    kw = gw(g, 500, 450, 0.9)
    xs = kw - hw
    g.vstem(xs, 0, KH(g))
    boat_tail(g, xs, hw, 0.62 * t, kw * 0.32)
    stamp(g, lambda s: mk_hamza(s, 0.52), (hw + xs) / 2 + 14, g.H + 30 + 0.2 * g.grow)
    c.rx = xs
    c.pt["above"] = (xs, KH(g) + DGAP(g) * 0.7)
    c.pt["below"] = (kw * 0.5, -DGAP(g))
    c.top = (xs, KH(g))
    c.bot = (kw * 0.5, 0)


def r_kafswash(c: Ctx):
    g = c.g
    if c.form in ("init", "medi"):
        return r_kafinit(c)
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    kw = gw(g, 660, 520, 1.1)
    xs = kw - hw
    at = gw(g, 420, 400, 0.3)
    bar = gw(g, 300, 220, 0.5)
    g.line(xs - bar + hw, at - hh, xs, at - hh)
    rr = hw * 0.35 + 16
    (g.pen(xs, at - hh).l(xs, jy + rr).v(xs - rr, jy, k=0.6)
        .l(hw + kw * 0.3, jy).h(hw, 0.62 * t - hh, k=0.6).end())
    c.rx = xs
    c.pt["above"] = (xs - bar * 0.5, at + DGAP(g))
    c.pt["below"] = (kw * 0.5, -DGAP(g))
    c.top = (xs - bar * 0.5, at)
    c.bot = (kw * 0.5, 0)


# ---------------------------------------------------------------------------
# lam
# ---------------------------------------------------------------------------

def r_lam(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    top = AH(g)
    if c.form in ("init", "medi"):
        xs = 0.0
        rc = hw + 26 + g.grow * 0.1
        g.pen(xs, top - hh).l(xs, jy + rc).v(xs - rc, jy, k=0.6).end()
        c.lx = xs - rc
        c.jl = JS(g)
        c.rx = xs
        c.sbr = gw(g, 54, 0, 0.3)
        c.top = (xs, top)
        c.bot = (xs, 0)
        c.pt["below"] = (xs - rc * 0.5, -DGAP(g))
    else:
        lw = gw(g, 380, 350, 0.8)
        xs = lw - hw
        bowl(g, xs, hw, top - hh, 0.55 * T(g) - hh, DESC(g))
        c.rx = xs
        c.sbr = gw(g, 54, 0, 0.3)
        c.top = (xs, top)
        c.bot = (lw / 2, DESC(g))
        c.pt["below"] = (lw / 2, DESC(g) - DGAP(g))
    c.pt["above"] = (xs, top + DGAP(g) * 0.7)


# ---------------------------------------------------------------------------
# meem
# ---------------------------------------------------------------------------

def r_meem(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    mw = gw(g, 236, 220, 1.6)
    mh = gw(g, 226, 210, 0.7)
    lc = mw * 0.5
    if c.form == "medi":
        g.oval(0, g.H - mh, mw, g.H, w=LW)
        top, bot = g.H, g.H - mh
    else:
        g.oval(0, 0, mw, mh, w=LW)
        top, bot = mh, 0
    if c.form in ("isol", "fina"):
        xt = hw * LW
        g.line(xt, mh * 0.45, xt, DESC(g) + hh)
        bot = DESC(g)
    if c.lj:
        c.lx = lc
        c.jl = mw * 0.5 + JS(g) * (1.0 if c.form == "init" else 0.6)
    if c.rj:
        c.rx = lc
        c.jr = mw * 0.5 + JS(g) * 0.6
    c.pt["above"] = (lc, top + DGAP(g))
    c.pt["below"] = (lc + (gw(g, 60, 50, 0.3) if c.form in ("isol", "fina") else 0),
                     (bot if c.form != "fina" and c.form != "isol" else 0) - DGAP(g))
    c.top = (lc, top)
    c.bot = (lc, bot)


# ---------------------------------------------------------------------------
# heh family
# ---------------------------------------------------------------------------

def _heh_init_shape(g):
    iw = gw(g, 290, 270, 1.6)
    ih = gw(g, 380, 350, 0.5)
    g.oval(0, 0, iw, ih, w=LW)
    g.line(iw * 0.36, ih - g.hh * LW, iw * 0.64, g.hh * LW, LW * DIAG)
    return iw, ih


def r_heh(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    if c.form == "isol":
        w_ = gw(g, 300, 280, 1.4)
        h_ = gw(g, 350, 330, 0.6)
        g.oval(0, 0, w_, h_)
        cx, top, bot = w_ / 2, h_, 0
    elif c.form == "fina":
        w_ = gw(g, 256, 240, 1.5)
        h_ = gw(g, 320, 300, 0.6)
        g.oval(0, 0, w_, h_, w=LW)
        c.rx = w_ * 0.55
        c.jr = w_ * 0.45 + JS(g) * 0.6
        cx, top, bot = w_ / 2, h_, 0
    elif c.form == "init":
        iw, ih = _heh_init_shape(g)
        c.lx = iw * 0.42
        c.jl = iw * 0.42 + JS(g)
        cx, top, bot = iw / 2, ih, 0
    else:
        uw = gw(g, 206, 196, 1.5)
        uh = gw(g, 250, 232, 0.6)
        lw2 = gw(g, 176, 166, 1.4)
        lh2 = gw(g, 196, 180, 0.6)
        g.oval(-uw / 2, 0, uw / 2, uh, w=LW)
        g.oval(-lw2 / 2, g.H - lh2, lw2 / 2, g.H, w=LW)
        c.lx = c.rx = 0
        c.jl = c.jr = uw / 2 + JS(g) * 0.5
        cx, top, bot = 0, uh, g.H - lh2
    c.pt["above"] = (cx, top + DGAP(g))
    c.pt["below"] = (cx, bot - DGAP(g))
    c.top = (cx, top)
    c.bot = (cx, bot)


def r_hehdo(c: Ctx):
    """Heh doachashmee (ھ): the two-eyed form in every position."""
    g = c.g
    iw, ih = _heh_init_shape(g)
    if c.lj:
        c.lx = iw * 0.42
        c.jl = iw * 0.42 + JS(g)
    if c.rj:
        c.rx = iw * 0.6
        c.jr = iw * 0.4 + JS(g) * 0.6
    c.pt["above"] = (iw / 2, ih + DGAP(g))
    c.pt["below"] = (iw / 2, -DGAP(g))
    c.top = (iw / 2, ih)
    c.bot = (iw / 2, 0)


def r_hehgoal(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    t = T(g)
    if c.form in ("init", "medi"):
        hk = 0.98 * t
        r = gw(g, 64, 54, 0.4)
        (g.pen(0, jy).l(0, hk - hh - r).v(r, hk - hh, k=0.6)
            .h(2 * r, hk - hh - r * 1.25, k=0.6).end())
        c.lx = c.rx = 0
        c.sbr = gw(g, 44, 0, 0.3)
        c.pt["above"] = (r, hk + DGAP(g))
        c.pt["below"] = (0, -DGAP(g))
        c.top = (r, hk)
        c.bot = (0, 0)
        return
    w_ = gw(g, 270, 250, 0.9)
    h_ = gw(g, 330, 310, 0.4)
    (g.pen(hw, h_ * 0.72).to(w_ * 0.48, h_ - hh, (0.45, 1), "r", k=0.6)
        .h(w_ - hw, h_ * 0.45, k=0.6).v(w_ * 0.48, jy, k=0.6)
        .to(hw + 4, jy + gw(g, 62, 52, 0.35), "l", (-0.45, 1), k=0.6).end())
    if c.form == "fina":
        c.rx = w_ * 0.5
        c.jr = w_ * 0.5 + JS(g) * 0.5
    c.pt["above"] = (w_ * 0.5, h_ + DGAP(g))
    c.pt["below"] = (w_ * 0.5, -DGAP(g))
    c.top = (w_ * 0.5, h_)
    c.bot = (w_ * 0.5, 0)


# ---------------------------------------------------------------------------
# waw
# ---------------------------------------------------------------------------

def r_waw(c: Ctx):
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    ww = gw(g, 236, 220, 1.6)
    wh = gw(g, 250, 235, 0.75)
    x0 = gw(g, 130, 104, 0.35)
    bottom = DESC(g) * 0.92
    g.oval(x0, 0, x0 + ww, wh, w=LW)
    # tail: leaves the loop along the join line, then sweeps down and away to
    # the left in a long curl (distinguishes waw from meem's straight drop)
    xt = hw * 0.6
    (g.pen(x0 + ww * 0.55, jy).l(x0 + ww * 0.42, jy)
        .to(x0 + ww * 0.08, (jy + bottom) * 0.42, "l", (-0.25, -1), k=0.6)
        .to(xt, bottom + hh, (-0.25, -1), (-1, -0.12), k=0.6).end())
    if c.form == "fina":
        c.rx = x0 + ww * 0.5
        c.jr = ww * 0.5 + JS(g) * 0.6
    c.sbl = gw(g, 30, 0, 0.2)
    c.pt["above"] = (x0 + ww * 0.5, wh + DGAP(g))
    c.pt["below"] = (x0 + ww * 0.62, -DGAP(g))
    c.pt["ring"] = (hw + 34, bottom * 0.5)
    c.pt["bar"] = (x0 * 0.5, bottom * 0.45)
    c.pt["hh"] = (x0 + ww + 60, wh * 0.85)
    c.top = (x0 + ww * 0.5, wh)
    c.bot = (x0 * 0.6, bottom)


# ---------------------------------------------------------------------------
# hamza, lam-alef
# ---------------------------------------------------------------------------

def r_hamza(c: Ctx):
    g = c.g
    stamp(g, lambda s: mk_hamza(s, 1.0, 0.94), 0, 0, True)
    c.sbl = c.sbr = gw(g, 40, 0, 0.3)
    c.top = (0, 0.95 * T(g))


def r_highhamza(c: Ctx):
    g = c.g
    stamp(g, lambda s: mk_hamza(s, 0.62), 0, T(g) * 0.95, True)
    c.sbl = c.sbr = gw(g, 30, 0, 0.3)


def lamalef(c: Ctx):
    """Lam-alef ligature body.  Points 'lam' and 'alef' for decorations."""
    g = c.g
    jy, hh, hw = JY(g), g.hh, g.hw
    top = AH(g)
    xs = gw(g, 340, 330, 0.8) - hw
    xj = xs - gw(g, 150, 120, 0.55)
    xa = xj - gw(g, 196, 150, 0.4)
    rc = hw + 24 + g.grow * 0.1
    g.pen(xs, top - hh).l(xs, jy + rc).v(xs - rc, jy, k=0.6).l(xj, jy).end()
    g.line(xj, jy, xa, top - hh * DIAG, DIAG)
    if c.form == "fina":
        c.rx = xs
        c.jr = JS(g)
    c.sbr = gw(g, 54, 0, 0.3)
    c.sbl = gw(g, 46, 0, 0.3)
    c.pt["lam_above"] = (xs, top + DGAP(g) * 0.7)
    c.pt["alef_above"] = (xa - 6, top + DGAP(g) * 0.7)
    c.pt["alef_below"] = (xj, -DGAP(g) * 0.7)
    c.pt["above"] = c.pt["lam_above"]
    c.pt["below"] = c.pt["alef_below"]
    c.top = (xs, top)
    c.bot = ((xs + xj) / 2, 0)


RASM = {
    "alef": (r_alef, "R"),
    "beh": (r_beh, "D"),
    "noon": (r_noon, "D"),
    "yeh": (r_yeh, "D"),
    "yehR": (r_yeh, "R"),
    "yehbarree": (r_yehbarree, "R"),
    "reh": (r_reh, "R"),
    "dal": (r_dal, "R"),
    "hah": (r_hah, "D"),
    "seen": (r_seen, "D"),
    "sad": (r_sad, "D"),
    "tah": (r_tah, "D"),
    "ain": (r_ain, "D"),
    "feh": (r_feh, "D"),
    "qaf": (r_qaf, "D"),
    "kaf": (r_kaf, "D"),
    "keheh": (r_keheh, "D"),
    "gaf": (r_gaf, "D"),
    "kafswash": (r_kafswash, "D"),
    "lam": (r_lam, "D"),
    "meem": (r_meem, "D"),
    "heh": (r_heh, "D"),
    "hehR": (r_heh, "R"),
    "hehdo": (r_hehdo, "D"),
    "hehgoal": (r_hehgoal, "D"),
    "hehgoalR": (r_hehgoal, "R"),
    "waw": (r_waw, "D" if False else "R"),
    "hamza": (r_hamza, "U"),
    "highhamza": (r_highhamza, "U"),
}
