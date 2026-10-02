"""Spaces and .notdef."""
from __future__ import annotations

from ..skeleton import glyph, G


@glyph(".notdef")
def notdef(g: G):
    bw = g.wd(440, 440, grow=0.2)
    s = 0.6
    hw, hh = g.hw * s, g.hh * s
    g.line(hw, hh, bw - hw, hh, s)
    g.line(bw - hw, hh, bw - hw, g.cap - hh, s)
    g.line(bw - hw, g.cap - hh, hw, g.cap - hh, s)
    g.line(hw, g.cap - hh, hw, hh, s)
    g.lsb = g.rsb = 50


def _space(name, cp, sans, mono=600):
    def f(g: G):
        g.advance = mono if g.mono else (round(sans + g.grow * 0.25) if sans else 0)
    glyph(name, *([cp] if cp else []), kind="space")(f)


_space("space", 0x20, 260)
_space("uni00A0", 0xA0, 260)
_space("uni2000", 0x2000, 500)
_space("uni2001", 0x2001, 1000)
_space("uni2002", 0x2002, 500)
_space("uni2003", 0x2003, 1000)
_space("uni2004", 0x2004, 333)
_space("uni2005", 0x2005, 250)
_space("uni2006", 0x2006, 167)
_space("uni2007", 0x2007, 560)   # figure space (tabular figure width)
_space("uni2008", 0x2008, 220)   # punctuation space
_space("uni2009", 0x2009, 160)
_space("uni200A", 0x200A, 90)
_space("uni202F", 0x202F, 160)
_space("uni205F", 0x205F, 222)
_space("uni200B", 0x200B, 0, 0)
_space("uni200C", 0x200C, 0, 0)
_space("uni200D", 0x200D, 0, 0)
_space("uni2060", 0x2060, 0, 0)
_space("uniFEFF", 0xFEFF, 0, 0)
_space("uni034F", 0x34F, 0, 0)
