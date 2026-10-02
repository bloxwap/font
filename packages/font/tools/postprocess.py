#!/usr/bin/env python3
"""Post-process compiled fonts into the distributable layout.

build/<fam>/{variable,otf,ttf}  ->  fonts/<PS>/{variable,otf,ttf,woff2,woff}
                                ->  apps/docs/public/fonts/<PS>/..., apps/docs/public/downloads/*.zip,
                                    apps/docs/public/bloxwap-font.css (the website, see apps/docs/)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fontTools.ttLib import TTFont, newTable

ROOT = Path(__file__).resolve().parent.parent          # packages/font
REPO = ROOT.parent.parent                               # repository root
DOCS = REPO / "apps" / "docs"                           # the Fumadocs website
LICENSE = REPO / "LICENSE"                              # SIL OFL 1.1 text (shipped as OFL.txt)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bwfont.families import FAMILIES  # noqa: E402

PS = {fid: f.ps for fid, f in FAMILIES.items()}


def fix_common(font: TTFont, hinted=False):
    font["OS/2"].fsType = 0
    font["head"].fontRevision = 1.0
    if "gasp" not in font:
        gasp = newTable("gasp")
        gasp.version = 1
        # smooth + gridfit everywhere (symmetric smoothing for ClearType)
        gasp.gaspRange = {0xFFFF: 0x000F if hinted else 0x000A}
        font["gasp"] = gasp


def autohint(src: Path, dst: Path) -> bool:
    try:
        import ttfautohint
        ttfautohint.ttfautohint(in_file=str(src), out_file=str(dst), hint_composites=True,
                                no_info=True, increase_x_height=0, default_script="latn",
                                fallback_script="latn")
        return True
    except Exception as e:  # pragma: no cover - hinting is best-effort
        print(f"      autohint skipped for {src.name}: {e}")
        return False


def process_static_ttf(args):
    src, out_ttf, out_woff2, out_woff = args
    tmp = out_ttf.with_suffix(".hinted.ttf")
    hinted = autohint(src, tmp)
    f = TTFont(tmp if hinted else src)
    fix_common(f, hinted)
    f.save(out_ttf)
    if hinted:
        tmp.unlink()
    for flavor, out in (("woff2", out_woff2), ("woff", out_woff)):
        w = TTFont(out_ttf)
        w.flavor = flavor
        w.save(out)
    return out_ttf.name


def process_otf(args):
    src, out = args
    f = TTFont(src)
    fix_common(f)
    f.save(out)
    return out.name


OVERLAP_SIMPLE = 0x40
OVERLAP_COMPOUND = 0x0400


def set_overlap_flags(font: TTFont):
    """Variable fonts keep their overlapping strokes (removing overlaps would break
    master compatibility). Flag them so Apple's rasterizer (Safari, and Chrome on
    macOS) fills overlaps with the non-zero rule cleanly instead of anti-aliasing
    seams and dark spots along every join, which reads as jagged text."""
    glyf = font["glyf"]
    for name in glyf.keys():
        g = glyf[name]
        if g.isComposite():
            g.components[0].flags |= OVERLAP_COMPOUND
        elif g.numberOfContours > 0:
            g.flags[0] |= OVERLAP_SIMPLE


def process_vf(args):
    src, out_ttf, out_woff2 = args
    f = TTFont(src)
    fix_common(f)
    set_overlap_flags(f)
    f.save(out_ttf)
    w = TTFont(out_ttf)
    w.flavor = "woff2"
    w.save(out_woff2)
    return out_ttf.name


def run(fams):
    jobs_static, jobs_otf, jobs_vf = [], [], []
    for fam in fams:
        ps = PS[fam]
        b = ROOT / "build" / fam
        d = ROOT / "fonts" / ps
        if d.exists():
            shutil.rmtree(d)
        for sub in ("variable", "otf", "ttf", "woff2", "woff"):
            (d / sub).mkdir(parents=True, exist_ok=True)
        for p in sorted((b / "variable").glob("*.ttf")):
            jobs_vf.append((p, d / "variable" / p.name, d / "variable" / (p.stem + ".woff2")))
        for p in sorted((b / "otf").glob("*.otf")):
            jobs_otf.append((p, d / "otf" / p.name))
        for p in sorted((b / "ttf").glob("*.ttf")):
            jobs_static.append((p, d / "ttf" / p.name, d / "woff2" / (p.stem + ".woff2"),
                                d / "woff" / (p.stem + ".woff")))
    with ProcessPoolExecutor() as ex:
        for name in ex.map(process_vf, jobs_vf):
            pass
        for name in ex.map(process_otf, jobs_otf):
            pass
        for name in ex.map(process_static_ttf, jobs_static):
            pass
    print(f"    {len(jobs_vf)} variable, {len(jobs_otf)} otf, {len(jobs_static)} ttf/woff/woff2")


def package():
    """Zips and web copies for the website (apps/docs/, a Fumadocs app served at /font/):
    apps/docs/public/downloads/<PS>.zip + Bloxwap-Fonts.zip, apps/docs/public/fonts/<PS>/{variable,woff2}/
    (WOFF2 only) and apps/docs/public/OFL.txt."""
    public = DOCS / "public"
    dl = public / "downloads"
    dl.mkdir(parents=True, exist_ok=True)
    # The all-in-one zip carries the three core families only: with the CJK
    # companions it would exceed GitHub's 100 MB per-file limit.  Script
    # companions ship as their own zips.
    ALL = ("BloxwapSans", "BloxwapMono", "BloxwapPixel")
    allzip = zipfile.ZipFile(dl / "Bloxwap-Fonts.zip", "w", zipfile.ZIP_DEFLATED)
    allzip.write(LICENSE, "Bloxwap-Fonts/OFL.txt")
    for ps in PS.values():
        d = ROOT / "fonts" / ps
        if not d.exists():
            continue
        z = zipfile.ZipFile(dl / f"{ps}.zip", "w", zipfile.ZIP_DEFLATED)
        z.write(LICENSE, f"{ps}/OFL.txt")
        for p in sorted(d.rglob("*")):
            if p.is_file():
                rel = p.relative_to(d)
                z.write(p, f"{ps}/{rel}")
                if ps in ALL:
                    allzip.write(p, f"Bloxwap-Fonts/{ps}/{rel}")
        z.close()
        # web copies (WOFF2 only; desktop formats ship in the zips)
        w = public / "fonts" / ps
        if w.exists():
            shutil.rmtree(w)
        (w / "variable").mkdir(parents=True)
        (w / "woff2").mkdir(parents=True)
        for p in (d / "variable").glob("*.woff2"):
            shutil.copy2(p, w / "variable" / p.name)
        for p in (d / "woff2").glob("*.woff2"):
            shutil.copy2(p, w / "woff2" / p.name)
    allzip.close()
    shutil.copy2(LICENSE, public / "OFL.txt")
    # the two static TTFs the website's social cards are rendered with (Satori needs TTF/OTF)
    og = DOCS / "assets" / "og"
    og.mkdir(parents=True, exist_ok=True)
    for style in ("SemiBold", "Black"):
        src = ROOT / "fonts" / "BloxwapSans" / "ttf" / f"BloxwapSans-{style}.ttf"
        if src.exists():
            shutil.copy2(src, og / src.name)


def stamp_site():
    """Cache-busting for the website: hash the web fonts, then write the combined
    stylesheet apps/docs/public/bloxwap-font.css (URLs carry ?v=<hash>) and the
    FONT_VERSION constant in apps/docs/lib/font-version.ts that the app appends to
    its own font and stylesheet URLs. See tools/webfonts.py."""
    import webfonts
    webfonts.write_css(DOCS / "public")


if __name__ == "__main__":
    fams = sys.argv[1:] or [f for f in PS if (ROOT / "build" / f).exists()]
    run(fams)
    package()
    stamp_site()
    sd = ROOT / "tools" / "site_data.py"
    if sd.exists():
        subprocess.run([sys.executable, str(sd)], check=False)
