#!/usr/bin/env python3
"""Subset coverage, retained font data and shaping checks. SIL OFL-1.1.

Run with the font venv. HarfBuzz compares whole single-script samples and each
CSS-selected run with the full font, including the former Latin boundary probes.
"""
from __future__ import annotations

import io
import re
import unittest
from itertools import combinations
from urllib.parse import quote, unquote, urlsplit
from weakref import WeakKeyDictionary

from fontTools.ttLib import TTFont
from fontTools.subset import parse_unicodes

from webfonts import GROUPS, PUBLIC, SHARED_CODEPOINTS, _faces, core_subsets, subset_path

try:
    import uharfbuzz as hb
except ImportError:
    hb = None

SAMPLES = {
    'en': 'AVATAR office fi fl 1234',
    'fr': 'Été français déjà vu',
    'de': 'Fünf große Vögel',
    'pl': 'Zażółć gęślą jaźń',
    'cs': 'Příliš žluťoučký kůň úpěl ďábelské ódy',
    'tr': 'İstanbul ışıkları, Çeşme ve güzel Türkçe',
    'vi': 'Tiếng Việt rất đẹp',
    'el': 'Αλφάβητο Ελληνικά',
    'ru': 'Съешь ещё этих булок',
    'uk': 'Ще не вмерла України і слава, і воля',
}
SHAPERS = WeakKeyDictionary()


def font_runs(text, groups):
    # Common characters join the script they occur in, preserving whole words,
    # combining clusters and punctuation. Latin is preferred for common-only text.
    scripts = {name for name in ['latin', 'greek', 'cyrillic']
               if any(ord(char) in groups[name] - SHARED_CODEPOINTS for char in text)}
    if len(scripts) <= 1:
        name = next(iter(scripts), 'latin')
        if set(map(ord, text)) <= groups[name]:
            return [[name, text]]
    runs = []
    for char in text:
        name = next(name for name, cps in groups.items() if ord(char) in cps)
        if runs and runs[-1][0] == name:
            runs[-1][1] += char
        else:
            runs.append([name, char])
    return runs


def shape(font, text, location, language, features=None):
    if hb is None:
        from fontTools.varLib.instancer import instantiateVariableFont
        instance = instantiateVariableFont(font, location, inplace=False)
        cmap = instance.getBestCmap()
        return [(cmap[ord(c)], instance['hmtx'][cmap[ord(c)]]) for c in text]
    # HarfBuzz needs an SFNT, not a compressed WOFF2 container.
    shaped = SHAPERS.get(font)
    if shaped is None:
        data = io.BytesIO()
        flavor = font.flavor
        font.flavor = None
        font.save(data)
        font.flavor = flavor
        shaped = hb.Font(hb.Face(data.getvalue()))
        SHAPERS[font] = shaped
    shaped.set_variations(location)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    buffer.language = language
    hb.shape(shaped, buffer, features)
    return [(font.getGlyphName(info.codepoint), pos.x_advance, pos.y_advance,
             pos.x_offset, pos.y_offset) for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)]


class Subsets(unittest.TestCase):
    def test_coverage_shared_overlap_and_preserved_font_data(self):
        css = (PUBLIC / 'bloxwap-font.css').read_text()
        rules = {}
        for face in re.findall(r'@font-face \{[^}]*\}', css):
            url = re.search(r'url\("([^\"]+)"\)', face)[1]
            ranges = re.search(r'unicode-range: ([^;]+);', face)
            if ranges:
                rules[unquote(urlsplit(url).path)] = set(parse_unicodes(ranges[1]))
        for family in GROUPS:
            sources = _faces(family, PUBLIC)
            self.assertEqual(len(sources), 2)
            for _style, path in sources:
                positions = [css.index(quote(subset_path(path, name).name))
                             for name in ['other', 'cyrillic', 'greek', 'latin']]
                self.assertEqual(positions, sorted(positions), 'Latin must win shared character matching')
                with TTFont(path, recalcTimestamp=False) as full:
                    groups = core_subsets(set(full.getBestCmap()))
                    for left, right in combinations(groups.values(), 2):
                        self.assertTrue(left & right <= SHARED_CODEPOINTS)
                    seen = set()
                    for name, cps in groups.items():
                        with self.subTest(path=path.name, subset=name), TTFont(subset_path(path, name)) as font:
                            seen |= cps
                            self.assertEqual(set(font.getBestCmap()), cps)
                            relative = subset_path(path, name).relative_to(PUBLIC).as_posix()
                            self.assertEqual(rules[relative] & set(full.getBestCmap()), cps)
                            self.assertEqual(font['fvar'].compile(font), full['fvar'].compile(full))
                            self.assertEqual(font['name'].compile(font), full['name'].compile(full))
                            self.assertEqual(font['head'].created, full['head'].created)
                            self.assertEqual(font['head'].modified, full['head'].modified)
                            self.assertEqual(font['OS/2'].fsType, full['OS/2'].fsType)
                            self.assertEqual(set(font.keys()), set(full.keys()))
                            self.assertEqual(font.reader['OS/2'], full.reader['OS/2'])
                            for field, value in full['hhea'].__dict__.items():
                                if field not in {'tableTag', 'numberOfHMetrics'}:
                                    self.assertEqual(getattr(font['hhea'], field), value, field)
                            for field in ['xMin', 'yMin', 'xMax', 'yMax', 'unitsPerEm', 'flags']:
                                self.assertEqual(getattr(font['head'], field), getattr(full['head'], field), field)
                            self.assertIn('Open Font License', font['name'].getDebugName(13))
                            for tag in ['fpgm', 'prep', 'cvt ', 'gasp', 'STAT', 'avar']:
                                if tag in full:
                                    self.assertEqual(font[tag].compile(font), full[tag].compile(full))
                            for glyph in font.getGlyphOrder():
                                self.assertIn(glyph, full.getGlyphOrder())
                                self.assertEqual(font['hmtx'][glyph], full['hmtx'][glyph])
                                a = font['glyf'][glyph].getCoordinates(font['glyf'])
                                b = full['glyf'][glyph].getCoordinates(full['glyf'])
                                self.assertEqual(a, b, glyph)
                                if hasattr(full['glyf'][glyph], 'program'):
                                    self.assertEqual(font['glyf'][glyph].program.getBytecode(),
                                                     full['glyf'][glyph].program.getBytecode(), glyph)
                                a = [(v.axes, v.coordinates) for v in font['gvar'].variations[glyph]]
                                b = [(v.axes, v.coordinates) for v in full['gvar'].variations[glyph]]
                                self.assertEqual(a, b, glyph)
                    self.assertEqual(seen, set(full.getBestCmap()))

    def test_shaping_matches_full_font(self):
        for family in GROUPS:
            for _style, path in _faces(family, PUBLIC):
                with TTFont(path, recalcTimestamp=False) as full:
                    groups = core_subsets(set(full.getBestCmap()))
                    fonts = {name: TTFont(subset_path(path, name), recalcTimestamp=False) for name in groups}
                    try:
                        locations = [{'wght': w} for w in [100, 400, 900]]
                        if family == 'pixel':
                            locations = [dict(loc, ROND=r) for loc in locations for r in [0, 50, 100]]
                        for language, text in SAMPLES.items():
                            for loc in locations:
                                for features in [None, {'kern': True, 'smcp': True, 'calt': True,
                                                        'dlig': True, 'pnum': True, 'ss01': True}]:
                                    actual = []
                                    for name, run in font_runs(text, groups):
                                        actual.extend(shape(fonts[name], run, loc, language, features))
                                    with self.subTest(path=path.name, language=language, location=loc,
                                                      sample=text, features=features):
                                        self.assertEqual(actual, shape(full, text, loc, language, features))
                            for name, run in font_runs(text, groups):
                                for loc in locations:
                                    for features in [None, {'kern': True, 'smcp': True, 'calt': True,
                                                            'dlig': True, 'pnum': True, 'ss01': True}]:
                                        with self.subTest(path=path.name, language=language, run=run, location=loc, features=features):
                                            self.assertEqual(shape(fonts[name], run, loc, language, features),
                                                             shape(full, run, loc, language, features))
                    finally:
                        for font in fonts.values():
                            font.close()

    def test_cross_subset_boundary_parity(self):
        # These formerly crossed Latin/Latin Extended font files. They must now
        # shape together, in both styles, including decomposed Latin accents.
        for family in GROUPS:
            for _style, path in _faces(family, PUBLIC):
                with TTFont(path, recalcTimestamp=False) as full:
                    groups = core_subsets(set(full.getBestCmap()))
                    text = 'Tą Vą TŁ AV\u0301 A\u0301'
                    self.assertEqual(font_runs(text, groups), [['latin', text]])
                    with TTFont(subset_path(path, 'latin'), recalcTimestamp=False) as font:
                        for weight in [100, 400, 900]:
                            with self.subTest(path=path.name, weight=weight):
                                self.assertEqual(shape(font, text, {'wght': weight}, 'pl'),
                                                 shape(full, text, {'wght': weight}, 'pl'))

    def test_mono_code_ligatures(self):
        text = 'a -> b => c != d; x <= y && z !== 0'
        for _style, path in _faces('mono', PUBLIC):
            with TTFont(path, recalcTimestamp=False) as full, TTFont(subset_path(path, 'latin'), recalcTimestamp=False) as font:
                self.assertTrue(set(map(ord, text)) <= set(font.getBestCmap()))
                for weight in [100, 400, 900]:
                    for features in [None, {'calt': True, 'dlig': True}, {'calt': False, 'dlig': False}]:
                        with self.subTest(path=path.name, weight=weight, features=features):
                            self.assertEqual(shape(font, text, {'wght': weight}, 'en', features),
                                             shape(full, text, {'wght': weight}, 'en', features))

    def test_script_shared_combining_marks(self):
        # Shared marks must remain encoded in each script font, including stress
        # accents without a precomposed Unicode character.
        for family in GROUPS:
            for _style, path in _faces(family, PUBLIC):
                with TTFont(path, recalcTimestamp=False) as full:
                    for name, text, language in [('cyrillic', 'мо\u0301ре', 'ru'),
                                                  ('greek', 'α\u0304\u0301', 'el')]:
                        with self.subTest(path=path.name, script=name, text=text), TTFont(
                                subset_path(path, name), recalcTimestamp=False) as font:
                            self.assertEqual(shape(font, text, {'wght': 400}, language),
                                             shape(full, text, {'wght': 400}, language))


if __name__ == '__main__':
    print('Shaping engine:', 'HarfBuzz' if hb else 'fontTools cmap/variable advances (no GPOS/GSUB validation)')
    unittest.main()
