"""Check real binary metadata, static instances, cmap and unchanged web sources."""
import json
import os
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.unicodedata import script
from faces import build, face_path

ROOT = Path(__file__).resolve().parents[1]


class BuiltFaces(unittest.TestCase):
    def test_all_binary_metadata_and_coverage(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        for face in manifest['faces']:
            with self.subTest(path=face['path']):
                font = TTFont(face_path(face), recalcBBoxes=False)
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
                    source_path = ROOT.parents[1] / face['source']
                    source = TTFont(source_path, recalcBBoxes=False)
                    self.assertEqual(face['sourceWeight'], source['OS/2'].usWeightClass)
                    from hashlib import sha256
                    self.assertEqual(face['sourceSha256'], sha256(source_path.read_bytes()).hexdigest())
                    self.assertEqual(font.getGlyphOrder(), source.getGlyphOrder())
                    for table in ['glyf', 'hmtx', 'cmap', 'fpgm', 'prep', 'cvt ']:
                        if table in source:
                            self.assertEqual(font[table].compile(font), source[table].compile(source), table)
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


class ParallelFaces(unittest.TestCase):
    def test_parallel_bytes_and_hash_checked_cache(self):
        # Exercise both a core italic and a large script face using isolated native outputs.
        paths = [ROOT / 'fonts/BloxwapSans/BloxwapSans-Italic-Variable.woff2',
                 ROOT / 'fonts/BloxwapSansKR/BloxwapSansKR-Variable.woff2']
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            serial = build(workers=1, paths=paths, native_root=base / 'serial',
                           manifest_path=base / 'serial.json')
            parallel_manifest = base / 'parallel.json'
            parallel_root = base / 'parallel'
            parallel = build(workers=2, paths=paths, native_root=parallel_root,
                             manifest_path=parallel_manifest)
            self.assertEqual(serial, parallel)
            targets = [face_path(f, parallel_root) for f in parallel['faces'] if f['format'] == 'ttf']
            for target in targets:
                os.utime(target, ns=(1_000_000_000, 1_000_000_000))
            warm = build(workers=2, paths=paths, native_root=parallel_root,
                         manifest_path=parallel_manifest)
            self.assertEqual(parallel, warm)
            self.assertTrue(all(p.stat().st_mtime_ns == 1_000_000_000 for p in targets))
            # A corrupt target, missing target or changed source hash must each invalidate its entry.
            targets[0].write_bytes(targets[0].read_bytes() + b'corrupt')
            targets[1].unlink()
            native_faces = [f for f in parallel['faces'] if f['format'] == 'ttf']
            native_faces[2]['sourceSha256'] = 'stale'
            parallel_manifest.write_text(json.dumps(parallel))
            repaired = build(workers=2, paths=paths, native_root=parallel_root,
                             manifest_path=parallel_manifest)
            self.assertEqual(serial, repaired)
            self.assertTrue(all(p.stat().st_mtime_ns != 1_000_000_000 for p in targets[:3]))
            self.assertTrue(all(p.stat().st_mtime_ns == 1_000_000_000 for p in targets[3:]))
            for face in repaired['faces']:
                if face['format'] == 'ttf':
                    self.assertEqual(face_path(face, parallel_root).read_bytes(),
                                     face_path(face, base / 'serial').read_bytes())


if __name__ == '__main__':
    unittest.main()
