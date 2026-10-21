"""Bounded build scheduling regression tests (SIL OFL-1.1)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from build_pool import Task, family_priority, run_pool


class BuildPoolTests(unittest.TestCase):
    def test_process_limit_and_dependencies(self):
        # Measure the dummy child processes themselves, independently of pool accounting.
        child = """
import json, os, sys, time
def event(kind):
    fd = os.open(sys.argv[1], os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    os.write(fd, (json.dumps([time.monotonic_ns(), sys.argv[2], kind]) + '\\n').encode())
    os.close(fd)
event('start')
time.sleep(0.04)
event('end')
"""
        for jobs in (1, 2, 4):
            with self.subTest(jobs=jobs), tempfile.TemporaryDirectory() as tmp:
                events = Path(tmp) / "events.jsonl"

                def task(name, children=()):
                    def action():
                        subprocess.run([sys.executable, "-c", child, str(events), name], check=True)
                        return children
                    return Task(name, 0, action)

                roots = []
                for family in ("a", "b", "c", "d"):
                    statics = [task(f"{family}-static-{i}") for i in range(4)]
                    instances = task(f"{family}-instances", statics)
                    variable = task(f"{family}-variable", [instances])
                    roots.append(task(f"{family}-generate", [variable]))
                reported = run_pool(roots, jobs)
                rows = sorted(json.loads(line) for line in events.read_text().splitlines())
                active = maximum = 0
                times = {}
                for time, name, kind in rows:
                    active += 1 if kind == "start" else -1
                    maximum = max(maximum, active)
                    self.assertLessEqual(active, jobs)
                    times[name, kind] = time
                self.assertEqual(active, 0)
                self.assertGreaterEqual(maximum, 1)
                self.assertLessEqual(maximum, reported)
                self.assertLessEqual(reported, jobs)
                for family in ("a", "b", "c", "d"):
                    for before, after in (("generate", "variable"), ("variable", "instances"),
                                          *(("instances", f"static-{i}") for i in range(4))):
                        self.assertLess(times[f"{family}-{before}", "end"],
                                        times[f"{family}-{after}", "start"])

    def test_longest_family_first(self):
        names = ["pixel", "sans", "sans-arabic", "mono-kr", "sans-jp", "mono-sc"]
        seen = []
        tasks = [Task(name, family_priority(name), lambda name=name: seen.append(name) or [])
                 for name in names]
        run_pool(tasks, 1)
        self.assertEqual(seen, ["mono-sc", "sans-jp", "mono-kr", "sans-arabic", "pixel", "sans"])

    def test_failure_stops_dependent_work(self):
        seen = []

        def fail():
            raise RuntimeError("compile failed")

        with self.assertRaisesRegex(RuntimeError, "broken: compile failed"):
            run_pool([Task("broken", 0, fail), Task("queued", 1, lambda: seen.append(1) or [])], 1)
        self.assertEqual(seen, [])

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            run_pool([], 0)


if __name__ == "__main__":
    unittest.main()
