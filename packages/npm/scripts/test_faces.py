"""Check real binary metadata, static instances, cmap and unchanged web sources."""
import json
import os
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.unicodedata import script
from faces import build, face_path
from io import BytesIO
from static_sources import load_lock, read_source, resolve_sources

ROOT = Path(__file__).resolve().parents[1]


class BuiltFaces(unittest.TestCase):
    def test_all_binary_metadata_and_coverage(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        sources = resolve_sources()
        for face in manifest['faces']:
            with self.subTest(path=face['path']):
                font = TTFont(face_path(face), recalcBBoxes=False)
                self.assertEqual(face['family'], font['name'].getDebugName(1))
                self.assertEqual(face['version'], font['name'].getDebugName(5))
                self.assertEqual(face['style'], 'italic' if font['OS/2'].fsSelection & 1 else 'normal')
                script_tags = {script(cp) for cp in font.getBestCmap()}
                self.assertEqual(face['scripts'], sorted(script_tags - {'Zyyy', 'Zinh', 'Zzzz'}) or sorted(script_tags - {'Zzzz'}))
                if face['format'] == 'ttf':
                    self.assertNotIn('fvar', font)
                    self.assertEqual(face['weight'], font['OS/2'].usWeightClass)
                    for name_id in [1, 4, 6, 16]:
                        self.assertEqual(face['registrationName'], font['name'].getDebugName(name_id))
                    if Path(face['path']).parent.name in ['BloxwapSans', 'BloxwapMono', 'BloxwapPixel']:
                        cmap = font.getBestCmap()
                        self.assertEqual(len({font['hmtx'][cmap[ord(n)]][0] for n in '0123456789'}), 1)
                    family = Path(face['path']).parent.name
                    source_input = sources[family, Path(face['source'].split('@')[0]).name]
                    self.assertEqual(face['source'], source_input[3])
                    source_bytes = read_source(source_input)
                    source = TTFont(BytesIO(source_bytes), recalcBBoxes=False)
                    self.assertEqual(face['sourceWeight'], source['OS/2'].usWeightClass)
                    from hashlib import sha256
                    self.assertEqual(face['sourceSha256'], sha256(source_bytes).hexdigest())
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
                    source_dir = ROOT.parents[1] / 'apps/docs/public/fonts' / family / 'variable'
                    original = list((source_dir / 'subsets').glob(f'*.{face["subset"]}.woff2')) if 'subset' in face else list(source_dir.glob('*.woff2'))
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


class StaticSources(unittest.TestCase):
    def test_dist_precedence_and_verified_zip_fallback(self):
        from hashlib import sha256
        from unittest.mock import patch
        from zipfile import ZipFile
        from static_sources import fetch_zip
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            family = 'BloxwapSans'
            inner = f'{family}/woff2/{family}-Regular.woff2'
            data = b'fixture static source'
            zipped = BytesIO()
            with ZipFile(zipped, 'w') as archive:
                archive.writestr(inner, data)
                archive.writestr(f'{family}/OFL.txt', (ROOT.parents[1] / 'LICENSE').read_bytes())
            archive_bytes = zipped.getvalue()
            entry = dict(tag='v0.1.2', asset=f'{family}.zip', sha256=sha256(archive_bytes).hexdigest(),
                         files=[dict(path=inner, sha256=sha256(data).hexdigest())])
            lock = dict(families={family: entry})
            local = base / 'dist' / inner
            local.parent.mkdir(parents=True)
            local.write_bytes(data)
            with patch('static_sources.urlopen', side_effect=AssertionError('unexpected network')):
                sources = resolve_sources(lock=lock, dist=base / 'dist', cache=base / 'cache')
                self.assertEqual(read_source(sources[family, local.name]), data)
                self.assertIsNone(sources[family, local.name][1])
            # An existing mismatched dist input must fail, even if a release zip is available.
            local.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'SHA256 mismatch.*Regular'):
                resolve_sources(lock=lock, dist=base / 'dist', cache=base / 'cache')
            local.unlink()
            with patch('static_sources.urlopen', return_value=BytesIO(archive_bytes)) as download:
                sources = resolve_sources(lock=lock, dist=base / 'dist', cache=base / 'cache')
                self.assertEqual(read_source(sources[family, local.name]), data)
                self.assertEqual(sources[family, local.name][3], f'{family}.zip:{inner}@v0.1.2')
                download.assert_called_once()
            with patch('static_sources.urlopen', side_effect=AssertionError('unexpected network')):
                sources = resolve_sources(lock=lock, dist=base / 'dist', cache=base / 'cache')
                self.assertEqual(read_source(sources[family, local.name]), data)
            cached = base / 'cache/v0.1.2' / entry['asset']
            # Verify inner entries independently, even when the zip hash is valid.
            entry['files'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(RuntimeError, 'SHA256 mismatch.*Regular'):
                fetch_zip(entry, base / 'cache')
            cached.write_bytes(archive_bytes + b'corrupt')
            with self.assertRaisesRegex(RuntimeError, 'SHA256 mismatch.*zip'):
                fetch_zip(entry, base / 'cache')

    def test_lock_covers_every_native_source(self):
        from faces import NATIVE_GROUPS, WEIGHTS
        lock = load_lock()
        self.assertEqual(set(lock['families']), {f for fs in NATIVE_GROUPS.values() for f in fs})
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        for family, entry in lock['families'].items():
            web = [f for f in manifest['faces'] if f['format'] == 'woff2' and Path(f['path']).parent.name == family]
            expected = {f'{family}/woff2/{family}-' +
                        (('Italic' if label == 'Regular' else label + 'Italic') if f['style'] == 'italic' else label) + '.woff2'
                        for f in web for label in WEIGHTS.values()}
            self.assertEqual({f['path'] for f in entry['files']}, expected)


if __name__ == '__main__':
    unittest.main()
