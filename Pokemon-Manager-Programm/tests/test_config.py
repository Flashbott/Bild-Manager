import os
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "App"))

import pokemon_manager as manager  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_missing_config_has_no_preselected_project_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            previous = os.environ.get("APPDATA")
            os.environ["APPDATA"] = temporary
            try:
                loaded_project, configured, language = manager.load_config()
                self.assertIsNone(loaded_project)
                self.assertFalse(configured)
                self.assertEqual(language, "de")
            finally:
                if previous is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = previous

    def test_config_round_trip_and_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            previous = os.environ.get("APPDATA")
            os.environ["APPDATA"] = temporary
            try:
                project = Path(temporary) / "Pokémon-Projekt"
                manager.save_settings(project, "de")
                loaded_project, configured, language = manager.load_config()
                self.assertEqual(loaded_project, project)
                self.assertTrue(configured)
                self.assertEqual(language, "de")
                raw = manager.app_config_path().read_text(encoding="utf-8")
                self.assertIn("Pokémon", raw)
                self.assertIn("config_schema_version", raw)
            finally:
                if previous is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = previous


if __name__ == "__main__":
    unittest.main()
