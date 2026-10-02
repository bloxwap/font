"""Composite engine wrapper for the monospaced pixel grid.

Reuses the shared recipe logic (`composites.recipe_for`, NFD decompositions,
aliases) but places components so that every glyph keeps the 600-unit
advance (the core `_compose` widens glyphs for `tonos_left`, `caron`,
`dotright` and `prefix`, which would break the monospaced grid), and adds the
italic row-shift correction when a mark is moved vertically.
"""
from __future__ import annotations

from .. import composites as comp
from ..build import GlyphOut
from .art import ADV, CELL
from .geom import italic_dx


def _italic_corr(dy, mark_row):
    d = round(dy / CELL)
    if d == 0:
        return 0
    return italic_dx(mark_row + d) - italic_dx(mark_row)


def compose_all(outs: dict, xh: int, italic: bool):
    have = set(outs)
    cmap = {}
    for o in outs.values():
        for u in o.unicodes:
            cmap[u] = o.name
            comp.register_cmap(u, o.name)

    def is_case(name):
        o = outs.get(name)
        if o is None or o.ink is None:
            return False
        return o.anchors.get("top", (0, 0))[1] > xh + 60

    pending = [cp for cp in comp.target_codepoints() if cp not in cmap]
    progress = True
    while progress:
        progress = False
        rest = []
        for cp in pending:
            r = comp.recipe_for(cp, have, is_case)
            if r is None:
                rest.append(cp)
                continue
            name = comp.glyph_name(cp)
            if name in have:
                name = f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"
            o = _compose(name, cp, r, outs, italic)
            if o is None:
                rest.append(cp)
                continue
            outs[name] = o
            have.add(name)
            cmap[cp] = name
            comp.register_cmap(cp, name)
            progress = True
        pending = rest
    return cmap, pending


def _compose(name, cp, recipe, outs, italic):
    if recipe[0][1] == "prefix":
        return None
    base_name = recipe[0][0]
    base = outs[base_name]
    if base.kind == "mark":
        return None
    o = GlyphOut(name, [cp])
    o.components.append((base_name, 0, 0))
    o.advance = ADV
    o.ink = base.ink
    o.minrow = getattr(base, "minrow", 0)
    anchors = dict(base.anchors)
    for mname, attach in recipe[1:]:
        if attach == "tonos_left":
            # Greek capitals: accent sits above the capital, flush left
            cand = mname + ".case"
            m = outs.get(cand) or outs.get(mname)
            if m is None or "top" not in anchors or "_top" not in m.anchors:
                return None
            bx, by = anchors["top"]
            mx, my = m.anchors["_top"]
            dy = by - my
            dx = CELL - m.minx
            if italic:
                dx += _italic_corr(dy, m.minrow)
            o.components.append((m.name, dx, dy))
            if "top" in m.anchors:
                anchors["top"] = (bx, m.anchors["top"][1] + dy)
            continue
        m = outs[mname]
        key = "_" + attach
        if attach not in anchors or key not in m.anchors:
            return None
        bx, by = anchors[attach]
        mx, my = m.anchors[key]
        dx, dy = bx - mx, by - my          # italic: anchors are already sheared
        o.components.append((mname, dx, dy))
        for an in ("top", "bottom"):
            if attach == an and an in m.anchors:
                anchors[an] = (m.anchors[an][0] + bx - mx, m.anchors[an][1] + dy)
    o.anchors = {k: v for k, v in anchors.items() if k in ("top", "bottom")}
    return o
