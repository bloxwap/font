#!/usr/bin/env python3
"""Find skeleton strokes that fold back on themselves (a segment whose
direction reverses against its neighbour, or a straight segment that
flips direction between masters).  These render as notches/slivers in
heavy weights and while interpolating.  usage: check_cusps.py [module ...]"""
import sys, importlib, pkgutil, math
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from bwfont.skeleton import GLYPHS, G, params_for, _unfold
from bwfont.geometry import start_tangent, end_tangent, norm, sub, dot, length
import bwfont.glyphs as gl
for m in pkgutil.iter_modules(gl.__path__):
    importlib.import_module(f"bwfont.glyphs.{m.name}")
mods = sys.argv[1:]

def seg_dirs(sg):
    if sg.kind == "line":
        d = sub(sg.pts[1], sg.pts[0])
        return (norm(d), norm(d), length(d))
    return (start_tangent(*sg.pts), end_tangent(*sg.pts), length(sub(sg.pts[-1], sg.pts[0])))

bad = {}
for fam in ("sans", "mono"):
    for slant in (0.0, 9.0):
        ref = {}
        for stem in (84, 22, 50, 120, 150, 180):
            for n, gd in GLYPHS.items():
                if fam not in gd.families:
                    continue
                if mods and getattr(gd.func, "__module__", "").rsplit(".", 1)[-1] not in mods:
                    continue
                g = G(params_for(fam, stem, slant), n)
                try:
                    gd.func(g)
                except Exception:
                    continue
                for si, s in enumerate(_unfold(x) for x in g.strokes):
                    dirs = [seg_dirs(sg) for sg in s.segs]
                    for i in range(len(dirs)):
                        key = (n, si, i)
                        a0, a1, L = dirs[i]
                        # 1) fold between consecutive segments of one stroke
                        if i + 1 < len(dirs) and dirs[i + 1][2] > 1 and L > 1:
                            if dot(a1, dirs[i + 1][0]) < 0.2:
                                bad.setdefault(n, set()).add(f"fold s{si} seg{i}->{i+1} @W{stem} {fam}")
                        # 2) straight segment flips direction vs Regular
                        if s.segs[i].kind == "line" and L > 0.5:
                            if stem == 84:
                                ref[(fam, slant, key)] = a0
                            elif (fam, slant, key) in ref and dot(ref[(fam, slant, key)], a0) < 0:
                                bad.setdefault(n, set()).add(f"flip s{si} seg{i} @W{stem} {fam}")
for n in sorted(bad):
    print(n, "|", "; ".join(sorted(bad[n])[:4]))
print(f"{len(bad)} glyphs with folds/flips")
