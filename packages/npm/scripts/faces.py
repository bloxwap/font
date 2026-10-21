"""Decode committed static WOFF2s into opt-in native TTFs and a face manifest.
No source outlines, cmap, shaping features, or variable font files are edited.
"""
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import shutil
import fontTools
from fontTools.ttLib import TTFont
from fontTools.unicodedata import script

ROOT = Path(__file__).resolve().parents[1]
NATIVE_ROOT = ROOT.parent / 'native'
VERSION = json.loads((ROOT / 'package.json').read_text())['version']
GENERATOR = f'fonttools {fontTools.__version__}'
WEIGHTS = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular',
           500: 'Medium', 600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black'}
NATIVE_GROUPS = {'core': ['BloxwapSans', 'BloxwapMono', 'BloxwapPixel']}
for suffix in ['Arabic', 'Hebrew', 'Armenian', 'Georgian', 'JP', 'KR', 'SC']:
    NATIVE_GROUPS[suffix.lower()] = [f'BloxwapSans{suffix}', f'BloxwapMono{suffix}']


@lru_cache(maxsize=None)
def _digest(path, size, mtime_ns):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(path):
    # Reuse hashes within each process, but never reuse one after a file is rewritten.
    status = path.stat()
    return _digest(path, status.st_size, status.st_mtime_ns)


def metadata(path, font, asset_path=None, **extra):
    return dict(dict(path=asset_path or str(path.relative_to(ROOT)), family=font['name'].getDebugName(1),
                weight=font['OS/2'].usWeightClass,
                style='italic' if font['OS/2'].fsSelection & 1 else 'normal',
                scripts=sorted({script(cp) for cp in font.getBestCmap()} - {'Zyyy', 'Zinh', 'Zzzz'}),
                version=font['name'].getDebugName(5), packageVersion=VERSION,
                bytes=path.stat().st_size, sha256=digest(path)), **extra)


def native_package(family):
    group = next(group for group, families in NATIVE_GROUPS.items() if family in families)
    return group, '@bloxwap/font-native' + ('' if group == 'core' else '-' + group)


def face_path(face, native_root=NATIVE_ROOT):
    if face['format'] == 'woff2':
        return ROOT / face['path']
    group, package = native_package(Path(face['path']).parent.name)
    return native_root / group / face['path'].removeprefix(package + '/assets/')


def web_face(task):
    path, cached = task
    if cached and cached['packageVersion'] == VERSION and cached['sha256'] == digest(path):
        return cached
    with TTFont(path, recalcTimestamp=False) as variable:
        axes = {a.axisTag: dict(min=a.minValue, default=a.defaultValue, max=a.maxValue)
                for a in variable['fvar'].axes}
        return metadata(path, variable, format='woff2', axes=axes,
                        weight=[axes['wght']['min'], axes['wght']['max']])


def native_face(task):
    web, weight, label, cached, native_root = task
    path = ROOT / web['path']
    family = path.parent.name
    group, package = native_package(family)
    italic = web['style'] == 'italic'
    source_suffix = ('Italic' if label == 'Regular' else label + 'Italic') if italic else label
    static_source = ROOT.parents[1] / 'apps/docs/public/fonts' / family / 'woff2' / f'{family}-{source_suffix}.woff2'
    name = f'{family}-{label}' + ('Italic' if italic else '')
    target = native_root / group / family / f'{name}.ttf'
    asset_path = f'{package}/assets/{family}/{name}.ttf'
    provenance = dict(package=package, registrationName=name,
                      source=str(static_source.relative_to(ROOT.parents[1])), sourceSha256=digest(static_source),
                      variableSource=web['path'], variableSourceSha256=web['sha256'],
                      generation='decode-static-woff2-and-register')
    if (cached and cached['packageVersion'] == VERSION and cached['path'] == asset_path
            and all(cached.get(key) == value for key, value in provenance.items())
            and target.is_file() and cached['sha256'] == digest(target)):
        return cached
    with TTFont(static_source, recalcTimestamp=False, recalcBBoxes=False) as face:
        if 'fvar' in face or face.sfntVersion != '\x00\x01\x00\x00':
            raise RuntimeError(f'Expected committed static TrueType source: {static_source}')
        source_weight = face['OS/2'].usWeightClass
        # Existing named static instances have approximate OS/2 classes (e.g. 608).
        # Normalize only registration metadata to the published named tier (600).
        face['OS/2'].usWeightClass = weight
        # A distinct family for each face works with Expo registration and bare RN on both OSes.
        # Request only this family; do not ask the native renderer to synthesize fontWeight/style.
        for name_id, value in {1: name, 2: 'Regular', 3: f'{VERSION};{name}', 4: name,
                               6: name, 16: name, 17: 'Regular'}.items():
            face['name'].removeNames(nameID=name_id)
            for platform, encoding, language in [(3, 1, 0x409), (1, 0, 0)]:
                face['name'].setName(value, name_id, platform, encoding, language)
        face.flavor = None
        target.parent.mkdir(parents=True, exist_ok=True)
        face.save(target)
        location = {tag: axis['default'] for tag, axis in web['axes'].items()}
        location['wght'] = weight
        return metadata(target, face, asset_path=asset_path, format='ttf', **provenance,
                        sourceWeight=source_weight, axes=location)


def build(workers=None, paths=None, native_root=NATIVE_ROOT, manifest_path=ROOT / 'manifest.json'):
    if fontTools.__version__ != '4.66.1':
        raise RuntimeError('Build requires fonttools[woff,unicode]==4.66.1; see README')
    # Each invocation must observe fresh file contents, including tests running multiple builds.
    _digest.cache_clear()
    cached = {}
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous['version'] == VERSION and previous['generator'] == GENERATOR:
            cached = {f['path']: f for f in previous['faces']}
    paths = sorted(paths if paths is not None else (ROOT / 'fonts').glob('*/*.woff2'))
    with ProcessPoolExecutor(max_workers=workers or os.cpu_count()) as executor:
        web_faces = list(executor.map(web_face, [(p, cached.get(str(p.relative_to(ROOT)))) for p in paths]))
        tasks = []
        for web in web_faces:
            family = Path(web['path']).parent.name
            _, package = native_package(family)
            for weight, label in WEIGHTS.items():
                name = f'{family}-{label}' + ('Italic' if web['style'] == 'italic' else '')
                asset_path = f'{package}/assets/{family}/{name}.ttf'
                tasks.append((web, weight, label, cached.get(asset_path), native_root))
        native_faces = list(executor.map(native_face, tasks))
    # map preserves input order even when workers finish out of order. Keep the serial manifest order.
    faces = []
    for index, web in enumerate(web_faces):
        faces.extend([web, *native_faces[index * len(WEIGHTS):(index + 1) * len(WEIGHTS)]])
    manifest = dict(schemaVersion=1, package='@bloxwap/font', version=VERSION,
                    license='OFL-1.1', generator=GENERATOR, faces=faces)
    for group, families in NATIVE_GROUPS.items():
        package_dir = native_root / group
        package_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT.parents[1] / 'LICENSE', package_dir / 'LICENSE')
        for family in families:
            entries = [f for f in native_faces if Path(f['path']).parent.name == family]
            if not entries:
                continue
            family_dir = package_dir / family
            (family_dir / 'index.js').write_text('// Generated Metro asset map. Register before rendering.\nmodule.exports = {\n' +
                ''.join(f'  "{f["registrationName"]}": require("./{Path(f["path"]).name}"),\n' for f in entries) + '};\n')
            (family_dir / 'index.d.ts').write_text('declare const faces: {\n' +
                ''.join(f'  readonly "{f["registrationName"]}": number;\n' for f in entries) + '};\nexport = faces;\n')
    # Publish the inventory only after every worker and asset map succeeds.
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Manifest: {len(faces)} faces, {sum(f["bytes"] for f in faces)} bytes')
    return manifest


if __name__ == '__main__':
    build()
