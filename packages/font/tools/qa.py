#!/usr/bin/env python3
"""Release QA: OTS (browser sanitizer) on every font, basic table sanity,
glyph/cmap counts and Hyperglot language support.  usage: qa.py [fonts_dir]"""
import json, subprocess, sys
from pathlib import Path
import ots
from fontTools.ttLib import TTFont
from check_unicode import unicode_errors

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "fonts")
fails = 0
report = {}
for fam in sorted(p for p in root.iterdir() if p.is_dir()):
    files = sorted(f for f in fam.rglob("*") if f.suffix in (".otf", ".ttf", ".woff", ".woff2"))
    bad = []
    unicode_bad = []
    for f in files:
        r = ots.sanitize(str(f), "/dev/null", capture_output=True)
        if r.returncode != 0:
            bad.append((f.name, (r.stderr or b"").decode()[:300]))
        with TTFont(f) as font:
            for error in unicode_errors(font):
                unicode_bad.append((f.name, error))
    vf = sorted((fam / "variable").glob("*.ttf"))
    info = {"files": len(files), "ots_failures": len(bad), "unicode_failures": len(unicode_bad)}
    if vf:
        t = TTFont(vf[0])
        info["glyphs"] = len(t.getGlyphOrder())
        info["codepoints"] = len(t.getBestCmap())
        info["axes"] = [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in t["fvar"].axes]
        gsub = sorted({fr.FeatureTag for fr in t["GSUB"].table.FeatureList.FeatureRecord}) if "GSUB" in t else []
        gpos = sorted({fr.FeatureTag for fr in t["GPOS"].table.FeatureList.FeatureRecord}) if "GPOS" in t else []
        info["features"] = sorted(set(gsub) | set(gpos))
        out = subprocess.run([str(Path(sys.executable).parent / "hyperglot"), str(vf[0])],
                             capture_output=True, text=True).stdout
        tot = [l for l in out.splitlines() if "languages supported in total" in l]
        info["languages"] = int(tot[0].split()[0]) if tot else 0
    report[fam.name] = info
    for name, err in bad:
        print(f"OTS FAIL {fam.name}/{name}: {err}")
    for name, err in unicode_bad:
        print(f"UNICODE FAIL {fam.name}/{name}: {err}")
    fails += len(bad) + len(unicode_bad)
print(json.dumps(report, indent=1))
sys.exit(1 if fails else 0)
