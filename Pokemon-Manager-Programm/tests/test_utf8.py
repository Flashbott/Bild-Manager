import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Utf8Tests(unittest.TestCase):
    def test_primary_documents_are_utf8_and_contain_german_characters(self) -> None:
        for relative in ("README.md", "App/README.md", "Gebrauchsanweisung_Pokemon-Auswahl.md"):
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertTrue(any(character in text for character in "äöüÄÖÜß"), relative)


if __name__ == "__main__":
    unittest.main()
