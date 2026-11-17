"""Pinned interpreter and package versions for font builds (SIL OFL-1.1)."""
from __future__ import annotations

import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
REQUIREMENTS = ROOT / "requirements.txt"


def source_date_epoch() -> int | None:
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if not raw:
        return None
    return int(raw)


def ensure_source_date_epoch() -> int:
    """Pin SOURCE_DATE_EPOCH from the last commit that touched packages/font.

    fontTools' ``timestampNow`` reads this variable, so head.created/modified
    and a second build of the same commit stay byte-identical.
    """
    current = source_date_epoch()
    if current is not None:
        return current
    try:
        epoch = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", "packages/font"],
            cwd=REPO, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        epoch = ""
    if not epoch:
        raise SystemExit("SOURCE_DATE_EPOCH is unset and git log of packages/font failed")
    os.environ["SOURCE_DATE_EPOCH"] = epoch
    return int(epoch)


def generated_stamp() -> str:
    """ISO-8601 UTC time for site data. Follows SOURCE_DATE_EPOCH when set."""
    from datetime import datetime, timezone
    epoch = source_date_epoch()
    if epoch is None:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="seconds")


def check_toolchain(requirements: Path = REQUIREMENTS) -> None:
    """Fail fast when Python or a pinned package does not match requirements.txt."""
    if os.environ.get("BWFONT_ALLOW_TOOLCHAIN_DRIFT") == "1":
        return
    if sys.version_info[:2] != (3, 12):
        raise SystemExit(
            f"Python {sys.version_info.major}.{sys.version_info.minor} is not the pinned 3.12. "
            "Run bun run fonts:setup")
    for raw in requirements.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        req = Requirement(line)
        specs = list(req.specifier)
        if len(specs) != 1 or specs[0].operator != "==":
            raise SystemExit(f"{requirements}: expected an exact pin, got {line}")
        try:
            installed = metadata.version(req.name)
        except metadata.PackageNotFoundError:
            raise SystemExit(f"{req.name} is not installed. Run bun run fonts:setup") from None
        if installed != specs[0].version:
            raise SystemExit(
                f"{req.name} {installed} != {specs[0].version}. Run bun run fonts:setup")
