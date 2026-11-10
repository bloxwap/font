"""License line shared by every generated master (SIL OFL-1.1)."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
LICENSE = REPO / "LICENSE"
RFN = 'Reserved Font Name "Bloxwap"'


def copyright_notice() -> str:
    """Name ID 0. Read from LICENSE so the Reserved Font Name cannot drift."""
    line = LICENSE.read_text(encoding="utf-8").splitlines()[0].strip()
    if RFN not in line:
        raise RuntimeError(f'{LICENSE} must declare {RFN}')
    return line
