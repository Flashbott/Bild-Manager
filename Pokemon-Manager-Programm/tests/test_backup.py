import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "App"))

from pokemon_backup import create_backup, list_backups, restore_backup, verify_backup  # noqa: E402


class BackupTests(unittest.TestCase):
    def test_backup_verify_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "S1").mkdir()
            (root / "Index").mkdir()
            (root / "S1" / "Pikachu.png").write_bytes(b"original-image")
            (root / "Index" / "pokemon-index.json").write_text(
                '{"active": 1}\n', encoding="utf-8"
            )
            (root / "Pokemon-Bilder-Auswahl.html").write_text(
                "<html>original</html>\n", encoding="utf-8"
            )

            backup = create_backup(root, "Teststand", "0.3.0", {"language": "de"})
            self.assertTrue(backup.valid)
            self.assertEqual(verify_backup(backup.path)["file_count"], 3)
            self.assertEqual(len(list_backups(root)), 1)

            (root / "S1" / "Pikachu.png").write_bytes(b"changed-image")
            (root / "Index" / "pokemon-index.json").write_text(
                '{"active": 99}\n', encoding="utf-8"
            )
            (root / "Pokemon-Bilder-Auswahl.html").write_text(
                "<html>changed</html>\n", encoding="utf-8"
            )

            restored = restore_backup(root, backup.path)
            self.assertEqual(restored.path, backup.path)
            self.assertEqual((root / "S1" / "Pikachu.png").read_bytes(), b"original-image")
            self.assertIn("original", (root / "Pokemon-Bilder-Auswahl.html").read_text(encoding="utf-8"))
            self.assertEqual(
                json.loads((root / "Index" / "pokemon-index.json").read_text(encoding="utf-8")),
                {"active": 1},
            )

    def test_retention_keeps_five_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "S1").mkdir()
            (root / "S1" / "Pikachu.png").write_bytes(b"image")
            for index in range(6):
                create_backup(root, f"Test {index}", "0.3.0", keep=5)
            backups = list_backups(root)
            self.assertEqual(len(backups), 5)
            self.assertEqual(backups[0].reason, "Test 5")


if __name__ == "__main__":
    unittest.main()
