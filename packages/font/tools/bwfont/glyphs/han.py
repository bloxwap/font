"""CJK ideographs (packs 'han' for SC families, 'han-jp' for JP families).

* SC: the 3,500 characters of 通用规范汉字表 level 1 (Simplified Chinese forms).
* JP: the 2,136 Jōyō kanji, drawn through the 'jp' layer (tools/bwfont/han/
  ids_jp*.txt decompositions and '<name>@jp' component forms override the
  shared data).
A character in both sets is one glyph definition used by both families; the
active family picks the layer.  See tools/bwfont/han/engine.py."""
from __future__ import annotations

from ..han import engine as E, load_all
from ..skeleton import glyph, G

LEVEL = 3500

load_all()
ORDER, STROKES = E.load_unihan()
JOYO, JOYO_STROKES = E.load_joyo()


def _resolves(ch, layer):
    try:
        E.resolve(ch, layer=layer)
        return True
    except (KeyError, IndexError):
        return False


def _register(ch, packs):
    def f(g: G):
        layer = "jp" if getattr(g.p, "family_id", "").endswith("-jp") else None
        if g.mono:
            E.build_char(g, ch, advance=1200, x_shift=100, layer=layer)
        else:
            E.build_char(g, ch, advance=1000, layer=layer)
    glyph(f"uni{ord(ch):04X}", ord(ch), families=("sans", "mono"), pack=packs)(f)


_sc = [ch for ch, idx in ORDER if idx <= LEVEL and _resolves(ch, None)]
_jp = [ch for ch in JOYO if _resolves(ch, "jp")]
_sc_set, _jp_set = set(_sc), set(_jp)
for _ch in sorted(_sc_set | _jp_set):
    _packs = tuple(p for p, s in (("han", _sc_set), ("han-jp", _jp_set)) if _ch in s)
    _register(_ch, _packs)
