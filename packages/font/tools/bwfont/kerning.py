"""Automatic class kerning from outline profiles.

Glyphs are grouped by their base glyph (composites share their base's groups).
For every pair of group representatives we measure the horizontal gap
between the two outlines on each scanline where both have ink, take a
power mean that emphasises the closest approach, and compare it with the
gap of a neutral pair (n|n, H|H).  Only *tightening* kerns are produced
(plus collision fixes), which is what neo-grotesk spacing needs: T, V, W, Y,
A, L, P, F, r, f, quotes and punctuation against everything else.
"""
from __future__ import annotations

import unicodedata

from .spacing import polygons, profile

Y0, Y1, STEP = -230, 990, 20
YS = [Y0 + STEP * (i + 0.5) for i in range(int((Y1 - Y0) / STEP))]
KERN_CATS = ("Lu", "Ll", "Lt", "Nd", "Po", "Pi", "Pf", "Ps", "Pe", "Pd")


class Prof:
    __slots__ = ("name", "left", "right", "adv", "zone", "script", "l_arr", "r_arr")


def _script(o):
    for u in o.unicodes:
        try:
            nm = unicodedata.name(chr(u))
        except ValueError:
            continue
        for s in ("LATIN", "GREEK", "CYRILLIC"):
            if nm.startswith(s):
                return s
        return "COMMON"
    return None


def _cat(o):
    for u in o.unicodes:
        if 0x1D00 <= u <= 0x1DBF:      # phonetic extensions (mostly superscripts)
            return "Lm"
        return unicodedata.category(chr(u))
    return None


def _base_of(outs, name, depth=0):
    o = outs[name]
    if o.components and depth < 6:
        return _base_of(outs, o.components[0][0], depth + 1)
    return name


def _profile(o, params):
    p = Prof()
    p.name = o.name
    p.adv = o.advance
    polys = polygons(o.contours)
    pr = profile(polys, YS)
    p.left = [None if q is None else q[0] for q in pr]
    p.right = [None if q is None else q[1] for q in pr]
    top = max((y for y, q in zip(YS, pr) if q is not None), default=0)
    p.zone = "uc" if top > params.xh + 80 else "lc"
    return p


import numpy as np

_YA = np.array(YS)
_DY = np.abs(_YA[:, None] - _YA[None, :])
_NEAR = _DY <= 170
VPEN = 0.9


def _arr(v):
    return np.array([np.nan if x is None else x for x in v], dtype=float)


def _vg_batch(L, Rs, pw=-8.0):
    """Visual gaps between L and each R in Rs (2D proximity, power mean).
    Returns (vg array, min-gap array) — NaN where no overlap."""
    lr = L.adv - L.r_arr                       # (n,)  distance from L ink to its advance
    rl = np.stack([R.l_arr for R in Rs])       # (m, n)
    # hgap[m, i, j] = lr[i] + rl[m, j] + VPEN*|yi - yj|
    h = lr[None, :, None] + rl[:, None, :] + VPEN * _DY[None, :, :]
    h = np.where(_NEAR[None, :, :], h, np.nan)
    import warnings
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        row = np.nanmin(h, axis=2)             # for each L row, closest R ink
        col = np.nanmin(h, axis=1)             # for each R row, closest L ink
        allg = np.concatenate([row, col], axis=1)
        valid = ~np.isnan(allg)
        cnt = valid.sum(axis=1)
        g = np.where(valid, np.maximum(allg, 4.0), 1.0)
        m = np.where(valid, g ** pw, 0.0).sum(axis=1) / np.maximum(cnt, 1)
        vg = np.where(cnt >= 3, m ** (1.0 / pw), np.nan)
        # direct (same row) minimum gap for collision checks
        direct = lr[None, :] + rl
        mn = np.nanmin(np.where(np.isnan(direct), np.inf, direct), axis=1)
    return vg, mn


BANDS = [-230, -60, 0, 135, 270, 405, 540, 640, 740, 990]
_BAND_IDX = [np.where((_YA >= lo) & (_YA < hi))[0] for lo, hi in zip(BANDS, BANDS[1:])]


def _bandsig(v, clip=140.0, empty=175.0):
    out = []
    for idx in _BAND_IDX:
        w = v[idx]
        w = w[~np.isnan(w)]
        out.append(float(np.minimum(w, clip).mean()) if len(w) else empty)
    return np.array(out)


def _cluster(bases, sig, zone, script, tol=36.0):
    """Greedy clustering of glyph sides by banded depth signature."""
    reps = []
    out = {}
    for b in bases:
        v = sig[b]
        hit = None
        for r, rv in reps:
            if zone[r] == zone[b] and np.abs(v - rv).max() < tol:
                hit = r
                break
        if hit is None:
            reps.append((b, v))
            out[b] = b
        else:
            out[b] = hit
    return out


def _core(o):
    for u in o.unicodes:
        return (0x20 <= u < 0x250) or (0x370 <= u < 0x530) or (0x1E00 <= u < 0x1F00) or (0x2000 <= u < 0x2070)
    return False


def make_kerning(family, params, outs, state=None):
    """Return (kerning dict, groups dict, state).  `state` (clusters + pair
    list) is computed on the first (Regular) master and replayed for the
    others so every master shares groups and pairs."""
    if family != "sans":
        return {}, {}, None
    members = {}
    for name, o in outs.items():
        if o.kind == "mark" or not o.unicodes:
            continue
        if _cat(o) not in KERN_CATS or not _core(o):
            continue
        base = _base_of(outs, name)
        if outs[base].kind == "mark" or not outs[base].contours:
            continue
        members.setdefault(base, []).append(name)
    bases = sorted(members)
    profs = {b: _profile(outs[b], params) for b in bases}
    scripts = {b: _script(outs[b]) for b in bases}
    for pr in profs.values():
        pr.l_arr = _arr(pr.left)
        pr.r_arr = _arr(pr.right)
    zone = {b: profs[b].zone for b in bases}
    if state is None:
        # signature = depth relative to the side's extreme + the sidebearing itself
        def sig1(b):
            v = profs[b].adv - profs[b].r_arr
            return _bandsig(v - np.nanmin(v)) if np.isfinite(np.nanmin(v)) else np.full(9, 175.0)
        def sig2(b):
            v = profs[b].l_arr
            return _bandsig(v - np.nanmin(v)) if np.isfinite(np.nanmin(v)) else np.full(9, 175.0)
        s1 = {b: np.append(sig1(b), np.nanmin(profs[b].adv - profs[b].r_arr) * 1.6) for b in bases}
        s2 = {b: np.append(sig2(b), np.nanmin(profs[b].l_arr) * 1.6) for b in bases}
        c1 = _cluster(bases, s1, zone, scripts)
        c2 = _cluster(bases, s2, zone, scripts)
        state = {"c1": c1, "c2": c2, "pairs": None}
    c1, c2 = state["c1"], state["c2"]
    groups = {}
    for side, cmap in (("kern1", c1), ("kern2", c2)):
        for b in bases:
            rep = cmap.get(b)
            if rep is None:
                continue
            names = members[b] + ([b] if outs[b].unicodes else [])
            groups.setdefault(f"public.{side}.{rep}", set()).update(names)
    groups = {k: sorted(v) for k, v in groups.items()}
    reps1 = sorted(set(c1.values()))
    reps2 = sorted(set(c2.values()))

    def ref_of(a, b):
        if a in profs and b in profs:
            v, _ = _vg_batch(profs[a], [profs[b]])
            return float(v[0])
        return None
    ref_lc = ref_of("n", "n") or 120.0
    ref_uc = ref_of("H", "H") or ref_lc * 1.1

    def kval(L, R, vg, mn):
        if np.isnan(vg):
            return 0
        if L.zone == "uc" and R.zone == "uc":
            ref = ref_uc
        elif L.zone == "lc" and R.zone == "lc":
            ref = ref_lc
        else:
            ref = (ref_lc + ref_uc) / 2
        k = 0.7 * (ref - vg)
        floor = 0.4 * ref
        if k < 0:
            if np.isfinite(mn):
                k = max(k, -(mn - floor))
            k = max(min(k, 0), -0.72 * ref)
        elif np.isfinite(mn) and mn < 0.25 * ref:
            k = 0.25 * ref - mn            # collision fix only
        else:
            k = 0
        return 2 * round(k / 2)

    kern = {}
    want = None
    if state["pairs"] is not None:
        want = {}
        for a, b in state["pairs"]:
            want.setdefault(a, []).append(b)
    new_pairs = []
    for a in reps1:
        L = profs[a]
        if want is not None:
            rights = want.get(a, [])
        else:
            rights = list(reps2)
        if not rights:
            continue
        vgs, mns = _vg_batch(L, [profs[b] for b in rights])
        for b, vg, mn in zip(rights, vgs, mns):
            k = kval(L, profs[b], vg, mn)
            if want is not None or abs(k) >= 24:
                kern[(f"public.kern1.{a}", f"public.kern2.{b}")] = k
                new_pairs.append((a, b))
    if state["pairs"] is None:
        state["pairs"] = new_pairs
    return kern, groups, state
