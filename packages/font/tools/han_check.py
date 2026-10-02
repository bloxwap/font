#!/usr/bin/env python3
"""Han coverage + validation report.

usage: han_check.py [--level 3500] [--sheet out.png] [--chars 字符] [--stems 22,84,180]
Reports: resolvable chars, stroke-count mismatches vs Unihan kTotalStrokes,
and the most-needed missing components/decompositions."""
import argparse, collections, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from bwfont.han import engine as E, load_all

ap = argparse.ArgumentParser()
ap.add_argument("--level", type=int, default=3500)
ap.add_argument("--sheet")
ap.add_argument("--chars")
ap.add_argument("--stems", default="84")
ap.add_argument("--size", type=int, default=64)
ap.add_argument("--quiet", action="store_true")
ap.add_argument("--jp", action="store_true",
                help="Japanese: check the 2,136 Jōyō kanji through the 'jp' layer (ids_jp*.txt, <name>@jp components)")
ap.add_argument("--ids-only", action="store_true",
                help="verify decompositions against Unihan stroke counts even where components are not drawn yet")
ap.add_argument("--range", default=None, help="tgh index range a-b to report on")
ap.add_argument("--radicals", default=None,
                help="a-b: list missing/undrawn leaf components whose Kangxi radical is in a..b")
a = ap.parse_args()
load_all()
order, strokes = E.load_unihan()
LAYER = "jp" if a.jp else None
target = [c for c, i in order if i <= a.level]
if a.jp:
    target, _jst = E.load_joyo()
    for k, v in _jst.items():
        strokes.setdefault(k, v)
if a.range:
    lo, hi = map(int, a.range.split("-"))
    target = target[lo - 1:hi] if a.jp else [c for c, i in order if lo <= i <= hi]


def _dec(x):
    """Decomposition of x honouring the active layer (None if none)."""
    if LAYER and x in E.LAYERS.get(LAYER, {}):
        return E.LAYERS[LAYER][x]
    return E.DECOMP.get(x)


def _is_comp(x):
    return x in E.COMPONENTS or (LAYER and f"{x}@{LAYER}" in E.COMPONENTS)

if a.radicals:
    from bwfont.han.engine import DECOMP, COMPONENTS, parse_ids, radical_of
    lo, hi = map(int, a.radicals.split("-"))
    need = collections.Counter()
    def walk(x, depth=0, stack=()):
        if isinstance(x, tuple):
            for c in x[1]:
                walk(c, depth + 1, stack)
            return
        if LAYER and x in E.LAYERS.get(LAYER, {}) and x not in stack and depth < 12:
            walk(parse_ids(E.LAYERS[LAYER][x]), depth + 1, stack + (x,))
            return
        if _is_comp(x):
            return
        if x in DECOMP and x not in stack and depth < 12:
            walk(parse_ids(DECOMP[x]), depth + 1, stack + (x,))
            return
        need[x] += 1
    for ch in target:
        d = _dec(ch)
        if d and not (LAYER and f"{ch}@{LAYER}" in COMPONENTS):
            walk(parse_ids(d))
        elif not _is_comp(ch):
            need[ch] += 1      # no decomposition yet: the char itself may be atomic
    mine = [(k, v) for k, v in need.most_common() if (radical_of(k) or 0) and lo <= radical_of(k) <= hi]
    other = [(k, v) for k, v in need.most_common() if not radical_of(k)]
    print(f"undrawn leaves with radical {lo}-{hi}: {len(mine)}")
    print(" ".join(f"{k}×{v}" for k, v in mine[:400]))
    print("undrawn leaves without radical data (shared):", " ".join(f"{k}×{v}" for k, v in other[:100]))
    sys.exit(0)

if a.ids_only:
    from bwfont.han.engine import DECOMP, COMPONENTS, parse_ids, IDC
    missing_ids, mism, unknown = [], [], collections.Counter()
    def vcount(x, depth=0, stack=()):
        """virtual stroke count; None if unknown"""
        if isinstance(x, tuple):
            vals = [vcount(c, depth + 1, stack) for c in x[1]]
            return None if any(v is None for v in vals) else sum(vals)
        if LAYER and f"{x}@{LAYER}" in COMPONENTS:
            return len(COMPONENTS[f"{x}@{LAYER}"].paths)
        if LAYER and x in E.LAYERS.get(LAYER, {}) and x not in stack and depth < 12:
            return vcount(parse_ids(E.LAYERS[LAYER][x]), depth + 1, stack + (x,))
        if x in COMPONENTS:
            return len(COMPONENTS[x].paths)
        if x in DECOMP and x not in stack and depth < 12:
            return vcount(parse_ids(DECOMP[x]), depth + 1, stack + (x,))
        if x in strokes:
            return strokes[x]
        if x in E.TOKEN_STROKES:
            return E.TOKEN_STROKES[x]
        unknown[x] += 1
        return None
    for ch in target:
        if _dec(ch) is None and not _is_comp(ch):
            missing_ids.append(ch); continue
        try:
            n = vcount(ch)
        except Exception as e:
            mism.append((ch, "ERR", str(e))); continue
        if n is not None and ch in strokes and n != strokes[ch]:
            mism.append((ch, n, strokes[ch]))
    print(f"decomposed {len(target) - len(missing_ids)}/{len(target)}; stroke mismatches {len(mism)}")
    print("mismatches:", " ".join(f"{c}{n}/{u}" for c, n, u in mism[:150]))
    print("no decomposition:", "".join(missing_ids[:300]))
    print("leaves without stroke data:", " ".join(f"{k}×{v}" for k, v in unknown.most_common(60)))
    sys.exit(0)
ok, bad_strokes, missing = [], [], collections.Counter()
for ch in target:
    try:
        t = E.resolve(ch, layer=LAYER)
    except KeyError as e:
        missing[str(e.args[0])] += 1
        continue
    except Exception as e:
        missing[f"<error {ch}: {e}>"] += 1
        continue
    ok.append(ch)
    n = E.stroke_count(t)
    if ch in strokes and strokes[ch] != n:
        bad_strokes.append((ch, n, strokes[ch]))
print(f"components: {len(E.COMPONENTS)}  decompositions: {len(E.DECOMP)}")
print(f"resolvable: {len(ok)}/{len(target)}   stroke-count mismatches: {len(bad_strokes)}")
if not a.quiet:
    if bad_strokes:
        print("mismatches (char ours/unihan):", " ".join(f"{c}{n}/{u}" for c, n, u in bad_strokes[:80]))
    print("most needed missing:", " ".join(f"{k}×{v}" for k, v in missing.most_common(80)))
if a.sheet:
    from bwfont.skeleton import G, params_for, outline
    from bwfont.geometry import Plan
    from bwfont import preview
    from PIL import Image
    chars = list(a.chars) if a.chars else ok[:120]
    rows = []
    for stem in [float(s) for s in a.stems.split(",")]:
        line = []
        for i, ch in enumerate(chars):
            g = G(params_for("sans", stem), ch)
            try:
                E.build_char(g, ch, layer=LAYER)
                cs = outline(g, Plan(), ch)
            except Exception as e:
                print("draw error", ch, e); cs = []
            line.append((cs, 1000))
            if len(line) == 20 or i == len(chars) - 1:
                rows.append(preview.render_line(line, size=a.size, asc=900, desc=-140)); line = []
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    img = Image.new("L", (W, H), 255); y = 0
    for r in rows:
        img.paste(r, (0, y)); y += r.height
    img.save(a.sheet)
