"""Verify release ZIPs against the committed binary inventory without changing pins."""
import sys
from pathlib import Path
from zipfile import ZipFile
from static_sources import load_lock, verify, REPO


def check(directory):
    lock = load_lock()
    expected = {entry['asset'] for entry in lock['families'].values()} | {'Bloxwap-Fonts.zip'}
    if {p.name for p in directory.glob('*.zip')} != expected:
        raise RuntimeError('Release must contain exactly the pinned family ZIPs and the core bundle')
    for entry in lock['families'].values():
        path = directory / entry['asset']
        verify(path.read_bytes(), entry['sha256'], path)
    with ZipFile(directory / 'Bloxwap-Fonts.zip') as bundle:
        contents = {'Bloxwap-Fonts/OFL.txt': (REPO / 'LICENSE').read_bytes()}
        for family in ('BloxwapSans', 'BloxwapMono', 'BloxwapPixel'):
            with ZipFile(directory / f'{family}.zip') as archive:
                for name in archive.namelist():
                    if name.endswith('/') or name == f'{family}/OFL.txt':
                        continue
                    contents[f'Bloxwap-Fonts/{name}'] = archive.read(name)
        actual = [n for n in bundle.namelist() if not n.endswith('/')]
        if len(actual) != len(contents) or set(actual) != set(contents):
            raise RuntimeError('Core bundle inventory differs from family ZIPs')
        for name, data in contents.items():
            if bundle.read(name) != data:
                raise RuntimeError(f'Core bundle differs from pinned family: {name}')
    print(f'Verified {len(expected)} release ZIPs')


if __name__ == '__main__':
    check(Path(sys.argv[1]))
