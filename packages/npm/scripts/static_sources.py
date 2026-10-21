"""Pin and verify Bloxwap static WOFF2 release sources (SIL OFL-1.1).

lock --tag vX rebuilds the inventory from local release zips; fetch downloads only
families with missing dist inputs. No authentication or third-party data is used.
"""
import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
LOCK = ROOT / 'static-sources.json'
DIST = REPO / 'packages/font/fonts'
DOWNLOADS = REPO / 'apps/docs/public/downloads'
RELEASES = 'https://github.com/bloxwap/font/releases/download'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify(data, expected, description):
    actual = sha256(data)
    if actual != expected:
        raise RuntimeError(f'SHA256 mismatch for {description}: expected {expected}, got {actual}. '
                           'Restore the pinned input, or rebuild and commit static-sources.json with the font release.')
    return data


def load_lock(path=LOCK):
    lock = json.loads(path.read_text())
    if lock['schemaVersion'] != 1 or lock['license'] != 'OFL-1.1':
        raise RuntimeError(f'Unsupported static source lock: {path}')
    return lock


def lock_sources(tag, downloads=DOWNLOADS, output=LOCK):
    if not re.fullmatch(r'v[\w.-]+', tag):
        raise ValueError(f'Invalid release tag: {tag}')
    families = {}
    for directory in sorted((REPO / 'apps/docs/public/fonts').iterdir()):
        if not directory.is_dir():
            continue
        family = directory.name
        asset = f'{family}.zip'
        archive = downloads / asset
        data = archive.read_bytes()
        with ZipFile(BytesIO(data)) as zipped:
            if zipped.read(f'{family}/OFL.txt') != (REPO / 'LICENSE').read_bytes():
                raise RuntimeError(f'{asset} must carry the repository OFL license')
            paths = sorted(n for n in zipped.namelist()
                           if n.startswith(f'{family}/woff2/') and n.endswith('.woff2'))
            variables = list((directory / 'variable').glob('*.woff2'))
            labels = ['Thin', 'ExtraLight', 'Light', 'Regular', 'Medium', 'SemiBold', 'Bold', 'ExtraBold', 'Black']
            expected = {f'{family}/woff2/{family}-' +
                        (('Italic' if label == 'Regular' else label + 'Italic') if '-Italic' in variable.name else label) + '.woff2'
                        for variable in variables for label in labels}
            if not paths or len(paths) != len(set(paths)) or set(paths) != expected:
                raise RuntimeError(f'Incomplete, unexpected or duplicate static WOFF2 entries in {asset}')
            files = [dict(path=p, sha256=sha256(zipped.read(p))) for p in paths]
        families[family] = dict(tag=tag, asset=asset, sha256=sha256(data), files=files)
    if not families:
        raise RuntimeError('No font families found')
    result = dict(schemaVersion=1, license='OFL-1.1', families=families)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Locked {len(families)} families at {tag}: {output}')
    return result


def fetch_zip(entry, cache=None):
    base = Path(cache or os.environ.get('BLOXWAP_STATIC_SOURCES_CACHE',
                                      Path.home() / '.cache/bloxwap-font/static-sources'))
    target = base / entry['tag'] / entry['asset']
    if target.exists():
        data = verify(target.read_bytes(), entry['sha256'], target)
    else:
        url = f"{RELEASES}/{entry['tag']}/{entry['asset']}"
        print(f'Fetching {url}', flush=True)
        try:
            with urlopen(url, timeout=120) as response:
                data = verify(response.read(), entry['sha256'], url)
        except OSError as error:
            raise RuntimeError(f'Cannot fetch {url}: {error}. Provide matching dist WOFF2s or '
                               'run static_sources.py fetch with network access.') from error
    with ZipFile(BytesIO(data)) as zipped:
        for file in entry['files']:
            verify(zipped.read(file['path']), file['sha256'], f"{entry['asset']}:{file['path']}")
        license_path = f"{Path(entry['asset']).stem}/OFL.txt"
        if zipped.read(license_path) != (REPO / 'LICENSE').read_bytes():
            raise RuntimeError(f"{entry['asset']} must carry the repository OFL license")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        # Readers never observe a partially downloaded zip.
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)
        temporary_path.replace(target)
    return target


def resolve_sources(families=None, lock=None, dist=DIST, cache=None):
    """Validate dist first; fetch each missing family's zip once before workers start."""
    locked = lock if lock is not None else load_lock()
    sources = {}
    for family in sorted(families if families is not None else locked['families']):
        entry = locked['families'][family]
        archive = None
        for file in entry['files']:
            local = dist / file['path']
            if local.is_file():
                verify(local.read_bytes(), file['sha256'], local)
                path, inner = local, None
            else:
                if archive is None:
                    archive = fetch_zip(entry, cache)
                path, inner = archive, file['path']
            provenance = f"{entry['asset']}:{file['path']}@{entry['tag']}"
            sources[family, Path(file['path']).name] = (path, inner, file['sha256'], provenance)
    return sources


def read_source(source):
    path, inner, expected, provenance = source
    if inner:
        with ZipFile(path) as zipped:
            data = zipped.read(inner)
    else:
        data = path.read_bytes()
    return verify(data, expected, provenance)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    lock = commands.add_parser('lock')
    lock.add_argument('--tag', required=True)
    lock.add_argument('--downloads', type=Path, default=DOWNLOADS)
    lock.add_argument('--output', type=Path, default=LOCK)
    fetch = commands.add_parser('fetch')
    fetch.add_argument('--family', action='append', help='Fetch only this family (repeatable)')
    fetch.add_argument('--cache', type=Path)
    args = parser.parse_args()
    if args.command == 'lock':
        lock_sources(args.tag, args.downloads, args.output)
    else:
        sources = resolve_sources(args.family, cache=args.cache)
        print(f'Verified {len(sources)} static WOFF2 sources')


if __name__ == '__main__':
    main()
