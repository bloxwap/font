"""Han (CJK ideographs) data: components_*.py (stroke drawings) and
ids_*.txt (decompositions, 'char<TAB>IDS' per line)."""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

_loaded = False


def load_all():
    global _loaded
    if _loaded:
        return
    from . import engine
    pkg = Path(__file__).parent
    for m in sorted(pkgutil.iter_modules([str(pkg)]), key=lambda m: m.name):
        if m.name.startswith("components"):
            importlib.import_module(f"{__name__}.{m.name}")
    for p in sorted(pkg.glob("ids*.txt")):
        if p.name.startswith("ids_jp"):
            continue
        engine.ids(p.read_text(encoding="utf-8"))
    for p in sorted(pkg.glob("ids_jp*.txt")):
        engine.ids(p.read_text(encoding="utf-8"), layer="jp")
    _loaded = True
