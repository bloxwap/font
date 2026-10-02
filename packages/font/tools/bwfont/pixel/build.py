"""Assemble Bloxwap Pixel masters, UFOs and the designspace."""
from __future__ import annotations

import math
import shutil
import time
from pathlib import Path

import ufoLib2
from fontTools.designspaceLib import (AxisDescriptor, AxisLabelDescriptor, DesignSpaceDocument,
                                      DiscreteAxisDescriptor, InstanceDescriptor, SourceDescriptor,
                                      VariableFontDescriptor, RangeAxisSubsetDescriptor,
                                      ValueAxisSubsetDescriptor)

from .. import build as B
from ..build import GlyphOut
from ..features import make_features, glyph_order
from . import art
from .art import ADV, CELL
from .compose import compose_all
from .geom import pixel, italic_dx, ITALIC_ANGLE

FAMILY = "pixel"
FAM = B.FAMILY_NAMES[FAMILY]          # "Bloxwap Pixel"
PS = FAM.replace(" ", "")              # "BloxwapPixel"

XH, CAP, ASC, DESC = 500, 700, 700, -200

# pixel size (fraction of the 100-unit cell) at the weight masters
WGHT_MASTERS = [(100, "Thin", 0.42), (400, "Regular", 0.78), (900, "Black", 1.04)]
ROND_MASTERS = [0, 50, 100]
ROND_DEFAULT = 50
ROND_LABELS = [(0, "Square"), (50, "Rounded"), (100, "Round")]

_registered = False


def register_all():
    global _registered
    if _registered:
        return
    from . import latin, marks, latin_ext, punct, greek, cyrillic, symbols, boxes, extra
    latin.register()
    marks.register()
    latin_ext.register()
    punct.register()
    greek.register()
    cyrillic.register()
    symbols.register()
    boxes.register()
    extra.register()
    marks.register_spacing()
    _registered = True


# ---------------------------------------------------------------------------
# anchors
# ---------------------------------------------------------------------------

def default_anchors(d: art.PixelDef):
    a = {}
    if not d.pix or d.kind == "mark":
        return a
    rows = [r for _, r in d.pix]
    top, low = max(rows), min(rows)
    body = [p for p in d.pix if p[1] >= 0] or list(d.pix)
    brows = [r for _, r in body]
    a["top"] = (300, (top + 1) * CELL)
    a["bottom"] = (300, min(0, low * CELL))
    row0 = [x for x, r in d.pix if r == min(brows)]
    a["ogonek"] = (max(row0), 0)
    a["horn"] = (500, (top + 1) * CELL)
    mid = (max(brows) + min(brows)) // 2
    a["center"] = (300, mid * CELL + CELL // 2)
    return a


# ---------------------------------------------------------------------------
# masters
# ---------------------------------------------------------------------------

def make_master(size: float, rond: int, italic: bool):
    s = size * CELL
    rho = rond / 100
    outs: dict[str, GlyphOut] = {}
    later = []
    for name in art.ORDER:
        d = art.REG[name]
        cs = []
        for x, r in sorted(d.pix, key=lambda p: (-p[1], p[0])):
            dx = italic_dx(r) if (italic and d.shear) else 0
            cs.append(pixel(x + dx, r * CELL + CELL // 2, s, rho))
        if d.shapes is not None:
            cs.extend(d.shapes(s, rho))
        o = GlyphOut(name, list(d.unicodes), contours=cs, components=list(d.comps),
                     kind="mark" if d.kind == "mark" else "base",
                     advance=0 if d.kind == "mark" else d.advance)
        if d.pix:
            xs = [x for x, _ in d.pix]
            rs = [r for _, r in d.pix]
            o.ink = (min(xs) - s / 2, min(rs) * CELL + 50 - s / 2, max(xs) + s / 2, max(rs) * CELL + 50 + s / 2)
            o.minx, o.minrow = min(xs), min(rs)
        else:
            o.ink = None
            o.minx, o.minrow = 300, 0
        anchors = {**default_anchors(d), **d.anchors}
        if italic and d.shear:
            # anchors follow the row shear, so GPOS mark offsets of whole
            # rows land on the right italic step
            anchors = {k: (x + italic_dx(math.floor(y / CELL)), y) for k, (x, y) in anchors.items()}
        o.anchors = anchors
        outs[name] = o
        if d.comps and not d.pix:
            later.append(name)
    # component-only glyphs inherit ink/anchors from their first component
    for name in later:
        o = outs[name]
        src = outs[o.components[0][0]]
        dx, dy = o.components[0][1], o.components[0][2]
        if src.ink:
            o.ink = (src.ink[0] + dx, src.ink[1] + dy, src.ink[2] + dx, src.ink[3] + dy)
        o.minx, o.minrow = src.minx + dx, src.minrow + round(dy / CELL)
        if src.kind != "mark":
            o.anchors = {k: (v[0] + dx, v[1] + dy) for k, v in src.anchors.items() if not k.startswith("_")}
        else:
            o.anchors = {}
    cmap, skipped = compose_all(outs, XH, italic)
    return outs, cmap, skipped


# ---------------------------------------------------------------------------
# UFO
# ---------------------------------------------------------------------------

def write_ufo(path: Path, style: str, weight: int, italic: bool, size: float,
              outs: dict, order: list, features: str):
    """Like build.write_ufo, with pixel-specific metrics (stacked accents over
    capitals reach row 11, underline/strikeout are one pixel thick)."""
    f = ufoLib2.Font()
    i = f.info
    i.familyName = FAM
    i.styleName = style
    i.styleMapFamilyName = FAM
    i.styleMapStyleName = "italic" if italic else "regular"
    i.versionMajor, i.versionMinor = 1, 0
    i.unitsPerEm = 1000
    i.ascender, i.descender = 960, -240
    i.xHeight, i.capHeight = XH, CAP
    i.italicAngle = -round(ITALIC_ANGLE, 2) if italic else 0
    i.copyright = "Copyright 2026 Bloxwap, Inc."
    i.trademark = "Bloxwap is a trademark of Bloxwap, Inc."
    i.openTypeNameDesigner = "Bloxwap, Inc."
    i.openTypeNameManufacturer = "Bloxwap, Inc."
    i.openTypeNameManufacturerURL = "https://bloxwap.com"
    i.openTypeNameDesignerURL = "https://bloxwap.github.io/font/"
    i.openTypeNameLicense = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                             "This license is available with a FAQ at: https://openfontlicense.org")
    i.openTypeNameLicenseURL = "https://openfontlicense.org"
    i.openTypeOS2VendorID = "BLXW"
    i.openTypeOS2WeightClass = weight
    i.openTypeOS2TypoAscender, i.openTypeOS2TypoDescender, i.openTypeOS2TypoLineGap = 960, -240, 0
    i.openTypeOS2WinAscent, i.openTypeOS2WinDescent = 1250, 420
    i.openTypeHheaAscender, i.openTypeHheaDescender, i.openTypeHheaLineGap = 960, -240, 0
    i.openTypeOS2Selection = [7]
    i.postscriptUnderlinePosition = -100
    i.postscriptUnderlineThickness = round(size * CELL)
    i.openTypeOS2StrikeoutPosition = 350 + round(size * CELL / 2)
    i.openTypeOS2StrikeoutSize = round(size * CELL)
    i.postscriptIsFixedPitch = True
    i.openTypeOS2Panose = [2, 11, 5, 9, 2, 2, 2, 2, 2, 4]
    for name in order:
        o = outs[name]
        gl = f.newGlyph(name)
        gl.unicodes = list(o.unicodes)
        gl.width = o.advance
        pen = gl.getPen()
        for c in o.contours:
            c.draw(pen)
        for cn, dx, dy in o.components:
            pen.addComponent(cn, (1, 0, 0, 1, round(dx), round(dy)))
        for an, (x, y) in sorted(o.anchors.items()):
            gl.appendAnchor({"name": an, "x": round(x), "y": round(y)})
    f.lib["public.glyphOrder"] = order
    f.lib["public.openTypeCategories"] = {n: ("mark" if outs[n].kind == "mark" else "base") for n in order}
    f.features.text = features
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.rmtree(path)
    f.save(path)


def pixel_features(outs, italic):
    """features.make_features plus a local fix: the core builds @FigNumr and
    @FigDnom from two independent set iterations, so their orders can
    disagree (class-to-class substitution then maps 4 -> three.dnom).
    Rebuild @FigDnom (and sort @FigDefault/@FigNumr) so they are paired."""
    import re
    fea = make_features(FAMILY, outs, italic)
    m = re.search(r"@FigDefault = \[([^\]]*)\];", fea)
    if m:
        bases = sorted(m.group(1).split())
        fea = re.sub(r"@FigDefault = \[[^\]]*\];", f"@FigDefault = [{' '.join(bases)}];", fea)
        fea = re.sub(r"@FigNumr = \[[^\]]*\];", f"@FigNumr = [{' '.join(b + '.numr' for b in bases)}];", fea)
        fea = re.sub(r"@FigDnom = \[[^\]]*\];", f"@FigDnom = [{' '.join(b + '.dnom' for b in bases)}];", fea)
    return fea


def master_style(wn, rond, italic):
    """Default-roundness masters carry plain style names (the default master
    becomes the VF's default name); the others are tagged Square / Round."""
    base = wn if rond == ROND_DEFAULT else f"{wn} {dict(ROND_LABELS)[rond]}"
    if italic:
        return "Italic" if base == "Regular" else f"{base} Italic"
    return base


def master_files():
    for italic in (False, True):
        for w, wn, size in WGHT_MASTERS:
            for rond in ROND_MASTERS:
                fn = f"{PS}-{wn}{'Italic' if italic else ''}-R{rond}.ufo"
                yield italic, w, wn, size, rond, fn


def generate_pixel(outdir: Path):
    outdir = Path(outdir)
    t0 = time.time()
    register_all()
    outdir.mkdir(parents=True, exist_ok=True)
    for p in outdir.glob("*.ufo"):
        shutil.rmtree(p)
    sources = []
    stats = {}
    for italic in (False, True):
        masters = {}
        for w, wn, size in WGHT_MASTERS:
            for rond in ROND_MASTERS:
                masters[(wn, rond)] = (size, make_master(size, rond, italic))
        ref_outs = masters[("Regular", ROND_DEFAULT)][1][0]
        names = set(ref_outs)
        for k, (_, (outs, _, _)) in masters.items():
            if set(outs) != names:
                raise SystemExit(f"pixel {k}: glyph set mismatch {sorted(names ^ set(outs))[:20]}")
        order = glyph_order(ref_outs)
        fea = pixel_features(ref_outs, italic)
        for (wn, rond), (size, (outs, cmap, skipped)) in masters.items():
            w = {n: v for v, n, _ in WGHT_MASTERS}[wn]
            fn = f"{PS}-{wn}{'Italic' if italic else ''}-R{rond}.ufo"
            style = master_style(wn, rond, italic)
            write_ufo(outdir / fn, style, w, italic, size, outs, order, fea)
            sources.append((fn, wn, w, rond, italic, style))
        outs, cmap, skipped = masters[("Regular", ROND_DEFAULT)][1]
        stats[italic] = (outs, cmap, skipped)
        print(f"  pixel {'italic' if italic else 'upright'}: {len(order)} glyphs, "
              f"{len(cmap)} codepoints ({time.time() - t0:.1f}s)", flush=True)
    write_designspace(outdir, sources)
    _report(stats[False])
    return stats


def _report(stat):
    outs, cmap, skipped = stat
    bitmaps = [n for n, d in art.REG.items() if d.pix]
    marks = [n for n in bitmaps if art.REG[n].kind == "mark"]
    shapes = [n for n, d in art.REG.items() if d.shapes is not None and not d.pix]
    refs = [n for n, d in art.REG.items() if d.comps and not d.pix]
    empty = [n for n, d in art.REG.items() if not d.pix and not d.comps and d.shapes is None]
    composed = [n for n in outs if n not in art.REG]
    print(f"  pixel: {len(outs)} glyphs = {len(bitmaps)} hand-drawn bitmaps ({len(marks)} marks) + "
          f"{len(shapes)} programmatic (box/blocks) + {len(refs)} component refs (aliases, sups, spacing) + "
          f"{len(empty)} spaces & zero-width + {len(composed)} engine composites")
    print(f"  pixel: {len(cmap)} encoded codepoints; {len(skipped)} of composites.target_codepoints() skipped")


def write_designspace(outdir: Path, sources):
    doc = DesignSpaceDocument()
    doc.formatVersion = "5.0"
    wght = AxisDescriptor()
    wght.name, wght.tag = "Weight", "wght"
    wght.minimum, wght.default, wght.maximum = 100, 400, 900
    wght.axisLabels = [AxisLabelDescriptor(name=n, userValue=w, elidable=(w == 400)) for w, n, _ in B.WEIGHTS]
    doc.addAxis(wght)
    rond = AxisDescriptor()
    rond.name, rond.tag = "Roundness", "ROND"
    rond.minimum, rond.default, rond.maximum = 0, ROND_DEFAULT, 100
    rond.axisLabels = [AxisLabelDescriptor(name=n, userValue=v, elidable=(v == ROND_DEFAULT))
                       for v, n in ROND_LABELS]
    doc.addAxis(rond)
    ital = DiscreteAxisDescriptor()
    ital.name, ital.tag = "Italic", "ital"
    ital.values = [0, 1]
    ital.default = 0
    ital.axisLabels = [AxisLabelDescriptor(name="Roman", userValue=0, elidable=True, linkedUserValue=1),
                       AxisLabelDescriptor(name="Italic", userValue=1)]
    doc.addAxis(ital)
    for fn, wn, w, r, italic, style in sources:
        s = SourceDescriptor()
        s.filename = fn
        s.familyName = FAM
        s.styleName = style
        s.location = {"Weight": w, "Roundness": r, "Italic": 1 if italic else 0}
        doc.addSource(s)
    for italic in (False, True):
        for w, n, _ in B.WEIGHTS:
            i = InstanceDescriptor()
            i.familyName = FAM
            i.styleName = ("Italic" if n == "Regular" else f"{n} Italic") if italic else n
            i.designLocation = {"Weight": w, "Roundness": ROND_DEFAULT, "Italic": 1 if italic else 0}
            psn = f"{PS}-{n if not (italic and n == 'Regular') else ''}{'Italic' if italic else ''}"
            i.postScriptFontName = psn
            i.styleMapFamilyName = FAM + ("" if n in ("Regular", "Bold") else f" {n}")
            i.styleMapStyleName = ({"Regular": "regular", "Bold": "bold"}.get(n, "regular")
                                   if not italic else {"Regular": "italic", "Bold": "bold italic"}.get(n, "italic"))
            i.filename = f"instances/{psn}.ufo"
            doc.addInstance(i)
    for italic in (False, True):
        vf = VariableFontDescriptor(
            name=f"{PS}{'-Italic' if italic else ''}[ROND,wght]",
            axisSubsets=[RangeAxisSubsetDescriptor(name="Weight"),
                         RangeAxisSubsetDescriptor(name="Roundness"),
                         ValueAxisSubsetDescriptor(name="Italic", userValue=1 if italic else 0)])
        doc.addVariableFont(vf)
    doc.write(outdir / f"{PS}.designspace")
