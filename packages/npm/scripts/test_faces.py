"""Check real binary metadata, static instances, cmap and unchanged web sources."""
import json
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.unicodedata import script

ROOT = Path(__file__).resolve().parents[1]


class BuiltFaces(unittest.TestCase):
    def test_all_binary_metadata_and_coverage(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        for face in manifest['faces']:
            with self.subTest(path=face['path']):
                font = TTFont(ROOT / face['path'])
                self.assertEqual(face['family'], font['name'].getDebugName(1))
                self.assertEqual(face['version'], font['name'].getDebugName(5))
                self.assertEqual(face['style'], 'italic' if font['OS/2'].fsSelection & 1 else 'normal')
                self.assertEqual(face['scripts'], sorted({script(cp) for cp in font.getBestCmap()} - {'Zyyy', 'Zinh', 'Zzzz'}))
                if face['format'] == 'ttf':
                    self.assertNotIn('fvar', font)
                    self.assertEqual(face['weight'], font['OS/2'].usWeightClass)
                    for name_id in [1, 4, 6, 16]:
                        self.assertEqual(face['registrationName'], font['name'].getDebugName(name_id))
                    if Path(face['path']).parent.name in ['BloxwapSans', 'BloxwapMono', 'BloxwapPixel']:
                        cmap = font.getBestCmap()
                        self.assertEqual(len({font['hmtx'][cmap[ord(n)]][0] for n in '0123456789'}), 1)
                    source = TTFont(ROOT / face['source'])
                    self.assertEqual(font.getBestCmap(), source.getBestCmap())
                    for table in ['GSUB', 'GPOS']:
                        if table in source:
                            self.assertEqual([r.ScriptTag for r in font[table].table.ScriptList.ScriptRecord],
                                             [r.ScriptTag for r in source[table].table.ScriptList.ScriptRecord])
                            self.assertEqual([r.FeatureTag for r in font[table].table.FeatureList.FeatureRecord],
                                             [r.FeatureTag for r in source[table].table.FeatureList.FeatureRecord])
                else:
                    self.assertEqual(face['weight'], [font['fvar'].axes[0].minValue,font['fvar'].axes[0].maxValue])
                    # Packaging only renames paths; it must not rewrite variable font bytes.
                    family = Path(face['path']).parent.name
                    original = list((ROOT.parents[1] / 'apps/docs/public/fonts' / family / 'variable').glob('*'))
                    matches = [p for p in original if ('-Italic' in p.name) == (face['style'] == 'italic')]
                    self.assertEqual((ROOT / face['path']).read_bytes(), matches[0].read_bytes())


if __name__ == '__main__':
    unittest.main()
