"""Hyperglot cache invalidation and recovery tests (SIL OFL-1.1)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import site_data


class LanguageCacheTests(unittest.TestCase):
    def test_hyperglot_pickle_does_not_collide_with_result_cache(self):
        from hyperglot import language

        previous = language.LANGUAGE_CACHE_FILE
        paths = []

        def check(path, checker):
            native = Path(language.LANGUAGE_CACHE_FILE)
            # Simulate Hyperglot's write while our result cache is a directory.
            self.assertTrue(native.is_absolute())
            self.assertNotEqual(native, cache)
            native.write_bytes(b"internal pickle")
            paths.append(native)
            return {"count": 0, "scripts": []}

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / ".hyperglot-cache"
            cache.mkdir()
            with (patch.object(site_data, "CACHE", cache),
                  patch.object(site_data, "_check_languages", side_effect=check)):
                site_data._languages_of(Path(tmp) / "font.ttf")
                self.assertTrue(cache.is_dir())
        self.assertEqual(language.LANGUAGE_CACHE_FILE, previous)
        self.assertFalse(paths[0].exists())

    def test_legacy_pickle_is_replaced_with_cache_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / ".hyperglot-cache"
            cache.write_bytes(b"old Hyperglot pickle")
            with patch.object(site_data, "CACHE", cache):
                site_data.prepare_language_cache()
                self.assertTrue(cache.is_dir())

    def test_content_version_and_corrupt_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            font = Path(tmp) / "font.ttf"
            font.write_bytes(b"first font")
            result = {"count": 1, "scripts": [{"script": "Latin", "languages": []}]}
            with (patch.object(site_data, "CACHE", Path(tmp) / "cache"),
                  patch.object(site_data, "version", return_value="1.0") as version,
                  patch.object(site_data, "_languages_of", return_value=result) as compute):
                self.assertEqual(site_data.languages_of(font), result)
                self.assertEqual(site_data.languages_of(font), result)
                self.assertEqual(compute.call_count, 1)
                font.write_bytes(b"changed font")
                self.assertEqual(site_data.languages_of(font), result)
                self.assertEqual(compute.call_count, 2)
                version.return_value = "2.0"
                self.assertEqual(site_data.languages_of(font), result)
                self.assertEqual(compute.call_count, 3)
                for cached in site_data.CACHE.glob("*.json"):
                    cached.write_text("{broken")
                self.assertEqual(site_data.languages_of(font), result)
                self.assertEqual(compute.call_count, 4)

    def test_errors_are_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            font = Path(tmp) / "font.ttf"
            font.write_bytes(b"font")
            with (patch.object(site_data, "CACHE", Path(tmp) / "cache"),
                  patch.object(site_data, "version", return_value="1.0"),
                  patch.object(site_data, "_languages_of", return_value={"error": "unavailable"}) as compute):
                site_data.languages_of(font)
                site_data.languages_of(font)
                self.assertEqual(compute.call_count, 2)
                self.assertFalse(site_data.CACHE.exists())


if __name__ == "__main__":
    unittest.main()
