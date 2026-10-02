#!/usr/bin/env python3
"""Check glyph skeletons: they must build at every master (upright+italic,
sans+mono) and stay point-compatible across weights.

usage: check_glyphs.py [module_name ...]     e.g. check_glyphs.py latin_upper
       (no args = all glyphs)
"""
import sys, importlib, pkgutil, traceback
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from bwfont.skeleton import GLYPHS, G, params_for, outline
from bwfont.geometry import Plan
from bwfont import preview
import bwfont.glyphs as gl

args = sys.argv[1:]
packs = None
if "--pack" in args:
    i = args.index("--pack")
    packs = set(args[i + 1].split(","))
    args = args[:i] + args[i + 2:]
mods = args
for m in pkgutil.iter_modules(gl.__path__):
    importlib.import_module(f"bwfont.glyphs.{m.name}")
def _mod(gd):
    return getattr(gd.func, "__module__", "").rsplit(".", 1)[-1]
names = [n for n, gd in GLYPHS.items() if ((not mods) or _mod(gd) in mods)
         and (packs is None or set(gd.pack if isinstance(gd.pack, tuple) else (gd.pack,)) & packs)]

def sig(cs):
    return [tuple(op[0] for op in c.ops) for c in cs]

bad = 0
for fam in ("sans", "mono"):
    for slant in (0.0, 9.0):
        plan = Plan()
        for n in names:
            gd = GLYPHS[n]
            if fam not in gd.families:
                continue
            sigs = {}
            try:
                for stem in (84, 22, 180):
                    g = G(params_for(fam, stem, slant), n)
                    gd.func(g)
                    cs = outline(g, plan, n)
                    sigs[stem] = sig(cs)
                    if cs:
                        preview.union(cs)
            except Exception as e:
                bad += 1
                print(f"ERROR {n} [{fam} slant={slant}]: {e!r}")
                traceback.print_exc(limit=3)
                continue
            if not (sigs[84] == sigs[22] == sigs[180]):
                bad += 1
                print(f"INCOMPATIBLE {n} [{fam} slant={slant}]: contours "
                      f"{[len(x) for x in sigs[22]]} / {[len(x) for x in sigs[84]]} / {[len(x) for x in sigs[180]]}")
print(f"checked {len(names)} glyphs, {bad} problems")
sys.exit(1 if bad else 0)
