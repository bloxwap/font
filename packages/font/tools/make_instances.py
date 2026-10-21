#!/usr/bin/env python3
"""Interpolate static instance UFOs in parallel (SIL OFL-1.1).

usage: make_instances.py FAMILY.designspace OUTDIR
The build pool also uses these helpers to compile instances without UFO I/O.
"""
from __future__ import annotations

import multiprocessing
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.designspaceLib.split import splitInterpolable
from fontmake.instantiator import Instantiator
import ufoLib2


def instance_descriptors(ds_path):
    doc = DesignSpaceDocument.fromfile(ds_path)
    for group, (_loc, sub) in enumerate(splitInterpolable(doc)):
        for index, desc in enumerate(sub.instances):
            yield group, index, Path(desc.filename).name


@lru_cache(maxsize=1)
def _interpolator(ds_path, group):
    # Reuse masters/mutators across instances in each worker, while bounding
    # retained source data when the global pool moves to another family.
    doc = DesignSpaceDocument.fromfile(ds_path)
    sub = list(splitInterpolable(doc))[group][1]
    sub.loadSourceFonts(ufoLib2.Font.open)
    return Instantiator.from_designspace(sub, round_geometry=True), sub.instances


def generate_instance(ds_path, group, index):
    inst, descriptors = _interpolator(str(Path(ds_path).resolve()), group)
    return inst.generate_instance(descriptors[index])


def _save_instance(args):
    ds_path, group, index, filename, outdir = args
    font = generate_instance(ds_path, group, index)
    font.save(Path(outdir) / filename, overwrite=True)


def main(ds_path, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    jobs = int(os.environ.get("JOBS", str(os.cpu_count() or 1)))
    if jobs < 1:
        raise ValueError("JOBS must be a positive integer")
    tasks = [(str(Path(ds_path).resolve()), group, index, filename, str(outdir))
             for group, index, filename in instance_descriptors(ds_path)]
    with ProcessPoolExecutor(max_workers=min(jobs, max(1, len(tasks))),
                             mp_context=multiprocessing.get_context("spawn")) as pool:
        list(pool.map(_save_instance, tasks))
    print(f"    {len(tasks)} instance UFOs -> {outdir}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
