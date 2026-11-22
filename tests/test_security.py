import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "App"))

from pokemon_security import AdminPinManager  # noqa: E402


class SecurityTests(unittest.TestCase):
    def test_pin_is_not_stored_in_plain_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            policy_path = Path(temporary) / "admin-policy.json"
            manager = AdminPinManager(policy_path)
            manager.set_pin("1234")
            raw = policy_path.read_text(encoding="utf-8")
            self.assertNotIn("1234", raw)
            self.assertFalse(manager.verify("0000")[0])
            self.assertTrue(manager.verify("1234")[0])

    def test_pin_format_is_strict(self) -> None:
        self.assertTrue(AdminPinManager.validate_pin("0000"))
        self.assertFalse(AdminPinManager.validate_pin("123"))
        self.assertFalse(AdminPinManager.validate_pin("12345"))
        self.assertFalse(AdminPinManager.validate_pin("12a4"))


if __name__ == "__main__":
    unittest.main()
