import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "App"))

from pokemon_engine import update_s1  # noqa: E402


class GeneratorTests(unittest.TestCase):
    def test_update_creates_index_and_print_action(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            s1 = root / "S1"
            s1.mkdir(parents=True)
            image_path = s1 / "Pikachu.png"
            Image.new("RGBA", (20, 20), (255, 220, 0, 255)).save(image_path)

            result = update_s1(root)

            self.assertEqual(result["active_count"], 1)
            self.assertTrue((root / "Index" / "pokemon-index.md").is_file())
            self.assertTrue((root / "Index" / "pokemon-index.json").is_file())
            html = (root / "Pokemon-Bilder-Auswahl.html").read_text(encoding="utf-8")
            self.assertIn("Druckauftrag starten", html)
            self.assertIn("<meta charset=\"utf-8\">", html.casefold())


if __name__ == "__main__":
    unittest.main()
