"""Regression checks for source-text identity; run with .venv/bin/python tools/test_unicode.py."""
import unittest

from fontTools.ttLib import TTFont

from check_unicode import unicode_errors
from site_data import find_variable, unicode_description


class UnicodeIntegrityTests(unittest.TestCase):
    def setUp(self):
        path, _ = find_variable('sans', 'BloxwapSans')
        self.assertIsNotNone(path, 'Build Sans before running font integrity tests')
        self.font = TTFont(path)
        self.addCleanup(self.font.close)

    def test_current_font_preserves_unicode(self):
        self.assertEqual(unicode_errors(self.font), [])

    def test_cmap_disagreement_is_rejected(self):
        table = next(t for t in self.font['cmap'].tables if t.isUnicode() and t.format == 4)
        table.cmap = dict(table.cmap)
        table.cmap[ord('I')] = self.font.getBestCmap()[ord('l')]
        self.assertTrue(any('Inconsistent Unicode mapping U+0049' in e for e in unicode_errors(self.font)))

    def test_encoded_stylistic_alternate_is_rejected(self):
        for table in self.font['cmap'].tables:
            if table.isUnicode() and table.format != 14:
                table.cmap[ord('0')] = 'zero.zero'
        self.assertTrue(any('Stylistic glyph zero.zero is encoded' in e for e in unicode_errors(self.font)))

    def test_descriptions_identify_source_characters(self):
        self.assertEqual(unicode_description('α'), 'Greek small letter alpha')
        self.assertEqual(unicode_description('I'), 'Latin capital letter i')
        self.assertEqual(unicode_description('l'), 'Latin small letter l')
        self.assertEqual(unicode_description('fi'), 'Latin small letter f, Latin small letter i')


if __name__ == '__main__':
    unittest.main()
