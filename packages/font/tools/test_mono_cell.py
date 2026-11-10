"""Mono composites stay on the 600-unit cell (SIL OFL-1.1)."""
import unittest

from bwfont import build as B
from bwfont.families import FAMILIES
from bwfont.geometry import Plan


class MonoCellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        B.load_glyph_modules()
        cls.outs = {}
        for stem, label in ((22, "Thin"), (84, "Regular"), (180, "Black")):
            params, outs = B.make_master(FAMILIES["mono"], stem, 0, Plan(), None)
            B.add_composites(params, outs, "mono")
            cls.outs[label] = outs

    def test_encoded_advances_are_cell_multiples(self):
        bad = []
        for label, outs in self.outs.items():
            for glyph in outs.values():
                if not glyph.unicodes:
                    continue
                if glyph.advance % 600 != 0:
                    bad.append(f"{label} {glyph.name} {glyph.advance}")
        self.assertEqual(bad, [])

    def test_known_overflows_are_one_cell(self):
        regular = self.outs["Regular"]
        by_cp = {cp: glyph for glyph in regular.values() for cp in glyph.unicodes}
        for cp, name in ((0x10F, "dcaron"), (0x13E, "lcaron"), (0x140, "ldot"),
                         (0x149, "napostrophe"), (0x165, "tcaron"), (0x386, "Alphatonos"),
                         (0x1F08, "Greek capital with breathing")):
            glyph = by_cp.get(cp)
            self.assertIsNotNone(glyph, name)
            self.assertEqual(glyph.advance, 600, name)
