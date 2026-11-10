"""Toolchain pin and reproducible timestamps (SIL OFL-1.1)."""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import toolchain


class ToolchainTests(unittest.TestCase):
    def test_drift_fails_fast(self):
        with TemporaryDirectory() as tmp:
            req = Path(tmp) / "requirements.txt"
            req.write_text("fontmake==3.12.0\n", encoding="utf-8")
            with patch.dict(os.environ, {"BWFONT_ALLOW_TOOLCHAIN_DRIFT": ""}, clear=False):
                os.environ.pop("BWFONT_ALLOW_TOOLCHAIN_DRIFT", None)
                with patch("toolchain.metadata.version", return_value="3.12.1"):
                    with self.assertRaises(SystemExit) as raised:
                        toolchain.check_toolchain(req)
            self.assertIn("fontmake 3.12.1 != 3.12.0", str(raised.exception))
            self.assertIn("fonts:setup", str(raised.exception))

    def test_override_skips_the_check(self):
        with TemporaryDirectory() as tmp:
            req = Path(tmp) / "requirements.txt"
            req.write_text("fontmake==0\n", encoding="utf-8")
            with patch.dict(os.environ, {"BWFONT_ALLOW_TOOLCHAIN_DRIFT": "1"}):
                toolchain.check_toolchain(req)

    def test_generated_stamp_follows_epoch(self):
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
            self.assertEqual(toolchain.generated_stamp(), "2023-11-14T22:13:20+00:00")
            again = toolchain.generated_stamp()
            self.assertEqual(toolchain.generated_stamp(), again)
