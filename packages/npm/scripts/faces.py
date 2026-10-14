"""Decode committed static WOFF2s into native TTFs and build a face manifest.
No source outlines, cmap, shaping features, or variable font files are edited.
"""
import hashlib
import json
from pathlib import Path
import fontTools
from fontTools.ttLib import TTFont
from fontTools.unicodedata import script

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / 'package.json').read_text())['version']
WEIGHTS = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular',
           500: 'Medium', 600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(path, font, **extra):
    return dict(dict(path=str(path.relative_to(ROOT)), family=font['name'].getDebugName(1),
                weight=font['OS/2'].usWeightClass,
                style='italic' if font['OS/2'].fsSelection & 1 else 'normal',
                scripts=sorted({script(cp) for cp in font.getBestCmap()} - {'Zyyy', 'Zinh', 'Zzzz'}),
                version=font['name'].getDebugName(5), packageVersion=VERSION,
                bytes=path.stat().st_size, sha256=digest(path)), **extra)


def build():
    if fontTools.__version__ != '4.66.1':
        raise RuntimeError('Build requires fonttools[woff,unicode]==4.66.1; see README')
    faces = []
    for path in sorted((ROOT / 'fonts').glob('*/*.woff2')):
        variable = TTFont(path, recalcTimestamp=False)
        axes = {a.axisTag: dict(min=a.minValue, default=a.defaultValue, max=a.maxValue)
                for a in variable['fvar'].axes}
        faces.append(metadata(path, variable, format='woff2', axes=axes,
                              weight=[axes['wght']['min'], axes['wght']['max']]))
        family = path.parent.name
        native_dir = ROOT / 'native' / family
        native_dir.mkdir(parents=True, exist_ok=True)
        for weight, label in WEIGHTS.items():
            location = {tag: axis['default'] for tag, axis in axes.items()}
            location['wght'] = weight
            source_suffix = ('Italic' if label == 'Regular' else label + 'Italic') if variable['OS/2'].fsSelection & 1 else label
            static_source = ROOT.parents[1] / 'apps/docs/public/fonts' / family / 'woff2' / f'{family}-{source_suffix}.woff2'
            face = TTFont(static_source, recalcTimestamp=False, recalcBBoxes=False)
            if 'fvar' in face or face.sfntVersion != '\x00\x01\x00\x00':
                raise RuntimeError(f'Expected committed static TrueType source: {static_source}')
            source_weight = face['OS/2'].usWeightClass
            # Existing named static instances have approximate OS/2 classes (e.g. 608).
            # Normalize only registration metadata to the published named tier (600).
            face['OS/2'].usWeightClass = weight
            suffix = label + ('Italic' if face['OS/2'].fsSelection & 1 else '')
            name = f'{family}-{suffix}'
            # A distinct family for each face works with Expo registration and bare RN on both OSes.
            # Request only this family; do not ask the native renderer to synthesize fontWeight/style.
            for name_id, value in {1: name, 2: 'Regular', 3: f'{VERSION};{name}', 4: name,
                                   6: name, 16: name, 17: 'Regular'}.items():
                face['name'].removeNames(nameID=name_id)
                for platform, encoding, language in [(3, 1, 0x409), (1, 0, 0)]:
                    face['name'].setName(value, name_id, platform, encoding, language)
            face.flavor = None
            target = native_dir / f'{name}.ttf'
            face.save(target)
            faces.append(metadata(target, face, format='ttf', registrationName=name,
                                  source=str(static_source.relative_to(ROOT.parents[1])), sourceSha256=digest(static_source),
                                  variableSource=str(path.relative_to(ROOT)), variableSourceSha256=digest(path),
                                  generation='decode-static-woff2-and-register', sourceWeight=source_weight,
                                  axes=location))
    manifest = dict(schemaVersion=1, package='@bloxwap/font', version=VERSION,
                    license='OFL-1.1', generator=f'fonttools {fontTools.__version__}', faces=faces)
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for family_dir in sorted((ROOT / 'native').iterdir()):
        entries = [f for f in faces if f['format'] == 'ttf' and Path(f['path']).parent.name == family_dir.name]
        (family_dir / 'index.js').write_text('// Generated Metro asset map. Register before rendering.\nmodule.exports = {\n' +
            ''.join(f'  "{f["registrationName"]}": require("./{Path(f["path"]).name}"),\n' for f in entries) + '};\n')
        (family_dir / 'package.json').write_text('{"type":"commonjs"}\n')
        (family_dir / 'index.d.ts').write_text('declare const faces: {\n' +
            ''.join(f'  readonly "{f["registrationName"]}": number;\n' for f in entries) + '};\nexport = faces;\n')
    print(f'Manifest: {len(faces)} faces, {sum(f["bytes"] for f in faces)} bytes')


if __name__ == '__main__':
    build()
