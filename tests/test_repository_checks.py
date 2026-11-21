"""Structural and project check unit tests."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import repo_health  # noqa: E402
import run_project_checks  # noqa: E402


class RepositoryTests(unittest.TestCase):
    def test_starter_health(self):
        self.assertEqual([], repo_health.inspect(repo_health.ROOT))

    def test_missing_application_checks_detected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.assertFalse(run_project_checks.app_code_exists(root))
            (root / "src").mkdir()
            self.assertTrue(run_project_checks.app_code_exists(root))

    def test_project_config_rejects_missing_checks(self):
        with self.assertRaises(ValueError):
            run_project_checks.validate_config({"commands": {"lint": ["npm", "run", "lint"]}})

    def test_project_config_rejects_fake_checks(self):
        commands = {name: ["echo", "passed"] for name in run_project_checks.REQUIRED_CHECKS}
        with self.assertRaises(ValueError):
            run_project_checks.validate_config({"commands": commands})


if __name__ == "__main__":
    unittest.main()

