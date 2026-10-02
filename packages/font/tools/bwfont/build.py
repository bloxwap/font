"""Generate UFO masters + designspace for each Bloxwap family."""
from __future__ import annotations

import importlib
import math
import pkgutil
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import ufoLib2
from fontTools.designspaceLib import (AxisDescriptor, AxisLabelDescriptor, DesignSpaceDocument,
                                      DiscreteAxisDescriptor, InstanceDescriptor, SourceDescriptor,
                                      VariableFontDescriptor)

from . import composites as comp
from .families import FAMILIES, Family
from .geometry import Contour, Plan
from .skeleton import GLYPHS, G, Params, outline, params_for, skew_point
from .spacing import autospace, polygons, bbox

VERSION = "1.000"

WEIGHTS = [
    (100, "Thin", 22),
    (200, "ExtraLight", 38),
    (300, "Light", 58),
    (400, "Regular", 84),
    (500, "Medium", 104),
    (600, "SemiBold", 124),
    (700, "Bold", 144),
    (800, "ExtraBold", 162),
    (900, "Black", 180),
]
MASTERS = [("Thin", 22), ("Regular", 84), ("Black", 180)]
ITALIC_ANGLE = 9.0

FAMILY_NAMES = {"sans": "Bloxwap Sans", "mono": "Bloxwap Mono", "pixel": "Bloxwap Pixel"}


def load_glyph_modules():
    import bwfont.glyphs as gl
    for m in pkgutil.iter_modules(gl.__path__):
        importlib.import_module(f"bwfont.glyphs.{m.name}")


@dataclass
class GlyphOut:
    name: str
    unicodes: list
    contours: list = field(default_factory=list)
    components: list = field(default_factory=list)   # (name, dx, dy)
    anchors: dict = field(default_factory=dict)
    advance: float = 0
    kind: str = "base"
    ink: tuple = None  # (xmin, ymin, xmax, ymax) after positioning


def _shift_contours(cs, dx):
    return [c.transform(lambda p: (p[0] + dx, p[1])) for c in cs]


def _default_anchors(g: G, out: GlyphOut, params: Params, zone: str):
    if out.ink is None:
        return
    xmin, ymin, xmax, ymax = out.ink
    cx = (xmin + xmax) / 2
    a = out.anchors
    if ymax <= params.xh + 60:
        ty = params.xh
    elif ymax <= params.cap + 30:
        ty = params.cap
    else:
        ty = params.asc if zone == "lc" or ymax > params.cap + 30 else params.cap
        if zone == "uc":
            ty = params.cap
    a.setdefault("top", (cx, ty))
    a.setdefault("bottom", (cx, 0 if ymin > -60 else ymin))
    a.setdefault("ogonek", (xmax - params.W * 0.5, 0))
    a.setdefault("horn", (xmax - params.W * 0.45, ty * 0.92))
    a.setdefault("center", (cx, (min(ymax, ty) + max(ymin, 0)) / 2))
    a.setdefault("caron", (xmax + 46 + params.grow * 0.2, (params.asc if ty > params.cap else params.cap) + 10))
    a.setdefault("dotright", (xmax + 70 + params.grow * 0.3, params.xh / 2 + (60 if ty > params.xh else 0)))


def _fam(family) -> Family:
    return family if isinstance(family, Family) else FAMILIES[family]


def make_master(family, stem: float, slant: float, plan: Plan, spacing_ref: dict | None):
    """Build all glyphs for one master.  Returns (params, dict name -> GlyphOut)."""
    fam = _fam(family)
    params = params_for(fam.style, stem, slant)
    params.family_id = fam.id
    outs: dict[str, GlyphOut] = {}
    for name, gd in GLYPHS.items():
        packs = gd.pack if isinstance(gd.pack, tuple) else (gd.pack,)
        if fam.style not in gd.families or not set(packs) & set(fam.packs):
            continue
        g = G(params, name)
        gd.func(g)
        cs = outline(g, plan, name)
        o = GlyphOut(name, list(gd.unicodes), kind=gd.kind)
        anchors = {k: skew_point(params, v) for k, v in g.anchors.items()}
        o.components = [(c[0], c[1], c[2]) for c in g.components]
        if g.fixed:
            # positioned as drawn, fixed advance, no measuring (CJK, Hangul, joined Arabic)
            o.contours = cs
            o.anchors = anchors
            o.advance = round(g.advance if g.advance is not None else 1000)
            o.dx = 0
            outs[name] = o
            continue
        polys = polygons(cs) if cs else []
        bb = bbox(polys) if polys else None
        if gd.kind == "mark":
            o.contours = cs
            o.anchors = anchors
            o.advance = 0
            o.ink = bb
            outs[name] = o
            continue
        zone = g.zone or gd.zone
        if spacing_ref is not None and name in spacing_ref:
            dx, adv = spacing_ref[name]
        elif g.advance is not None and bb is None:
            dx, adv = 0, g.advance
        elif bb is None:
            dx, adv = 0, (g.advance if g.advance is not None else 260)
        else:
            sp = autospace(cs, zone, params.W, params.xh, params.cap, scale=g.sb.get("scale", 1.0))
            lsb, rsb, xmin, xmax = sp
            if g.lsb is not None:
                lsb = g.lsb
            if g.rsb is not None:
                rsb = g.rsb
            lsb += g.sb.get("l", 0)
            rsb += g.sb.get("r", 0)
            if params.mono and g.advance is None:
                adv = params.mono_adv
                ink = xmax - xmin
                # balance remaining space using measured optical sidebearings
                extra = adv - (lsb + ink + rsb)
                dx = lsb + extra / 2 - xmin
            elif g.advance is not None:
                adv = g.advance
                ink = xmax - xmin
                extra = adv - (lsb + ink + rsb)
                dx = lsb + extra / 2 - xmin
            else:
                dx = lsb - xmin
                adv = lsb + (xmax - xmin) + rsb
        o.contours = _shift_contours(cs, dx)
        o.anchors = {k: (v[0] + dx, v[1]) for k, v in anchors.items()}
        o.advance = round(adv)
        if bb is not None:
            o.ink = (bb[0] + dx, bb[1], bb[2] + dx, bb[3])
        o.dx = dx
        _default_anchors(g, o, params, zone)
        outs[name] = o
    return params, outs


def add_composites(params: Params, outs: dict, family: str):
    """Create alias / accented glyphs from recipes."""
    have = set(outs)
    cmap = {}
    for o in outs.values():
        for u in o.unicodes:
            cmap[u] = o.name
            comp.register_cmap(u, o.name)

    def is_case(name):
        o = outs.get(name)
        if o is None or o.ink is None:
            return False
        return o.anchors.get("top", (0, 0))[1] > params.xh + 60

    recipes = {}
    pending = [cp for cp in comp.target_codepoints() if cp not in cmap]
    progress = True
    while progress:
        progress = False
        rest = []
        for cp in pending:
            r = comp.recipe_for(cp, have, is_case)
            if r is None:
                rest.append(cp)
                continue
            name = comp.glyph_name(cp)
            if name in have:
                name = f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"
            o = _compose(name, cp, r, outs, params)
            if o is None:
                rest.append(cp)
                continue
            outs[name] = o
            have.add(name)
            cmap[cp] = name
            comp.register_cmap(cp, name)
            recipes[name] = r
            progress = True
        pending = rest
    # small-cap versions of composed lowercase letters (base has a .sc form)
    for name, r in list(recipes.items()):
        base = r[0][0]
        sc_base = base + ".sc"
        if base in ("dotlessi", "dotlessj"):
            sc_base = base[-1] + ".sc"
        if sc_base not in have or name + ".sc" in have or r[0][1] is not None:
            continue
        r2 = [(sc_base, None)] + [(m.replace(".case", ""), a) for m, a in r[1:]]
        if not all(m in have for m, _ in r2):
            continue
        o = _compose(name + ".sc", None, r2, outs, params)
        if o is not None:
            o.unicodes = []
            outs[name + ".sc"] = o
            have.add(name + ".sc")
    return cmap


def _compose(name, cp, recipe, outs, params):
    base_name = recipe[0][0]
    o = GlyphOut(name, [cp] if cp is not None else [])
    if recipe[0][1] == "seq":
        if params.mono:
            return None
        x = 0
        prev = None
        for cn, kind in recipe:
            c = outs[cn]
            if kind == "seqmark":
                pb, px = prev
                if "top" not in pb.anchors or "_top" not in c.anchors:
                    return None
                bx, by = pb.anchors["top"]
                mx, my = c.anchors["_top"]
                o.components.append((cn, px + bx - mx, by - my))
                continue
            o.components.append((cn, x, 0))
            prev = (c, x)
            x += c.advance
        o.advance = x
        return o
    if recipe[0][1] == "prefix":
        # e.g. ŉ: apostrophe then n
        a, b = outs[recipe[0][0]], outs[recipe[1][0]]
        o.components = [(a.name, 0, 0), (b.name, a.advance - 30, 0)]
        o.advance = a.advance - 30 + b.advance
        return o
    base = outs[base_name]
    if base.kind == "mark":
        return None
    o.components.append((base_name, 0, 0))
    o.advance = base.advance
    o.ink = base.ink
    anchors = dict(base.anchors)
    lead = 0
    for mname, attach in recipe[1:]:
        m = outs[mname]
        if attach == "tonos_left":
            # Greek capital with accents: shift base right, accent sits to the
            # left at cap height (lowercase-size mark, top aligned to cap)
            mx = m.ink[2] - m.ink[0] if m.ink else 80
            lead = mx + 34 + params.grow * 0.3
            o.components = [(base_name, lead, 0)] + o.components[1:]
            o.advance = base.advance + lead
            tx = (m.ink[0] if m.ink else 0)
            ty = (m.ink[3] if m.ink else params.xh + 200)
            o.components.append((mname, -tx + 24, params.cap - ty + 6))
            continue
        if attach == "dotright":
            ax, ay = anchors["dotright"]
            pc = outs[mname]
            ink = pc.ink
            cxm = (ink[0] + ink[2]) / 2
            cym = (ink[1] + ink[3]) / 2
            o.components.append((mname, ax - cxm, ay - cym))
            o.advance = max(o.advance, round(ax - cxm + pc.advance - 20))
            continue
        key = "_" + attach
        if attach not in anchors or key not in m.anchors:
            return None
        bx, by = anchors[attach]
        mx, my = m.anchors[key]
        dx, dy = bx - mx, by - my
        o.components.append((mname, dx, dy))
        if attach == "caron":
            right = dx + (m.ink[2] if m.ink else 0)
            o.advance = max(o.advance, round(right + 30))
        # update stacking anchors
        for an in ("top", "bottom"):
            if attach == an and an in m.anchors:
                anchors[an] = (m.anchors[an][0] + dx, m.anchors[an][1] + dy)
    o.anchors = {k: v for k, v in anchors.items() if k in ("top", "bottom")}
    return o


# ---------------------------------------------------------------------------
# UFO writing
# ---------------------------------------------------------------------------

def _round_pen_draw(contours, pen):
    for c in contours:
        c.draw(pen)


def write_ufo(path: Path, family, style: str, weight: int, italic: bool, params: Params,
              outs: dict, order: list, features: str, kerning: dict, groups: dict):
    f = ufoLib2.Font()
    info = f.info
    famobj = _fam(family) if (isinstance(family, Family) or family in FAMILIES) else None
    fam = famobj.name if famobj else FAMILY_NAMES[family]
    m = famobj.metrics if famobj else dict(asc=960, desc=-240, gap=0, win_asc=1050, win_desc=330)
    family = famobj.style if famobj else family
    info.familyName = fam
    info.styleName = style
    info.versionMajor, info.versionMinor = 1, 0
    info.unitsPerEm = 1000
    info.ascender = m["asc"]
    info.descender = m["desc"]
    info.xHeight = params.xh
    info.capHeight = params.cap
    info.italicAngle = -params.slant if italic else 0
    info.copyright = "Copyright 2026 Bloxwap, Inc."
    info.trademark = "Bloxwap is a trademark of Bloxwap, Inc."
    info.openTypeNameDesigner = "Bloxwap, Inc."
    info.openTypeNameManufacturer = "Bloxwap, Inc."
    info.openTypeNameManufacturerURL = "https://bloxwap.com"
    info.openTypeNameDesignerURL = "https://bloxwap.github.io/font/"
    info.openTypeNameLicense = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                                "This license is available with a FAQ at: https://openfontlicense.org")
    info.openTypeNameLicenseURL = "https://openfontlicense.org"
    info.openTypeOS2VendorID = "BLXW"
    info.openTypeOS2WeightClass = weight
    info.openTypeOS2TypoAscender = m["asc"]
    info.openTypeOS2TypoDescender = m["desc"]
    info.openTypeOS2TypoLineGap = m["gap"]
    info.openTypeOS2WinAscent = m["win_asc"]
    info.openTypeOS2WinDescent = m["win_desc"]
    info.openTypeHheaAscender = m["asc"]
    info.openTypeHheaDescender = m["desc"]
    info.openTypeHheaLineGap = m["gap"]
    info.openTypeOS2Selection = [7]  # USE_TYPO_METRICS
    info.postscriptUnderlinePosition = -120
    info.postscriptUnderlineThickness = round(params.H * 0.8)
    info.openTypeOS2StrikeoutPosition = round(params.xh / 2 + params.H * 0.4)
    info.openTypeOS2StrikeoutSize = round(params.H * 0.8)
    info.postscriptIsFixedPitch = family in ("mono", "pixel")
    info.openTypeOS2Panose = [2, 11, 5 if family == "sans" else 9, 2, 2, 2, 4, 2, 2, 4] if family == "sans" else [2, 11, 5, 9, 2, 2, 2, 2, 2, 4]
    for name in order:
        o = outs[name]
        gl = f.newGlyph(name)
        gl.unicodes = list(o.unicodes)
        gl.width = o.advance
        pen = gl.getPen()
        _round_pen_draw(o.contours, pen)
        for cn, dx, dy in o.components:
            pen.addComponent(cn, (1, 0, 0, 1, round(dx), round(dy)))
        for an, (x, y) in sorted(o.anchors.items()):
            gl.appendAnchor({"name": an, "x": round(x), "y": round(y)})
    f.lib["public.glyphOrder"] = order
    cats = {n: "mark" for n in order if outs[n].kind == "mark"}
    for n in order:
        if n not in cats and outs[n].unicodes:
            pass
    f.lib["public.openTypeCategories"] = {**{n: "base" for n in order if outs[n].kind != "mark"}, **cats}
    f.features.text = features
    for k, v in kerning.items():
        f.kerning[k] = v
    for k, v in groups.items():
        f.groups[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        import shutil
        shutil.rmtree(path)
    f.save(path)
