#!/usr/bin/env python3
"""Interpolate static instance UFOs from a designspace (handles discrete axes).

usage: make_instances.py FAMILY.designspace OUTDIR
Writes one UFO per <instance>, ready for `fontmake -u` in parallel.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.designspaceLib.split import splitInterpolable
from fontmake.instantiator import Instantiator


def main(ds_path, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    doc = DesignSpaceDocument.fromfile(ds_path)
    n = 0
    for _loc, sub in splitInterpolable(doc):
        sub.loadSourceFonts(lambda p: __import__("ufoLib2").Font.open(p))
        inst = Instantiator.from_designspace(sub, round_geometry=True)
        for desc in sub.instances:
            font = inst.generate_instance(desc)
            fn = outdir / Path(desc.filename).name
            font.save(fn, overwrite=True)
            n += 1
    print(f"    {n} instance UFOs -> {outdir}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
