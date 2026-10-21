#!/usr/bin/env python3
"""One bounded pool for source generation and all fontmake work (SIL OFL-1.1)."""
from __future__ import annotations

import argparse
import heapq
import itertools
import os
import shutil
import subprocess
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parent.parent
PY = ".venv/bin/python"
FONTMAKE = ".venv/bin/fontmake"
FILTER = "bwfont.ufo2ft_filters::RobustRemoveOverlapsFilter"


@dataclass
class Task:
    name: str
    priority: int
    # Success returns newly ready work; dependent tasks cannot start earlier.
    action: Callable[[], Iterable[Task]]


def run_pool(tasks: Iterable[Task], jobs: int) -> int:
    """Run ready tasks longest-family-first, with at most jobs subprocess owners."""
    if jobs < 1:
        raise ValueError("JOBS must be a positive integer")
    ready = []
    sequence = itertools.count()

    def enqueue(tasks):
        for task in tasks:
            heapq.heappush(ready, (task.priority, next(sequence), task))

    enqueue(tasks)
    maximum = 0
    try:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            running = {}
            while ready or running:
                while ready and len(running) < jobs:
                    _, _, task = heapq.heappop(ready)
                    running[pool.submit(task.action)] = task
                    maximum = max(maximum, len(running))
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                # Check every completed task before releasing any dependent work.
                completed = []
                for future in done:
                    task = running.pop(future)
                    try:
                        completed.extend(future.result())
                    except Exception as e:
                        raise RuntimeError(f"{task.name}: {e}") from e
                enqueue(completed)
    finally:
        print(f"max concurrency: {maximum} (JOBS={jobs})", flush=True)
    return maximum


def family_priority(fid: str) -> int:
    for rank, suffix in enumerate(("-sc", "-jp", "-kr")):
        if fid.endswith(suffix):
            return rank
    return 4 if fid in ("sans", "mono", "pixel") else 3


def command(argv: list[str], log: Path | None = None, append=False) -> None:
    if log is None:
        subprocess.run(argv, cwd=ROOT, check=True)
        return
    with log.open("a" if append else "w") as output:
        result = subprocess.run(argv, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        print("\n".join(log.read_text(errors="replace").splitlines()[-30:]), file=sys.stderr)
        result.check_returncode()


def family_task(fid: str, ps: str) -> Task:
    priority = family_priority(fid)
    ds = f"sources/{fid}/{ps}.designspace"
    out = Path("build") / fid

    def static(ufo):
        # Keep the original OTF -> TTF invocation order and filter arguments.
        for fmt, filt in (("otf", FILTER), ("ttf", f"{FILTER}(pre=True)")):
            command([FONTMAKE, "-u", str(ufo), "-o", fmt, "--output-dir", str(out / fmt),
                     "--keep-overlaps", "--filter", filt], ROOT / out / "static.log", append=True)
        return []

    def instances():
        command([PY, "tools/make_instances.py", ds, str(out / "instance_ufos")])
        ufos = sorted((ROOT / out / "instance_ufos").glob("*.ufo"))
        if not ufos:
            raise RuntimeError(f"no static instance UFOs for {fid}")
        return [Task(f"{fid}: {ufo.stem}", priority,
                     lambda ufo=ufo: static(ufo.relative_to(ROOT))) for ufo in ufos]

    def variable():
        if (ROOT / out).exists():
            shutil.rmtree(ROOT / out)
        (ROOT / out).mkdir(parents=True)
        command([FONTMAKE, "-m", ds, "-o", "variable", "--output-dir", str(out / "variable")],
                ROOT / out / "fontmake.log")
        print(f"    {fid}: variable done", flush=True)
        return [Task(f"{fid}: instances", priority, instances)]

    def generate():
        command([PY, "tools/generate.py", fid])
        return [Task(f"{fid}: variable", priority, variable)]

    return Task(f"{fid}: generate", priority, generate)


def main(argv=None) -> int:
    from bwfont.families import FAMILIES

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("families", nargs="*", choices=list(FAMILIES))
    args = ap.parse_args(argv)
    try:
        jobs = int(os.environ.get("JOBS", str(os.cpu_count() or 1)))
        if jobs < 1:
            raise ValueError
    except ValueError:
        ap.error("JOBS must be a positive integer")
    families = list(dict.fromkeys(args.families or FAMILIES))
    run_pool((family_task(fid, FAMILIES[fid].ps) for fid in families), jobs)
    for fid in families:
        out = ROOT / "build" / fid
        print(f"    {fid}: {len(list((out / 'otf').glob('*.otf')))} otf, "
              f"{len(list((out / 'ttf').glob('*.ttf')))} ttf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
