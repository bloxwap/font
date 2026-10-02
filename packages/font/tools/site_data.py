#!/usr/bin/env python3
"""Generate the JSON data that powers the Bloxwap Font website (apps/docs/, a Fumadocs app).

Usage:
    .venv/bin/python tools/site_data.py                # write apps/docs/public/data/*.json
    .venv/bin/python tools/site_data.py --dev-fonts    # also convert build VFs into
                                                       # apps/docs/public/fonts/ (dev preview)
    .venv/bin/python tools/site_data.py --no-languages # skip hyperglot (fast)
    .venv/bin/python tools/site_data.py --only sans-kr # one family (repeatable)

Families come from tools/bwfont/families.py (FAMILIES). Inputs (first match wins):
    fonts/<PS>/variable/<PS>[axes].ttf                  (dist, from tools/build_all.sh)
    build/<id>/variable/<PS>[axes].ttf                  (in-progress builds)
    apps/docs/public/fonts/<PS>/variable/<PS>[axes].woff2    (whatever the website already has)

Outputs (apps/docs/public/data/, read by the Next.js app at build time and fetched at runtime):
    <id>.json         metadata, axes, instances, OpenType features, languages, script coverage
    <id>.glyphs.json  the glyph list for the glyph browser (large for CJK, so kept separate)
    index.json        every family in FAMILIES with a `built` flag, totals, zip sizes
    languages.json    every language the collection supports, each with the family that renders it

Families without built fonts are skipped (their JSON is removed); the website then
marks them "in development".
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import unicodedata
from pathlib import Path

from fontTools import unicodedata as ftu
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT.parent.parent / "apps" / "docs" / "public"   # the website's static root (served at /font/)
DATA = PUBLIC / "data"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bwfont.families import FAMILIES as _FAMILY_DEFS  # noqa: E402

try:  # design-side names for stylistic sets, used when the font carries no UI name
    from bwfont.features import SS_NAMES  # noqa: E402
except Exception:  # pragma: no cover
    SS_NAMES = {}

BLURBS = {
    "sans": "Rounded neo-grotesk for interfaces, editorial text and numbers.",
    "mono": "The same rounded design on a fixed 600-unit cell, with code ligatures.",
    "pixel": "Pixel display face with weight and roundness axes.",
    "sans-arabic": "Bloxwap Sans with Arabic: a contemporary interpretation of the Naskh style.",
    "mono-arabic": "Bloxwap Mono with Arabic script on the fixed cell.",
    "sans-kr": "Bloxwap Sans with Korean Hangul.",
    "mono-kr": "Bloxwap Mono with Korean Hangul.",
    "sans-sc": "Bloxwap Sans with Simplified Chinese hanzi.",
    "mono-sc": "Bloxwap Mono with Simplified Chinese hanzi.",
    "sans-jp": "Bloxwap Sans with Japanese kana and Jōyō kanji.",
    "mono-jp": "Bloxwap Mono with Japanese kana and Jōyō kanji.",
    "sans-hebrew": "Bloxwap Sans with Hebrew and full Niqqud.",
    "mono-hebrew": "Bloxwap Mono with Hebrew and full Niqqud.",
    "sans-armenian": "Bloxwap Sans with Armenian, balanced for multilingual typesetting.",
    "mono-armenian": "Bloxwap Mono with Armenian.",
    "sans-georgian": "Bloxwap Sans with modern Georgian: Mkhedruli and Mtavruli.",
    "mono-georgian": "Bloxwap Mono with modern Georgian: Mkhedruli and Mtavruli.",
}

# (id, file stem / PostScript family prefix, display name, blurb) for every defined family.
FAMILIES = [(fid, f.ps, f.name, BLURBS.get(fid, f.name)) for fid, f in _FAMILY_DEFS.items()]

FORMATS = ["otf", "ttf", "woff2", "woff", "variable"]

# Registered/common OpenType feature descriptions (shown when the font has no UI name).
FEATURE_NAMES = {
    "aalt": "Access all alternates", "c2sc": "Capitals to small caps", "calt": "Contextual alternates",
    "case": "Case-sensitive forms", "ccmp": "Glyph composition", "cpsp": "Capital spacing",
    "dlig": "Discretionary ligatures", "dnom": "Denominators", "frac": "Fractions",
    "hlig": "Historical ligatures", "kern": "Kerning", "liga": "Standard ligatures",
    "lnum": "Lining figures", "locl": "Localized forms", "mark": "Mark positioning",
    "mkmk": "Mark-to-mark positioning", "numr": "Numerators", "onum": "Oldstyle figures",
    "ordn": "Ordinals", "pnum": "Proportional figures", "rlig": "Required ligatures",
    "salt": "Stylistic alternates", "sinf": "Scientific inferiors", "smcp": "Small capitals",
    "subs": "Subscript", "sups": "Superscript", "tnum": "Tabular figures", "zero": "Slashed zero",
    "rvrn": "Required variation alternates", "titl": "Titling", "dist": "Distances",
    "init": "Initial forms", "medi": "Medial forms", "fina": "Terminal forms", "isol": "Isolated forms",
    "curs": "Cursive positioning", "rclt": "Required contextual alternates", "abvm": "Above-base mark positioning",
    "blwm": "Below-base mark positioning", "ljmo": "Leading jamo forms", "vjmo": "Vowel jamo forms",
    "tjmo": "Trailing jamo forms", "vert": "Vertical alternates", "vrt2": "Vertical alternates and rotation",
    "vkrn": "Vertical kerning", "vpal": "Proportional alternate vertical metrics", "fwid": "Full widths",
    "hwid": "Half widths", "pwid": "Proportional widths", "halt": "Alternate half widths",
    "palt": "Proportional alternate widths", "trad": "Traditional forms", "smpl": "Simplified forms",
    "jp78": "JIS78 forms", "jp83": "JIS83 forms", "jp90": "JIS90 forms", "jp04": "JIS2004 forms",
    "nlck": "NLC kanji forms", "expt": "Expert forms", "ruby": "Ruby notation forms", "hkna": "Horizontal kana alternates",
}
for _i in range(1, 21):
    FEATURE_NAMES[f"ss{_i:02d}"] = f"Stylistic set {_i}"
for _i in range(1, 100):
    FEATURE_NAMES[f"cv{_i:02d}"] = f"Character variant {_i}"

# Features that are always on / not useful as tester toggles.
HIDDEN_FEATURES = {"ccmp", "mark", "mkmk", "rvrn", "aalt", "dist", "abvm", "blwm", "rlig", "locl",
                   # required shaping features (Arabic joining, Hangul jamo, vertical layout)
                   "init", "medi", "fina", "isol", "med2", "fin2", "fin3", "curs", "rclt",
                   "ljmo", "vjmo", "tjmo", "vert", "vrt2", "vkrn", "vpal", "vhal"}

# Short pangrams / sample sentences for well-known languages (hyperglot iso 639-3).
SAMPLES = {
    "eng": "The quick brown fox jumps over the lazy dog.",
    "deu": "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich.",
    "fra": "Portez ce vieux whisky au juge blond qui fume.",
    "spa": "El veloz murciélago hindú comía feliz cardillo y kiwi.",
    "ita": "Quel vituperabile xenofobo zelante assaggia il whisky ed esclama: alleluja!",
    "nld": "Pa’s wijze lynx bezag vroom het fikse aquaduct.",
    "pol": "Pchnąć w tę łódź jeża lub ośm skrzyń fig.",
    "ces": "Příliš žluťoučký kůň úpěl ďábelské ódy.",
    "slk": "Kŕdeľ šťastných ďatľov učí pri ústí Váhu mĺkveho koňa obhrýzať kôru.",
    "tur": "Pijamalı hasta yağız şoföre çabucak güvendi.",
    "dan": "Høj bly gom vandt fræk sexquiz på wc.",
    "nob": "Vår sære Zulu fra badeøya spilte jo whist og quickstep i min taxi.",
    "swe": "Flygande bäckasiner söka hwila på mjuka tuvor.",
    "hun": "Árvíztűrő tükörfúrógép.",
    "ron": "Muzicologă în bej vând whisky și tequila, preț fix.",
    "hrv": "Gojazni đačić s biciklom drži hmelj i finu vatu u džepu nošnje.",
    "cat": "Jove xef, porti whisky amb quinze glaçons d’hidrogen, coi!",
    "est": "Põdur Zagrebi tšellomängija-följetonist Ciqo külmetas kehvas garaažis.",
    "lav": "Glāžšķūņa rūķīši dzērumā čiepj Baha koncertflīģeļu vākus.",
    "lit": "Įlinkdama fechtuotojo špaga sublykčiojusi pragręžė apvalų arbūzą.",
    "isl": "Kæmi ný öxi hér, ykist þjófum nú bæði víl og ádrepa.",
    "gle": "D’fhuascail Íosa Úrmhac na hÓighe Beannaithe pór Éava agus Ádhaimh.",
    "cym": "Parciais fy jac codi baw hud llawn dŵr ger tŷ Mabon.",
    "vie": "Tôi có thể ăn thủy tinh mà không hại gì.",
    "por": "Luís argüia à Júlia que «brações, fé, chá, óxido, pôr, zângão» eram palavras do português.",
    "rus": "Съешь же ещё этих мягких французских булок, да выпей чаю.",
    "ukr": "Чуєш їх, доцю, га? Кумедна ж ти, прощайся без ґольфів!",
    "bul": "Жълтата дюля беше щастлива, че пухът, който цъфна, замръзна като гьон.",
    "ell": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία.",
    "kor": "다람쥐 헌 쳇바퀴에 타고파.",
    "cmn": "我能吞下玻璃而不伤身体。",
    "jpn": "私はガラスを食べられます。それは私を傷つけません。",
    "zho": "我能吞下玻璃而不伤身体。",
    "arb": "صِف خَلقَ خَودِ كَمِثلِ الشَمسِ إِذ بَزَغَت",
    "ara": "صِف خَلقَ خَودِ كَمِثلِ الشَمسِ إِذ بَزَغَت",
    "fas": "من می‌توانم بدون آسیب دیدن شیشه بخورم.",
    "urd": "میں کانچ کھا سکتا ہوں اور مجھے تکلیف نہیں ہوتی۔",
}


def warn(msg: str) -> None:
    print(f"site_data: warning: {msg}", file=sys.stderr)


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT.parent.parent))
    except ValueError:
        return str(p)


# --------------------------------------------------------------------------- discovery

def find_variable(fid: str, stem: str) -> tuple[Path | None, Path | None]:
    """Return (upright, italic) variable TTF paths for a family, or (None, None)."""
    candidates = [
        (ROOT / "fonts" / stem / "variable", "ttf"),
        (ROOT / "build" / fid / "variable", "ttf"),
        (PUBLIC / "fonts" / stem / "variable", "woff2"),
    ]
    for d, ext in candidates:
        if not d.is_dir():
            continue
        ups = sorted(p for p in d.glob(f"{stem}[[]*].{ext}"))
        if not ups:
            continue
        itals = sorted(p for p in d.glob(f"{stem}-Italic[[]*].{ext}"))
        return ups[0], (itals[0] if itals else None)
    return None, None


# --------------------------------------------------------------------------- font facts

def name_of(font: TTFont, name_id: int | None) -> str | None:
    if name_id is None:
        return None
    rec = font["name"].getDebugName(name_id)
    return rec or None


def axes_of(font: TTFont) -> list[dict]:
    if "fvar" not in font:
        return []
    return [
        {
            "tag": a.axisTag,
            "name": name_of(font, a.axisNameID) or a.axisTag,
            "min": a.minValue, "default": a.defaultValue, "max": a.maxValue,
        }
        for a in font["fvar"].axes
    ]


def instances_of(font: TTFont) -> list[dict]:
    if "fvar" not in font:
        return []
    out = []
    for inst in font["fvar"].instances:
        out.append({
            "name": name_of(font, inst.subfamilyNameID) or "",
            "coords": {k: round(v, 2) for k, v in inst.coordinates.items()},
            "psName": name_of(font, inst.postscriptNameID) if inst.postscriptNameID not in (None, 0xFFFF) else None,
        })
    return out


def metrics_of(font: TTFont) -> dict:
    os2 = font["OS/2"]
    hhea = font["hhea"]
    return {
        "upm": font["head"].unitsPerEm,
        "ascender": hhea.ascent,
        "descender": hhea.descent,
        "lineGap": hhea.lineGap,
        "xHeight": getattr(os2, "sxHeight", None),
        "capHeight": getattr(os2, "sCapHeight", None),
        "italicAngle": font["post"].italicAngle,
    }


def _lookup_subtables(lookup):
    for st in lookup.SubTable:
        if lookup.LookupType == 7:  # extension: unwrap
            yield st.ExtensionLookupType, st.ExtSubTable
        else:
            yield lookup.LookupType, st


def _nested_lookups(table, idx: int, seen: set[int]) -> list[int]:
    """Lookup idx plus any lookups referenced by contextual subtables (type 5/6)."""
    if idx in seen:
        return []
    seen.add(idx)
    out = [idx]
    lookup = table.LookupList.Lookup[idx]
    for ltype, st in _lookup_subtables(lookup):
        if ltype not in (5, 6):
            continue
        recs = []
        for attr in ("SubstLookupRecord",):
            recs += list(getattr(st, attr, None) or [])
        for rs_attr in ("SubRuleSet", "SubClassSet", "ChainSubRuleSet", "ChainSubClassSet"):
            for rs in getattr(st, rs_attr, None) or []:
                if rs is None:
                    continue
                for rule_attr in ("SubRule", "SubClassRule", "ChainSubRule", "ChainSubClassRule"):
                    for rule in getattr(rs, rule_attr, None) or []:
                        recs += list(getattr(rule, "SubstLookupRecord", None) or [])
        for r in recs:
            out += _nested_lookups(table, r.LookupListIndex, seen)
    return out


def gsub_map(font: TTFont, cmap: dict[int, str]) -> tuple[dict[str, tuple[str, str]], dict[str, set[str]]]:
    """Map unencoded glyph -> (text, feature) and feature -> set of affected input chars."""
    rev: dict[str, str] = {}
    for cp, g in sorted(cmap.items()):
        rev.setdefault(g, chr(cp))
    reach: dict[str, tuple[str, str]] = {}
    affected: dict[str, set[str]] = {}
    if "GSUB" not in font:
        return reach, affected
    table = font["GSUB"].table
    if not table.FeatureList or not table.LookupList:
        return reach, affected
    # (feature tag, lookup indices) – include nested contextual lookups
    feats: list[tuple[str, list[int]]] = []
    for fr in table.FeatureList.FeatureRecord:
        idxs: list[int] = []
        seen: set[int] = set()
        for li in fr.Feature.LookupListIndex:
            idxs += _nested_lookups(table, li, seen)
        feats.append((fr.FeatureTag, idxs))
    # priority: user-facing features first so a.ss01 is attributed to ss01, not aalt/ccmp
    def prio(tag: str) -> int:
        if tag in ("aalt", "ccmp", "rvrn"):
            return 2
        if tag == "locl":
            return 1
        return 0
    feats.sort(key=lambda ft: prio(ft[0]))

    def text_for(g: str) -> str | None:
        if g in rev:
            return rev[g]
        if g in reach:
            return reach[g][0]
        return None

    for _pass in range(3):  # a few passes so chains (a -> a.ss01 -> a.ss01.sc) resolve
        for tag, idxs in feats:
            for li in idxs:
                lookup = table.LookupList.Lookup[li]
                for ltype, st in _lookup_subtables(lookup):
                    pairs: list[tuple[list[str], str]] = []
                    if ltype == 1:
                        pairs = [([a], b) for a, b in (st.mapping or {}).items()]
                    elif ltype == 3:
                        for a, alts in (st.alternates or {}).items():
                            pairs += [([a], b) for b in alts]
                    elif ltype == 4:
                        for first, ligs in (st.ligatures or {}).items():
                            for lig in ligs:
                                pairs.append(([first] + list(lig.Component), lig.LigGlyph))
                    elif ltype == 2:
                        for a, seq in (st.mapping or {}).items():
                            for b in seq:
                                if b != a:
                                    pairs.append(([a], b))
                    for src, dst in pairs:
                        texts = [text_for(s) for s in src]
                        if any(t is None for t in texts):
                            continue
                        txt = "".join(texts)  # type: ignore[arg-type]
                        if prio(tag) == 0 and len(src) == 1 and src[0] in rev:
                            affected.setdefault(tag, set()).add(rev[src[0]])
                        elif prio(tag) == 0 and len(src) > 1:
                            affected.setdefault(tag, set()).add(txt)
                        if dst not in rev and dst not in reach:
                            reach[dst] = (txt, tag)
    return reach, affected


def features_of(font: TTFont, affected: dict[str, set[str]]) -> tuple[list[dict], list[dict]]:
    feats: dict[str, dict] = {}
    locl: dict[str, dict] = {}
    for tbl in ("GSUB", "GPOS"):
        if tbl not in font or not font[tbl].table.FeatureList:
            continue
        t = font[tbl].table
        for fr in t.FeatureList.FeatureRecord:
            tag = fr.FeatureTag
            entry = feats.setdefault(tag, {"tag": tag, "tables": [], "label": None})
            if tbl not in entry["tables"]:
                entry["tables"].append(tbl)
            params = fr.Feature.FeatureParams
            if params is not None:
                nid = getattr(params, "UINameID", None) or getattr(params, "FeatUILabelNameID", None)
                label = name_of(font, nid) if nid else None
                if label:
                    entry["label"] = label
        # locl languages
        if tbl == "GSUB" and t.ScriptList:
            try:
                import uharfbuzz as hb  # optional
            except Exception:  # pragma: no cover
                hb = None
            locl_idx = {i for i, fr in enumerate(t.FeatureList.FeatureRecord) if fr.FeatureTag == "locl"}
            for sr in t.ScriptList.ScriptRecord:
                for lsr in sr.Script.LangSysRecord:
                    if not locl_idx.intersection(lsr.LangSys.FeatureIndex):
                        continue
                    ot = str(lsr.LangSysTag)
                    bcp = None
                    if hb is not None:
                        try:
                            bcp = hb.ot_tag_to_language(str(ot))
                        except Exception:
                            bcp = None
                    if not bcp:
                        bcp = ot.strip().lower()
                    locl.setdefault(ot, {"otTag": ot.strip(), "lang": bcp, "script": sr.ScriptTag.strip()})
    out = []
    for tag in sorted(feats):
        e = feats[tag]
        chars = sorted(affected.get(tag, set()), key=lambda s: (len(s), s))
        out.append({
            "tag": tag,
            "tables": e["tables"],
            "name": FEATURE_NAMES.get(tag, tag),
            "label": e["label"] or SS_NAMES.get(tag),
            "toggle": tag not in HIDDEN_FEATURES,
            "chars": "".join(c for c in chars if len(c) == 1)[:64],
            "sequences": [c for c in chars if len(c) > 1][:48],
        })
    return out, sorted(locl.values(), key=lambda d: (d["script"], d["lang"]))


def category_of(cp: int) -> str:
    if 0xAC00 <= cp <= 0xD7A3:
        return "Hangul syllables"
    if 0x1100 <= cp <= 0x11FF or 0x3130 <= cp <= 0x318F or 0xA960 <= cp <= 0xA97F or 0xD7B0 <= cp <= 0xD7FF:
        return "Hangul jamo"
    if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xF900 <= cp <= 0xFAFF
            or 0x20000 <= cp <= 0x3134F):
        return "Ideographs"
    if 0x2500 <= cp <= 0x257F:
        return "Box drawing"
    if 0x2580 <= cp <= 0x259F or 0x25A0 <= cp <= 0x25FF:
        return "Blocks & shapes"
    if 0x2190 <= cp <= 0x21FF or 0x27F0 <= cp <= 0x27FF or 0x2900 <= cp <= 0x297F:
        return "Arrows"
    cat = unicodedata.category(chr(cp))
    if cat == "Lu" or cat == "Lt":
        return "Uppercase"
    if cat == "Ll":
        return "Lowercase"
    if cat in ("Lo", "Lm"):
        return "Letters"
    if cat[0] == "N":
        return "Numbers"
    if cat[0] == "P":
        return "Punctuation"
    if cat == "Sc":
        return "Currency"
    if cat == "Sm":
        return "Math"
    if cat[0] == "S":
        return "Symbols"
    if cat[0] == "M":
        return "Marks"
    return "Spaces & controls"


def script_of(cp: int) -> str:
    try:
        name = ftu.script_name(ftu.script(chr(cp)))
    except Exception:
        return "Common"
    return {"Common": "Common", "Inherited": "Common"}.get(name, name)


def glyphs_of(font: TTFont, cmap: dict[int, str], reach: dict[str, tuple[str, str]]) -> list[dict]:
    hmtx = font["hmtx"].metrics
    by_glyph: dict[str, list[int]] = {}
    for cp, g in cmap.items():
        by_glyph.setdefault(g, []).append(cp)
    out = []
    for g in font.getGlyphOrder():
        adv = hmtx.get(g, (0, 0))[0]
        cps = sorted(by_glyph.get(g, []))
        if cps:
            cp = cps[0]
            cat = category_of(cp)
            entry = {"n": g, "u": cp, "c": cat, "s": script_of(cp), "a": adv}
            if len(cps) > 1:
                entry["alt"] = cps[1:]
            out.append(entry)
            continue
        if g in reach:
            txt, feat = reach[g]
            base_cp = ord(txt[0])
            if len(txt) > 1 and all(unicodedata.category(c)[0] != "M" for c in txt):
                cat = "Ligatures"
            elif unicodedata.category(txt[0])[0] == "M":
                cat = "Marks"
            else:
                cat = "Alternates"
            out.append({"n": g, "u": None, "c": cat, "s": script_of(base_cp), "a": adv,
                        "t": txt, "f": feat})
            continue
        out.append({"n": g, "u": None, "c": "Unencoded", "s": "Common", "a": adv})
    return out


# --------------------------------------------------------------------------- languages

def languages_of(path: Path) -> dict:
    try:
        from hyperglot.checker import FontChecker
        from hyperglot.languages import Languages  # noqa: F401  (import check)
    except Exception as e:  # pragma: no cover
        warn(f"hyperglot unavailable ({e}); skipping languages")
        return {"count": 0, "scripts": [], "error": "hyperglot unavailable"}
    try:
        support = FontChecker(str(path)).get_supported_languages()
    except Exception as e:
        warn(f"hyperglot failed on {rel(path)}: {e}")
        return {"count": 0, "scripts": [], "error": str(e)}
    isos: set[str] = set()
    scripts = []
    for script, langs in support.items():
        rows = []
        for iso, lang in langs.items():
            isos.add(iso)
            try:
                name = lang.get_name(script) or lang.name
            except Exception:
                name = getattr(lang, "name", iso)
            try:
                autonym = lang.get_autonym(script) or ""
            except Exception:
                autonym = ""
            try:
                speakers = lang.speakers or 0
            except Exception:
                speakers = 0
            alphabet = ""
            try:
                orth = lang.get_orthography(script)
                if orth:
                    base = [c for c in orth.base if c.strip()]
                    lower = [c for c in base if len(c) == 1 and c == c.lower() and c != c.upper()]
                    letters = lower or base
                    alphabet = " ".join(letters)[:160]
            except Exception:
                pass
            row = {"iso": iso, "name": name, "autonym": autonym if autonym != name else autonym,
                   "speakers": speakers, "alphabet": alphabet}
            if iso in SAMPLES:
                row["sample"] = SAMPLES[iso]
            rows.append(row)
        rows.sort(key=lambda r: (-(r["speakers"] or 0), r["name"]))
        scripts.append({"script": script, "count": len(rows), "languages": rows})
    scripts.sort(key=lambda s: -s["count"])
    return {"count": len(isos), "scripts": scripts}


# --------------------------------------------------------------------------- script coverage

def _assigned(start: int, end: int) -> int:
    """Number of assigned code points in [start, end] (Unicode data from unicodedata2 if present)."""
    try:
        import unicodedata2 as ud
    except Exception:  # pragma: no cover
        ud = unicodedata
    n = 0
    for cp in range(start, end + 1):
        if ud.category(chr(cp)) not in ("Cn", "Cs", "Co"):
            n += 1
    return n


def coverage_of(cmap: dict[int, str]) -> dict:
    """Encoded code points per Unicode script and per Unicode block.

    Hyperglot reports few or no languages for CJK fonts (it needs every character of an
    orthography), so the site also shows raw coverage: "11,172 Hangul syllables",
    "3,500 CJK ideographs", "Arabic: 256 characters" and so on.
    """
    from fontTools.unicodedata import Blocks
    import bisect
    scripts: dict[str, int] = {}
    blocks: dict[int, int] = {}
    for cp in cmap:
        s = script_of(cp)
        scripts[s] = scripts.get(s, 0) + 1
        i = bisect.bisect_right(Blocks.RANGES, cp) - 1
        blocks[i] = blocks.get(i, 0) + 1
    block_rows = []
    for i, count in sorted(blocks.items()):
        name = Blocks.VALUES[i]
        if name == "No_Block":
            continue
        start = Blocks.RANGES[i]
        end = (Blocks.RANGES[i + 1] - 1) if i + 1 < len(Blocks.RANGES) else 0x10FFFF
        block_rows.append({"name": name, "start": start, "end": end, "count": count,
                           "assigned": _assigned(start, end)})
    return {
        "codepoints": len(cmap),
        "scripts": [{"script": k, "count": v} for k, v in sorted(scripts.items(), key=lambda kv: -kv[1])],
        "blocks": block_rows,
    }


# --------------------------------------------------------------------------- files

def files_of(stem: str) -> dict:
    """Formats in the dist (fonts/<PS>/<fmt>) plus web files and zips already in apps/docs/public.

    Paths are relative to the website root (apps/docs/public), without a leading slash."""
    formats = {}
    for fmt in FORMATS:
        d = ROOT / "fonts" / stem / fmt
        if not d.is_dir():
            continue
        files = sorted(p for p in d.iterdir() if p.is_file() and not p.name.startswith("."))
        formats[fmt] = {
            "count": len(files),
            "bytes": sum(p.stat().st_size for p in files),
            "files": [{"name": p.name, "bytes": p.stat().st_size} for p in files],
        }
    web = []
    for sub in ("variable", "woff2"):
        d = PUBLIC / "fonts" / stem / sub
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.woff2")):
            web.append({"path": p.relative_to(PUBLIC).as_posix(), "name": p.name, "bytes": p.stat().st_size,
                        "variable": sub == "variable"})
    z = PUBLIC / "downloads" / f"{stem}.zip"
    zip_info = {"path": z.relative_to(PUBLIC).as_posix(), "bytes": z.stat().st_size} if z.is_file() else None
    return {"formats": formats, "web": web, "zip": zip_info}


# --------------------------------------------------------------------------- dev helper

def dev_populate(stem: str, upright: Path, italic: Path | None) -> None:
    """Convert VF TTFs to WOFF2 in apps/docs/public/fonts/<PS>/variable (dev preview only;
    tools/postprocess.py does this for releases). Also refreshes the combined stylesheet."""
    out = PUBLIC / "fonts" / stem / "variable"
    out.mkdir(parents=True, exist_ok=True)
    for src in (upright, italic):
        if src is None or src.suffix != ".ttf":
            continue
        dst = out / (src.stem + ".woff2")
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            continue
        f = TTFont(str(src))
        f.flavor = "woff2"
        f.save(str(dst))
        print(f"site_data: dev: wrote {rel(dst)}")


# --------------------------------------------------------------------------- main

def build_family(fid: str, stem: str, display: str, blurb: str, args) -> dict | None:
    upright, italic = find_variable(fid, stem)
    if upright is None:
        print(f"site_data: {display}: not built yet (no fonts/{stem}/variable, build/{fid}/variable "
              f"or apps/docs/public/fonts/{stem}/variable) — skipping")
        return None
    if args.dev_fonts:
        dev_populate(stem, upright, italic)
    font = TTFont(str(upright))
    cmap = font.getBestCmap() or {}
    reach, affected = gsub_map(font, cmap)
    features, locl = features_of(font, affected)
    glyphs = glyphs_of(font, cmap, reach)
    langs = {"count": 0, "scripts": [], "skipped": True} if args.no_languages else languages_of(upright)
    files = files_of(stem)
    cats: dict[str, int] = {}
    for g in glyphs:
        cats[g["c"]] = cats.get(g["c"], 0) + 1
    glyph_scripts = sorted({g["s"] for g in glyphs if g["s"] != "Common"})
    fam_def = _FAMILY_DEFS[fid]
    data = {
        "id": fid,
        "style": fam_def.style,
        "family": name_of(font, 16) or name_of(font, 1) or display,
        "cssFamily": display,
        "fileStem": stem,
        "blurb": blurb,
        "version": (name_of(font, 5) or "").replace("Version ", ""),
        "source": rel(upright),
        "italicSource": rel(italic) if italic else None,
        "hasItalic": italic is not None,
        "generated": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "web": has_web(stem),
        "metrics": metrics_of(font),
        "axes": axes_of(font),
        "instances": instances_of(font),
        "features": features,
        "locl": locl,
        "categories": [{"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda kv: -kv[1])],
        "glyphScripts": glyph_scripts,
        "glyphs": glyphs,
        "languages": langs,
        "coverage": coverage_of(cmap),
        "files": files,
        "counts": {
            "glyphs": len(glyphs),
            "encoded": len(cmap),
            "features": len([f for f in features if f["toggle"]]),
            "languages": langs.get("count", 0),
            "scripts": len(langs.get("scripts", [])),
            "instances": len(instances_of(font)),
        },
    }
    return data


def has_web(stem: str) -> bool:
    """True when the website has this family's variable WOFF2 (apps/docs/public/fonts/<PS>/variable)."""
    d = PUBLIC / "fonts" / stem / "variable"
    return d.is_dir() and any(d.glob(f"{stem}[[]*].woff2"))


def summary(data: dict) -> dict:
    cov = data["coverage"]
    return {"id": data["id"], "family": data["family"], "cssFamily": data["cssFamily"], "fileStem": data["fileStem"],
            "style": data["style"], "version": data["version"], "web": has_web(data["fileStem"]),
            "counts": data["counts"], "axes": data["axes"],
            "hasItalic": data["hasItalic"], "scripts": cov["scripts"],
            "blocks": [b for b in cov["blocks"] if b["count"] >= 32],
            "zip": data["files"]["zip"]}


HAN_LANGUAGE_MIN = 2500     # common hanzi needed to count Chinese as supported
KANJI_LANGUAGE_MIN = 2000   # Jōyō-level kanji (plus full kana) to count Japanese


CHARACTER_LANGUAGES = {  # languages Hyperglot does not evaluate, counted from character coverage
    "cmn": {"iso": "cmn", "name": "Chinese (Simplified)", "autonym": "简体中文", "speakers": 1_100_000_000,
            "alphabet": "", "sample": SAMPLES["cmn"], "script": "Han"},
    "jpn": {"iso": "jpn", "name": "Japanese", "autonym": "日本語", "speakers": 123_000_000,
            "alphabet": "あ い う え お ア イ ウ エ オ", "sample": SAMPLES["jpn"], "script": "Kana"},
}
# Which family a language is shown (and tested) in when several families support it.
_LANG_ORDER = ["sans", "mono", "pixel"]


def totals_of(ids: list[str]) -> tuple[dict, dict]:
    """Headline numbers for the whole collection, de-duplicated across families:
    unique characters, unique languages (Hyperglot ISO codes, plus Chinese when the
    hanzi coverage supports it — Hyperglot does not evaluate Chinese), and scripts.
    Also returns those languages as one list (languages.json), each row naming the
    first family that supports it and every family that does."""
    chars: set[int] = set()
    isos: set[str] = set()
    rows: dict[str, dict] = {}
    order: dict[str, list[str]] = {}
    scripts: set[str] = set()
    statics = variables = 0
    han = 0
    han_family = None
    japanese = None
    ids = sorted(ids, key=lambda i: _LANG_ORDER.index(i) if i in _LANG_ORDER else len(_LANG_ORDER))
    for fid in ids:
        meta = json.loads((DATA / f"{fid}.json").read_text(encoding="utf-8"))
        glyphs = json.loads((DATA / f"{fid}.glyphs.json").read_text(encoding="utf-8"))["glyphs"]
        fam_han = 0
        fam_kana = 0
        for g in glyphs:
            u = g.get("u")
            if u is None:
                continue
            chars.add(u)
            if g.get("s") not in ("Common", "Inherited", None):
                scripts.add(g["s"])
            if g.get("s") == "Han":
                fam_han += 1
            if g.get("s") in ("Hiragana", "Katakana"):
                fam_kana += 1
        if fam_kana >= 150 and fam_han >= KANJI_LANGUAGE_MIN and japanese is None:
            japanese = fid
        if not fid.endswith("-jp") and fam_han > han:
            han, han_family = fam_han, fid
        for sc in meta.get("languages", {}).get("scripts", []):
            for row in sc.get("languages", []):
                isos.add(row["iso"])
                key = f"{sc['script']}:{row['iso']}"
                if key not in rows:
                    rows[key] = {**row, "family": fid, "families": []}
                    order.setdefault(sc["script"], []).append(key)
                rows[key]["families"].append(fid)
        n = len(meta.get("instances", []))
        statics += n * (2 if meta.get("hasItalic") else 1)
        variables += 2 if meta.get("hasItalic") else 1
    chinese = han >= HAN_LANGUAGE_MIN
    for iso, fid in (("cmn", han_family if chinese else None), ("jpn", japanese)):
        if not fid:
            continue
        isos.add(iso)
        row = dict(CHARACTER_LANGUAGES[iso])
        script = row.pop("script")
        rows[f"{script}:{iso}"] = {**row, "family": fid, "families": [fid]}
        order.setdefault(script, []).append(f"{script}:{iso}")
    # a handful of Han characters (e.g. in enclosed forms) don't make a Han script family
    if not chinese and han < 100:
        scripts.discard("Han")
    scripts_out = []
    for script, keys in order.items():
        langs = sorted((rows[k] for k in keys), key=lambda r: (-(r["speakers"] or 0), r["name"]))
        scripts_out.append({"script": script, "count": len(langs), "languages": langs})
    scripts_out.sort(key=lambda sc: -sc["count"])
    languages = {"count": len(isos), "scripts": scripts_out}
    return {
        "families": len(ids),
        "characters": len(chars),
        "languages": len(isos),
        "languagesNote": "Hyperglot, unique languages" + "".join(
            [f"; {n} counted from character coverage" for n, ok in (("Chinese", chinese), ("Japanese", japanese)) if ok]),
        "scripts": sorted(scripts),
        "staticFonts": statics,
        "variableFonts": variables,
    }, languages


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dev-fonts", action="store_true",
                    help="convert variable TTFs to WOFF2 in apps/docs/public/fonts (for local preview)")
    ap.add_argument("--no-languages", action="store_true", help="skip hyperglot language detection")
    ap.add_argument("--only", choices=[f[0] for f in FAMILIES], action="append",
                    help="only process this family (repeatable)")
    args = ap.parse_args(argv)

    DATA.mkdir(parents=True, exist_ok=True)
    built: dict[str, dict] = {}
    for fid, stem, display, blurb in FAMILIES:
        if args.only and fid not in args.only:
            continue
        try:
            data = build_family(fid, stem, display, blurb, args)
        except Exception as e:  # never let one broken font kill the whole site build
            warn(f"{display}: failed: {e!r} — skipping")
            data = None
        out = DATA / f"{fid}.json"
        out_glyphs = DATA / f"{fid}.glyphs.json"
        if data is None:
            for p in (out, out_glyphs):
                if p.exists():
                    p.unlink()
            continue
        glyphs = data.pop("glyphs")
        out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        out_glyphs.write_text(json.dumps({"id": fid, "glyphs": glyphs}, ensure_ascii=False, separators=(",", ":")),
                              encoding="utf-8")
        c = data["counts"]
        top = ", ".join(f"{s['count']} {s['script']}" for s in data["coverage"]["scripts"][:4])
        print(f"site_data: {display}: {c['glyphs']} glyphs ({top}), {c['features']} features, "
              f"{c['languages']} languages in {c['scripts']} scripts -> {rel(out)}")
        built[fid] = summary(data)

    # Families not regenerated this run (--only) keep their previous summaries.
    old: dict = {}
    if (DATA / "index.json").exists():
        try:
            old = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
        except Exception:
            old = {}
    if args.only:
        for f in old.get("families", []):
            if f.get("id") not in built and f.get("id") not in args.only and (DATA / f"{f.get('id')}.json").exists():
                built[f["id"]] = f
    index = {
        "generated": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "catalog": [
            {"id": fid, "name": f.name, "ps": f.ps, "style": f.style, "italic": f.italic,
             "packs": list(f.packs), "built": fid in built, "web": has_web(f.ps)}
            for fid, f in _FAMILY_DEFS.items()
        ],
        "families": [built[fid] for fid in _FAMILY_DEFS if fid in built],
    }
    index["totals"], languages = totals_of([fid for fid in _FAMILY_DEFS if fid in built])
    (DATA / "languages.json").write_text(json.dumps(languages, ensure_ascii=False, separators=(",", ":")),
                                         encoding="utf-8")
    allzip = PUBLIC / "downloads" / "Bloxwap-Fonts.zip"
    index["zip"] = {"path": "downloads/Bloxwap-Fonts.zip", "bytes": allzip.stat().st_size} if allzip.is_file() else None
    (DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    if not index["families"]:
        warn("no families found; the website will show placeholders")
    if args.dev_fonts:
        try:
            import webfonts
            webfonts.write_css(PUBLIC)
        except Exception as e:  # pragma: no cover
            warn(f"could not refresh the combined stylesheet: {e!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
