#!/usr/bin/env python3
"""Compile both static formats from one interpolated UFO (SIL OFL-1.1)."""
from __future__ import annotations

from copy import deepcopy
import json
import re
import resource
import time
from pathlib import Path

from fontmake.font_project import FontProject
from ufo2ft.constants import CFFOptimization
from ufo2ft.featureCompiler import FeatureCompiler

from bwfont.ufo2ft_filters import RobustRemoveOverlapsFilter
from make_instances import generate_instance


class PairedFontProject(FontProject):
    def __init__(self):
        super().__init__()
        cache = {}

        class SharedFeatures(FeatureCompiler):
            def buildTables(self):
                # Cache layout and feature-name compilation only. Other table
                # statements or variable features need the normal compiler.
                if re.search(r"\btable\s+(?!GDEF\b|BASE\b)|\b(?:include|variation|conditionset)\b",
                             self.features):
                    return super().buildTables()
                key = (self.features, tuple(self.ttFont.getGlyphOrder()),
                       self.ttFont["name"].compile(self.ttFont))
                if key not in cache:
                    super().buildTables()
                    tables = {tag: deepcopy(self.ttFont[tag])
                              for tag in ("GDEF", "GPOS", "GSUB", "BASE", "name")
                              if tag in self.ttFont}
                    cache[key] = tables, self.ttFont["OS/2"].usMaxContext
                else:
                    tables, context = cache[key]
                    for tag, table in tables.items():
                        self.ttFont[tag] = deepcopy(table)
                    self.ttFont["OS/2"].usMaxContext = context

        self.feature_compiler = SharedFeatures

    def _iter_compile(self, ufos, *args, **kwargs):
        return super()._iter_compile(ufos, *args,
                                     featureCompilerClass=self.feature_compiler, **kwargs)


def _cpu():
    return sum(u.ru_utime + u.ru_stime for u in
               (resource.getrusage(resource.RUSAGE_SELF),
                resource.getrusage(resource.RUSAGE_CHILDREN)))


def compile_instance(ds_path, group, index, filename, outdir):
    """One global pool slot owns interpolation and both compiles, with no subpool."""
    outdir = Path(outdir)
    name = Path(filename).stem
    rows = []

    def timed(stage, action):
        start, cpu = time.monotonic(), _cpu()
        result = action()
        rows.append(dict(stage=stage, start=start, end=time.monotonic(),
                         cpu_seconds=_cpu() - cpu))
        return result

    font = timed("make_instances", lambda: generate_instance(ds_path, group, index))
    # FontProject.save_otfs currently forces inplace=True internally, so each
    # format must receive an independent font. Never feed OTF-filtered contours
    # into the TTF pre-filter.
    ttf_source = timed("make_instances", lambda: deepcopy(font))
    project = PairedFontProject()
    memo = {}
    for fmt, source in (("otf", font), ("ttf", ttf_source)):
        def compile_format():
            project.run_from_ufos(
                [source], output=[fmt],
                output_path=str(outdir / fmt / f"{name}.{fmt}"),
                remove_overlaps=False,
                optimize_cff=CFFOptimization.SUBROUTINIZE,
                filters=[RobustRemoveOverlapsFilter(pre=fmt == "ttf", memo=memo)],
            )
        timed(f"static_{fmt}", compile_format)
    (outdir / "timings").mkdir(exist_ok=True)
    (outdir / "timings" / f"{name}.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows
