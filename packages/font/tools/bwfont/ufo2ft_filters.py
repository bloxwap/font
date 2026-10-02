"""ufo2ft filter: verified overlap removal for static instances.

fontmake ... --keep-overlaps --filter "bwfont.ufo2ft_filters::RobustRemoveOverlapsFilter(pre=True)"
(requires tools/ on PYTHONPATH)
"""
from __future__ import annotations

import logging

from ufo2ft.filters import BaseFilter

from .robust import robust_union

log = logging.getLogger(__name__)


class RobustRemoveOverlapsFilter(BaseFilter):
    def filter(self, glyph):
        if len(glyph) < 2:
            return False
        contours = list(glyph)
        path = robust_union([c.draw for c in contours])
        glyph.clearContours()
        path.draw(glyph.getPen())
        return True
