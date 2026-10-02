"""Han (CJK ideograph) composition engine.

Characters are assembled from *components* following Ideographic
Description Sequences (IDS).  Components are drawn once as stroke skeletons
in a 1000×1000 unit box (SVG convention: origin top-left, y down) and are
re-stroked with the family pen wherever they are placed, so a component
squeezed into a narrow left-side slot keeps the same stroke weight as a
full-size one (the property that makes stroke-based CJK construction work).

Component definition (see components_*.py):

    comp("口", "M150 150 L150 850", "M150 150 L850 150 L850 850", "M150 850 L850 850",
         solo=(0.72, 0.68))

Each string is ONE calligraphic stroke as an SVG path (M/L/Q/C, absolute).
Corners (L→L) become rounded joins; Q/C segments are smooth.
Optional:
    solo=(sx, sy)      size when the component stands alone as a character
    inner={"⿴": (x0, y0, x1, y1), ...}   inner box for enclosures
    share={"L": 0.32, "T": 0.4, ...}     preferred size share in a position
Positional variants are separate components named "<name>.L" (left of ⿰),
".R", ".T" (top of ⿱), ".B", ".M" (middle of ⿲/⿳) and are chosen
automatically when they exist.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
IDC = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")
ARITY = {c: 2 for c in IDC}
ARITY["⿲"] = ARITY["⿳"] = 3

# face box (skeleton coordinates are inset by half a stroke inside it)
FACE = (60.0, -58.0, 940.0, 818.0)


@dataclass
class Comp:
    name: str
    paths: list
    solo: tuple = None
    inner: dict = field(default_factory=dict)
    share: dict = field(default_factory=dict)
    segs: list = None          # parsed: list of strokes, each list of (kind, pts) in unit y-up


COMPONENTS: dict[str, Comp] = {}
DECOMP: dict[str, str] = {}
# Regional layers: decompositions that override DECOMP for one region
# (ids_jp*.txt -> LAYERS["jp"]).  Components may also have regional forms
# named "<name>@jp" (and "<name>@jp.L" etc.), preferred when drawing that region.
LAYERS: dict[str, dict[str, str]] = {"jp": {}}
_LAYER = [None]      # active layer while laying out / drawing


def comp(name, *paths, solo=None, inner=None, share=None):
    COMPONENTS[name] = Comp(name, list(paths), solo, dict(inner or {}), dict(share or {}))


TOKEN_STROKES: dict[str, int] = {}


def ids(text: str, layer: str | None = None):
    """Register decompositions: lines 'char<TAB>IDS'.  Comment lines start with
    '# ' (or are just '#'); inline comments follow ' # '.  Unencoded parts are
    written as {name}; their stroke counts can be declared in comments as
    {name}=N."""
    for line in text.splitlines():
        st = line.strip()
        if not st:
            continue
        if st == "#" or st.startswith("# ") or st.startswith("#\t"):
            for m in re.finditer(r"(\{[^}]+\}|[^\x00-\x7f])\s*=\s*(\d+)", st):
                TOKEN_STROKES[m.group(1)] = int(m.group(2))
            continue
        st = st.split(" # ", 1)[0].split("\t# ", 1)[0].strip()
        parts = st.split()
        if len(parts) >= 2:
            (LAYERS.setdefault(layer, {}) if layer else DECOMP)[parts[0]] = parts[1]


# --------------------------------------------------------------------------
# path parsing
# --------------------------------------------------------------------------

_TOK = re.compile(r"[MLQCmlqc]|-?\d+(?:\.\d+)?")


def parse_path(d: str):
    """SVG subset → list of segments ('line', p0, p1) / ('cubic', p0, c1, c2, p1),
    converted to y-up unit coordinates (y' = 1000 - y)."""
    toks = _TOK.findall(d)
    i = 0
    cur = None
    segs = []
    cmd = None
    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v
    def pt():
        x = num(); y = num()
        return (x, 1000.0 - y)
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t.upper(); i += 1
            if t.islower():
                raise ValueError(f"relative commands not supported: {d}")
        if cmd == "M":
            cur = pt(); cmd = "L"
        elif cmd == "L":
            p = pt(); segs.append(("line", cur, p)); cur = p
        elif cmd == "Q":
            c = pt(); p = pt()
            c1 = (cur[0] + (c[0] - cur[0]) * 2 / 3, cur[1] + (c[1] - cur[1]) * 2 / 3)
            c2 = (p[0] + (c[0] - p[0]) * 2 / 3, p[1] + (c[1] - p[1]) * 2 / 3)
            segs.append(("cubic", cur, c1, c2, p)); cur = p
        elif cmd == "C":
            c1 = pt(); c2 = pt(); p = pt()
            segs.append(("cubic", cur, c1, c2, p)); cur = p
        else:
            raise ValueError(f"bad path {d!r}")
    return segs


def _tan0(s):
    if s[0] == "line":
        a, b = s[1], s[2]
    else:
        a = s[1]
        b = s[2] if (abs(s[2][0] - s[1][0]) + abs(s[2][1] - s[1][1])) > 1e-6 else s[3]
    return _n(b[0] - a[0], b[1] - a[1])


def _tan1(s):
    if s[0] == "line":
        a, b = s[1], s[2]
    else:
        b = s[4]
        a = s[3] if (abs(s[4][0] - s[3][0]) + abs(s[4][1] - s[3][1])) > 1e-6 else s[2]
    return _n(b[0] - a[0], b[1] - a[1])


def _n(x, y):
    m = math.hypot(x, y)
    return (x / m, y / m) if m > 1e-9 else (0.0, 0.0)


def split_corners(segs, deg=25.0):
    """Split a stroke into tangent-continuous runs (corners → separate runs)."""
    runs = [[segs[0]]]
    c = math.cos(math.radians(deg))
    for a, b in zip(segs, segs[1:]):
        t1, t0 = _tan1(a), _tan0(b)
        if t1[0] * t0[0] + t1[1] * t0[1] < c:
            runs.append([b])
        else:
            runs[-1].append(b)
    return runs


def prepared(c: Comp):
    if c.segs is None:
        c.segs = [split_corners(parse_path(p)) for p in c.paths]
    return c.segs


# --------------------------------------------------------------------------
# IDS resolution and layout
# --------------------------------------------------------------------------

def parse_ids(s: str):
    """IDS string → tree: str (component/char/{token}) or (op, [children])."""
    pos = 0
    def node():
        nonlocal pos
        ch = s[pos]; pos += 1
        if ch in IDC:
            return (ch, [node() for _ in range(ARITY[ch])])
        if ch == "{":
            end = s.index("}", pos)
            tok = "{" + s[pos:end] + "}"
            pos = end + 1
            return tok
        return ch
    t = node()
    return t


def resolve(x, depth=0, stack=(), layer=None):
    """Expand a component/char into a tree whose leaves are COMPONENTS names.
    With a regional layer, its decompositions and '@layer' components win."""
    if isinstance(x, tuple):
        return (x[0], [resolve(c, depth + 1, stack, layer) for c in x[1]])
    lay = LAYERS.get(layer, {}) if layer else {}
    if layer and f"{x}@{layer}" in COMPONENTS:
        return f"{x}@{layer}"
    if x in lay and x not in stack and depth < 12:
        return resolve(parse_ids(lay[x]), depth + 1, stack + (x,), layer)
    if x in COMPONENTS:
        return x
    if x in DECOMP and x not in stack and depth < 12:
        return resolve(parse_ids(DECOMP[x]), depth + 1, stack + (x,), layer)
    raise KeyError(x)


def leaves(t):
    if isinstance(t, str):
        return [t]
    out = []
    for c in t[1]:
        out += leaves(c)
    return out


def _counts(name):
    """(#vertical-ish, #horizontal-ish, #strokes) of a component."""
    c = COMPONENTS[name]
    v = h = 0
    for runs in prepared(c):
        for run in runs:
            for s in run:
                a, b = s[1], s[-1]
                dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
                if dx + dy < 60:
                    continue
                if dy > dx * 1.2:
                    v += 1
                elif dx > dy * 1.2:
                    h += 1
                else:
                    v += 0.5
                    h += 0.5
    return v, h, len(c.paths)


def demand(t, axis):
    """How much room (relative) a subtree wants along axis 'x' or 'y'."""
    if isinstance(t, str):
        v, h, n = _counts(t)
        k = v if axis == "x" else h
        return 1.0 + k * 0.9 + n * 0.12
    op, kids = t
    ds = [demand(k, axis) for k in kids]
    if (op in "⿰⿲" and axis == "x") or (op in "⿱⿳" and axis == "y"):
        return sum(ds)
    if op in "⿰⿲⿱⿳⿻":
        return max(ds)
    return ds[0] * 0.5 + ds[1]     # enclosure: frame + inner


def _variant(name, pos):
    if pos and f"{name}.{pos}" in COMPONENTS:
        return f"{name}.{pos}"
    return name


GAP_FRAC = 0.095     # a split never spends more than this fraction of the box on its gap
_MIN_GAP = [0.0]     # set by build_char: stroke thickness + hairline


def _gap(gap, extent):
    return max(_MIN_GAP[0], min(gap, GAP_FRAC * extent))


def layout(t, box, gap, pos=None, out=None):
    """Assign skeleton boxes (y-up) to leaves. Returns list of (comp, box)."""
    if out is None:
        out = []
    x0, y0, x1, y1 = box
    if isinstance(t, str):
        out.append((_variant(t, pos), box))
        return out
    op, kids = t
    if op in "⿰⿲":
        poss = ["L", "R"] if op == "⿰" else ["L", "M", "R"]
        ds = [_share(k, p, "x") for k, p in zip(kids, poss)]
        tot = sum(ds)
        gg = _gap(gap, x1 - x0)
        avail = (x1 - x0) - gg * (len(kids) - 1)
        x = x0
        for k, d, p in zip(kids, ds, poss):
            w = avail * d / tot
            layout(k, (x, y0, x + w, y1), gap, p, out)
            x += w + gg
    elif op in "⿱⿳":
        poss = ["T", "B"] if op == "⿱" else ["T", "M", "B"]
        ds = [_share(k, p, "y") for k, p in zip(kids, poss)]
        tot = sum(ds)
        gg = _gap(gap, y1 - y0)
        avail = (y1 - y0) - gg * (len(kids) - 1)
        y = y1
        for k, d, p in zip(kids, ds, poss):
            h = avail * d / tot
            layout(k, (x0, y - h, x1, y), gap, p, out)
            y -= h + gg
    elif op == "⿻":
        for k in kids:
            layout(k, box, gap, pos, out)
    else:
        outer, inner = kids
        oname = outer if isinstance(outer, str) else None
        layout(outer, box, gap, "O", out)
        ib = _inner_box(oname, op, box, gap)
        layout(inner, ib, gap, "I", out)
    return out


DEFAULT_INNER = {     # unit (y-down) inner boxes by enclosure operator
    "⿴": (210, 210, 790, 790),
    "⿵": (230, 300, 770, 1000),
    "⿶": (230, 0, 770, 700),
    "⿷": (300, 230, 1000, 770),
    "⿸": (330, 330, 1000, 1000),
    "⿹": (0, 330, 670, 1000),
    "⿺": (330, 0, 1000, 670),
}


def _inner_box(oname, op, box, gap):
    ub = None
    if oname is not None:
        c = COMPONENTS.get(_variant(oname, "O"))
        if c is not None:
            ub = c.inner.get(op) or c.inner.get("*")
    if ub is None:
        ub = DEFAULT_INNER.get(op, (200, 200, 800, 800))
    x0, y0, x1, y1 = box
    ux0, uy0, ux1, uy1 = ub
    W, H = x1 - x0, y1 - y0
    # unit y-down → box y-up
    return (x0 + W * ux0 / 1000, y1 - H * uy1 / 1000, x0 + W * ux1 / 1000, y1 - H * uy0 / 1000)


def _share(t, pos, axis):
    if isinstance(t, str):
        c = COMPONENTS.get(_variant(t, pos))
        if c is not None and pos in c.share:
            # explicit share is relative to a partner of demand ~4
            return c.share[pos] / (1 - c.share[pos]) * 4.0
        return demand(t, axis)
    return demand(t, axis)


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------

def place(g, placements, scale):
    """Stroke every placed component into builder g with pen scale."""
    for name, (x0, y0, x1, y1) in placements:
        c = COMPONENTS[name]
        sx = (x1 - x0) / 1000.0
        sy = (y1 - y0) / 1000.0
        T = lambda p: (x0 + p[0] * sx, y0 + p[1] * sy)
        for runs in prepared(c):
            for run in runs:
                p = g.pen(*T(run[0][1]))
                for s in run:
                    if s[0] == "line":
                        p.l(*T(s[2]))
                    else:
                        p.c(T(s[2]), T(s[3]), T(s[4]))
                p.end(scale=scale)


def density_scale(placements, W, H):
    """Stroke scale so long parallel strokes keep enough white between them.
    Considers strokes across all placed components (they share the box)."""
    hs, vs = [], []
    for name, (x0, y0, x1, y1) in placements:
        c = COMPONENTS[name]
        sx = (x1 - x0) / 1000.0
        sy = (y1 - y0) / 1000.0
        for runs in prepared(c):
            for run in runs:
                for s in run:
                    if s[0] != "line":
                        continue
                    a, b = s[1], s[-1]
                    ax, ay = x0 + a[0] * sx, y0 + a[1] * sy
                    bx, by = x0 + b[0] * sx, y0 + b[1] * sy
                    dx, dy = abs(bx - ax), abs(by - ay)
                    if dx > dy * 4 and dx > 90:
                        hs.append((min(ax, bx), max(ax, bx), (ay + by) / 2))
                    elif dy > dx * 4 and dy > 90:
                        vs.append((min(ay, by), max(ay, by), (ax + bx) / 2))
    best = 1.0
    for lines, thick in ((hs, H), (vs, W)):
        lines.sort(key=lambda l: l[2])
        for i in range(len(lines)):
            a = lines[i]
            for j in range(i + 1, len(lines)):
                b = lines[j]
                d = b[2] - a[2]
                if d < 8:
                    continue
                ov = min(a[1], b[1]) - max(a[0], b[0])
                if ov < 0.4 * min(a[1] - a[0], b[1] - b[0]):
                    continue
                best = min(best, 0.6 * d / thick)
                break
    # soften: per-character weight changes should stay subtle
    best = 0.35 + 0.65 * best if best < 1 else 1.0
    return max(0.5, min(1.0, best))


def cjk_weight_factor(W):
    """Ideographs carry many strokes: their pen tapers relative to Latin as
    weight grows (Thin ≈ 0.95, Regular ≈ 0.83, Black ≈ 0.65 of the Latin stem)."""
    return 0.95 - 0.0019 * (W - 22)


def build_char(g, ch, weight_factor=None, advance=1000.0, x_shift=0.0, layer=None):
    """Draw character `ch` into glyph builder g (fixed, advance set)."""
    t = resolve(ch, layer=layer)
    if weight_factor is None:
        weight_factor = cjk_weight_factor(g.W)
    W = g.W * weight_factor
    gap = 0.98 * W + 24
    fx0, fy0, fx1, fy1 = FACE
    hw, hh = W / 2, g.H * weight_factor / 2
    box = (fx0 + hw + x_shift, fy0 + hh, fx1 - hw + x_shift, fy1 - hh)
    if isinstance(t, str):
        c = COMPONENTS[t]
        if c.solo:
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            w = (box[2] - box[0]) * c.solo[0] / 2
            h = (box[3] - box[1]) * c.solo[1] / 2
            box = (cx - w, cy - h, cx + w, cy + h)
    _MIN_GAP[0] = 1.08 * W + 10
    pl = layout(t, box, gap)
    sc = density_scale(pl, W, g.H * weight_factor)
    if sc < 0.999:
        # second pass: thinner strokes allow tighter gaps in dense characters
        _MIN_GAP[0] = 1.08 * W * sc + 10
        pl = layout(t, box, gap * (0.5 + 0.5 * sc))
        sc = min(sc, density_scale(pl, W, g.H * weight_factor))
    place(g, pl, weight_factor * sc)
    g.fixed = True
    g.advance = advance
    return pl


def load_joyo():
    """Jōyō kanji (Unihan kJoyoKanji) in code-point order, with stroke counts."""
    out, strokes = [], {}
    for line in (HERE / "unihan_joyo.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        cp, ch, st = line.split("\t")
        out.append(ch)
        if st:
            strokes[ch] = int(st.split(",")[0])
    return out, strokes


def load_unihan():
    order, strokes = [], {}
    for line in (HERE / "unihan_tgh.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        cp, ch, idx, st = line.split("\t")
        order.append((ch, int(idx)))
        if st:
            strokes[ch] = int(st)
    for line in (HERE / "unihan_strokes.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        strokes.setdefault(parts[0], int(parts[1]))
    return order, strokes


def radical_of(ch):
    """Kangxi radical number of a character (Unihan kRSUnicode) or None."""
    global _RAD
    if "_RAD" not in globals() or _RAD is None:
        _RAD = {}
        for line in (HERE / "unihan_strokes.tsv").read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) > 2 and parts[2]:
                _RAD[parts[0]] = int(parts[2])
    return _RAD.get(ch)


_RAD = None


def stroke_count(t):
    return sum(len(COMPONENTS[l].paths) for l in leaves(t))
