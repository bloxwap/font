#!/usr/bin/env python3
"""Generate UFO sources + designspaces for Bloxwap Sans / Mono / Pixel.

usage: generate.py [sans|mono|pixel ...]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fontTools.designspaceLib import (AxisDescriptor, AxisLabelDescriptor, DesignSpaceDocument,
                                      DiscreteAxisDescriptor, InstanceDescriptor, SourceDescriptor,
                                      VariableFontDescriptor, RangeAxisSubsetDescriptor,
                                      ValueAxisSubsetDescriptor)

from bwfont import build as B
from bwfont.geometry import Plan
from bwfont.features import make_features, glyph_order
from bwfont.kerning import make_kerning
from bwfont.families import FAMILIES

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources"


def ps(family):
    return FAMILIES[family].ps


def gen_family(family: str):
    B.load_glyph_modules()
    fam = FAMILIES[family]
    t0 = time.time()
    fam_dir = SRC / family
    upright_spacing = {}
    sources = []
    all_order = None
    for italic in ((False, True) if fam.italic else (False,)):
        slant = B.ITALIC_ANGLE if italic else 0.0
        plan = Plan()
        masters = {}
        # Regular first: it records the structural plan
        order_of_build = ["Regular", "Thin", "Black"]
        stems = dict(B.MASTERS)
        for mname in order_of_build:
            stem = stems[mname]
            ref = upright_spacing.get(mname) if italic else None
            params, outs = B.make_master(fam, stem, slant, plan, ref)
            cmap = B.add_composites(params, outs, family)
            masters[mname] = (params, outs, cmap)
            if not italic:
                upright_spacing[mname] = {n: (getattr(o, "dx", 0), o.advance) for n, o in outs.items()
                                          if o.kind != "mark" and not o.components}
        # all masters must share the glyph set
        names = set(masters["Regular"][1])
        for mname, (_, outs, _) in masters.items():
            if set(outs) != names:
                missing = names ^ set(outs)
                raise SystemExit(f"{family} {mname}: glyph set mismatch {sorted(missing)[:20]}")
        order = glyph_order(masters["Regular"][1])
        all_order = order
        fea = make_features(fam, masters["Regular"][1], italic)
        kpairs = None
        for mname, (params, outs, cmap) in masters.items():
            kern, groups, kp = make_kerning(fam.style if fam.kern else "none", params, outs, kpairs)
            if kpairs is None:
                kpairs = kp
            style = mname if not italic else ("Italic" if mname == "Regular" else f"{mname} Italic")
            fn = f"{ps(family)}-{mname}{'Italic' if italic else ''}.ufo"
            weight = {"Thin": 100, "Regular": 400, "Black": 900}[mname]
            B.write_ufo(fam_dir / fn, fam, style, weight, italic, params, outs, order, fea, kern, groups)
            sources.append((fn, mname, italic, params))
        print(f"  {family} {'italic' if italic else 'upright'}: {len(order)} glyphs "
              f"({time.time() - t0:.1f}s)", flush=True)
    write_designspace(family, sources)
    return all_order


def write_designspace(family, sources):
    fam = FAMILIES[family]
    doc = DesignSpaceDocument()
    doc.formatVersion = "5.0"
    wght = AxisDescriptor()
    wght.name, wght.tag = "Weight", "wght"
    wght.minimum, wght.default, wght.maximum = 100, 400, 900
    wght.map = [(w, s) for w, _, s in B.WEIGHTS]
    wght.axisLabels = [AxisLabelDescriptor(name=n, userValue=w, elidable=(w == 400)) for w, n, _ in B.WEIGHTS]
    doc.addAxis(wght)
    if fam.italic:
        ital = DiscreteAxisDescriptor()
        ital.name, ital.tag = "Italic", "ital"
        ital.values = [0, 1]
        ital.default = 0
        ital.axisLabels = [AxisLabelDescriptor(name="Roman", userValue=0, elidable=True, linkedUserValue=1),
                           AxisLabelDescriptor(name="Italic", userValue=1)]
        doc.addAxis(ital)

    def loc(stem, italic):
        d = {"Weight": stem}
        if fam.italic:
            d["Italic"] = 1 if italic else 0
        return d

    for fn, mname, italic, params in sources:
        s = SourceDescriptor()
        s.filename = fn
        s.familyName = fam.name
        s.styleName = mname + (" Italic" if italic else "")
        s.location = loc(params.W, italic)
        doc.addSource(s)
    for italic in ((False, True) if fam.italic else (False,)):
        for w, n, stem in B.WEIGHTS:
            i = InstanceDescriptor()
            i.familyName = fam.name
            i.styleName = ("Italic" if n == "Regular" else f"{n} Italic") if italic else n
            i.designLocation = loc(stem, italic)
            tail = (n if not (italic and n == "Regular") else "") + ("Italic" if italic else "")
            i.postScriptFontName = f"{fam.ps}-{tail}"
            i.styleMapFamilyName = fam.name + ("" if n in ("Regular", "Bold") else f" {n}")
            i.styleMapStyleName = ({"Regular": "regular", "Bold": "bold"}.get(n, "regular")
                                   if not italic else {"Regular": "italic", "Bold": "bold italic"}.get(n, "italic"))
            i.filename = f"instances/{fam.ps}-{tail}.ufo"
            doc.addInstance(i)
    for italic in ((False, True) if fam.italic else (False,)):
        subsets = [RangeAxisSubsetDescriptor(name="Weight")]
        if fam.italic:
            subsets.append(ValueAxisSubsetDescriptor(name="Italic", userValue=1 if italic else 0))
        doc.addVariableFont(VariableFontDescriptor(
            name=f"{fam.ps}{'-Italic' if italic else ''}[wght]", axisSubsets=subsets))
    doc.write(SRC / family / f"{fam.ps}.designspace")


if __name__ == "__main__":
    fams = sys.argv[1:] or ["sans", "mono"]
    for fam in fams:
        if fam == "pixel":
            from bwfont.pixel import generate_pixel
            generate_pixel(SRC / "pixel")
        else:
            gen_family(fam)
