"""OpenType feature code, generated from glyph-name conventions.

Suffix conventions:
    .ssNN   stylistic set NN          .cvNN   character variant NN
    .pnum   proportional figure       .zero   slashed zero
    .sups   superior                  .subs   inferior (also sinf)
    .numr   numerator                 .dnom   denominator
    .case   case-sensitive form       .sc     small capital
    a_b     ligature of a + b (liga; .code => calt code ligature in Mono)
    .loclXXX  localized form for language tag XXX
"""
from __future__ import annotations

import re

SS_NAMES = {
    "ss01": "Single-storey a",
    "ss02": "Open digits",
    "ss03": "Round dots & quotes",
    "ss04": "y with curved tail",
    "ss05": "Simplified capitals (G, R, Q)",
    "ss06": "Flat-top 3 and 1 without flag",
    "ss07": "Square punctuation",
    "ss08": "Circled & disambiguation (Il1 0O)",
}


def glyph_order(outs):
    first = [n for n in (".notdef", "space") if n in outs]

    def key(n):
        o = outs[n]
        if o.unicodes:
            return (0, min(o.unicodes), n)
        base = n.split(".")[0].split("_")[0]
        bo = outs.get(base)
        bu = min(bo.unicodes) if bo and bo.unicodes else 0x10FFFF
        return (1, bu, n)

    rest = sorted((n for n in outs if n not in first), key=key)
    return first + rest


def _pairs(names, suffix):
    out = []
    for n in sorted(names):
        if n.endswith(suffix):
            base = n[: -len(suffix)]
            if base in names:
                out.append((base, n))
    return out


FEATURE_HOOKS = []   # callables(family, outs) -> (langsys list, fea code) or None


def make_features(family, outs, italic=False):
    fobj = family if not isinstance(family, str) else None
    family = fobj.style if fobj is not None else family
    names = set(outs)
    hooks = [h(fobj, outs) for h in FEATURE_HOOKS] if fobj is not None else []
    hooks = [h for h in hooks if h]
    marks = sorted(n for n, o in outs.items() if o.kind == "mark")
    top_marks = [n for n in marks if "_top" in outs[n].anchors]
    fea = []
    fea.append("languagesystem DFLT dflt;")
    for script, langs in (("latn", ["dflt", "TRK", "AZE", "CRT", "KAZ", "TAT", "ROM", "MOL", "CAT", "NLD"]),
                          ("grek", ["dflt"]), ("cyrl", ["dflt", "SRB", "MKD", "BGR"])):
        for l in langs:
            fea.append(f"languagesystem {script} {l};")
    for ls, _code in hooks:
        for script, l in ls:
            fea.append(f"languagesystem {script} {l};")
    fea.append("")
    for _ls, code in hooks:
        fea.append(code)
        fea.append("")

    def sub_feature(tag, pairs, extra=""):
        if not pairs and not extra:
            return
        fea.append(f"feature {tag} {{")
        for a, b in pairs:
            fea.append(f"  sub {a} by {b};")
        if extra:
            fea.append(extra)
        fea.append(f"}} {tag};")
        fea.append("")

    # --- ccmp: soft-dotted i/j lose dots under top marks -------------------
    dotless = [(a, b) for a, b in (("i", "dotlessi"), ("j", "dotlessj")) if a in names and b in names]
    if dotless and top_marks:
        fea.append(f"@TopMarks = [{' '.join(top_marks)}];")
        fea.append("feature ccmp {")
        fea.append("  lookup ccmp_soft_dotted {")
        for a, b in dotless:
            fea.append(f"    sub {a}' @TopMarks by {b};")
        fea.append("  } ccmp_soft_dotted;")
        case_marks = [n for n in top_marks if n + ".case" in names]
        caps = [n for n, o in outs.items() if o.kind == "base" and o.unicodes and
                any(chr(u).isupper() for u in o.unicodes) and len(o.unicodes) >= 1]
        if case_marks and caps:
            fea.append(f"  @UC = [{' '.join(sorted(caps))}];")
            fea.append(f"  @MarksLC = [{' '.join(case_marks)}];")
            fea.append(f"  @MarksUC = [{' '.join(m + '.case' for m in case_marks)}];")
            fea.append("  lookup ccmp_case_marks {")
            fea.append("    sub @UC @MarksLC' by @MarksUC;")
            fea.append("  } ccmp_case_marks;")
        fea.append("} ccmp;")
        fea.append("")

    # --- locl ---------------------------------------------------------------
    locl = []
    if "scedilla" in names and "uni0219" in names:
        locl.append(("ROM", [("scedilla", "uni0219"), ("Scedilla", "uni0218"),
                              ("uni0163", "uni021B"), ("uni0162", "uni021A")]))
        locl.append(("MOL", [("scedilla", "uni0219"), ("Scedilla", "uni0218"),
                              ("uni0163", "uni021B"), ("uni0162", "uni021A")]))
    serb = sorted(n for n in names if n.endswith(".loclSRB"))
    bgr = sorted(n for n in names if n.endswith(".loclBGR"))
    if locl or serb or bgr:
        fea.append("feature locl {")
        for lang, pairs in locl:
            pairs = [(a, b) for a, b in pairs if a in names and b in names]
            fea.append("  script latn;")
            fea.append(f"  language {lang} exclude_dflt;")
            for a, b in pairs:
                fea.append(f"    sub {a} by {b};")
        if "periodcentered" in names and "l" in names:
            fea.append("  script latn;")
            fea.append("  language CAT exclude_dflt;")
            fea.append("    sub l periodcentered' l by periodcentered.loclCAT;" if "periodcentered.loclCAT" in names else "")
        for lang, lst in (("SRB", serb), ("MKD", serb), ("BGR", bgr)):
            if lst:
                fea.append("  script cyrl;")
                fea.append(f"  language {lang} exclude_dflt;")
                for n in lst:
                    base = n.rsplit(".", 1)[0]
                    if base in names:
                        fea.append(f"    sub {base} by {n};")
        fea.append("} locl;")
        fea.append("")

    # --- figures --------------------------------------------------------------
    sub_feature("pnum", _pairs(names, ".pnum"))
    sub_feature("zero", _pairs(names, ".zero"))
    for tag, suf in (("sups", ".sups"), ("subs", ".subs"), ("sinf", ".subs"), ("numr", ".numr"), ("dnom", ".dnom")):
        sub_feature(tag, _pairs(names, suf))
    nd = sorted(set(a for a, _ in _pairs(names, ".numr")) & set(a for a, _ in _pairs(names, ".dnom")))
    numr = [(a, a + ".numr") for a in nd]
    dnom = [(a, a + ".dnom") for a in nd]
    if numr and dnom and "fraction" in names:
        fea.append("feature frac {")
        fea.append(f"  @FigDefault = [{' '.join(a for a, _ in numr)}];")
        fea.append(f"  @FigNumr = [{' '.join(b for _, b in numr)}];")
        fea.append(f"  @FigDnom = [{' '.join(b for _, b in dnom)}];")
        fea.append("  lookup frac_numr { sub @FigDefault by @FigNumr; } frac_numr;")
        fea.append("  lookup frac_slash { sub [slash fraction] by fraction; } frac_slash;")
        fea.append("  lookup frac_dnom { sub [fraction @FigDnom] @FigNumr' by @FigDnom; } frac_dnom;")
        fea.append("} frac;")
        fea.append("")
    # ordinals
    if "ordfeminine" in names and "ordmasculine" in names:
        fea.append("feature ordn {")
        fea.append("  sub [zero one two three four five six seven eight nine] [A a]' by ordfeminine;")
        fea.append("  sub [zero one two three four five six seven eight nine] [O o]' by ordmasculine;")
        fea.append("} ordn;")
        fea.append("")

    # --- case -----------------------------------------------------------------
    case_pairs = [(a, b) for a, b in _pairs(names, ".case") if outs[a].kind != "mark"]
    sub_feature("case", case_pairs)

    # --- small caps -------------------------------------------------------------
    sc = _pairs({n.replace(".sc", "").lower() + ".sc" if n.endswith(".sc") else n for n in names}, ".sc")
    smcp = []
    c2sc = []
    for n in sorted(names):
        if n.endswith(".sc"):
            base = n[:-3]
            # base is the lowercase glyph name; uppercase counterpart via unicode
            if base in names:
                smcp.append((base, n))
                o = outs[base]
                for u in o.unicodes:
                    up = chr(u).upper()
                    if len(up) == 1:
                        for cand, oo in outs.items():
                            if ord(up) in oo.unicodes and ord(up) != u:
                                c2sc.append((cand, n))
                                break
    sub_feature("smcp", smcp)
    sub_feature("c2sc", c2sc)

    # --- stylistic sets / character variants ---------------------------------
    for i in range(1, 21):
        tag = f"ss{i:02d}"
        pairs = [(n.split(".")[0] if n.count(".") == 1 else n.rsplit(".", 1)[0], n)
                 for n in sorted(names) if n.endswith("." + tag)]
        pairs = [(a, b) for a, b in pairs if a in names]
        if pairs:
            fea.append(f"feature {tag} {{")
            if tag in SS_NAMES:
                fea.append(f'  featureNames {{ name "{SS_NAMES[tag]}"; }};')
            for a, b in pairs:
                fea.append(f"  sub {a} by {b};")
            fea.append(f"}} {tag};")
            fea.append("")
    for i in range(1, 100):
        tag = f"cv{i:02d}"
        pairs = [(n.rsplit(".", 1)[0], n) for n in sorted(names) if n.endswith("." + tag)]
        pairs = [(a, b) for a, b in pairs if a in names]
        if pairs:
            sub_feature(tag, pairs)

    # --- ligatures --------------------------------------------------------------
    ligs = []
    code = []
    for n in sorted(names):
        base = n.split(".")[0]
        if "_" in base and outs[n].kind != "mark" and not base.endswith("comb") and "comb_" not in base:
            parts = base.split("_")
            if all(p in names for p in parts):
                (code if n.endswith(".code") else ligs).append((parts, n))
    if ligs:
        fea.append("feature liga {")
        for parts, n in sorted(ligs, key=lambda x: -len(x[0])):
            fea.append(f"  sub {' '.join(parts)} by {n};")
        fea.append("} liga;")
        fea.append("")
    if code:
        fea.append("feature calt {")
        for parts, n in sorted(code, key=lambda x: -len(x[0])):
            fea.append(f"  sub {' '.join(parts)} by {n};")
        fea.append("} calt;")
        fea.append("")
    # arrows in sans via calt
    arrows = [(p, n) for p, n in [(["hyphen", "greater"], "arrowright"), (["less", "hyphen"], "arrowleft"),
                                  (["less", "hyphen", "greater"], "arrowboth"),
                                  (["equal", "greater"], "uni21D2")] if n in names and all(x in names for x in p)]
    if arrows and family == "sans":
        fea.append("feature dlig {")
        for p, n in sorted(arrows, key=lambda x: -len(x[0])):
            fea.append(f"  sub {' '.join(p)} by {n};")
        fea.append("} dlig;")
        fea.append("")
    return "\n".join(l for l in fea if l is not None)
