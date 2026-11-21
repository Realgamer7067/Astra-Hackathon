"""Tests for task card management in a temporary task tree."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tasks  # noqa: E402


class TaskBoardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for state in tasks.STATES:
            (self.root / state).mkdir()
        (self.root / "_TEMPLATE.md").write_text(
            "# TASK-XXX: Short, user-visible feature title\n"
            "\n- **Owner:** unclaimed\n- **PR:** none\n"
            "\n## Acceptance criteria\n\n- [ ] Exact user-observable outcome 1\n",
            encoding="utf-8",
        )

    def test_new_and_claim_require_ready(self):
        card = tasks.new_card("TASK-001", "Landing page", self.root)
        self.assertIn("planned", str(card))
        with self.assertRaises(ValueError):
            tasks.relocate("TASK-001", "active", owner="alex", root=self.root)
        card.write_text(card.read_text().replace("Exact user-observable outcome 1", "Landing page opens on mobile"), encoding="utf-8")
        tasks.relocate("TASK-001", "ready", root=self.root)
        active = tasks.relocate("TASK-001", "active", owner="alex", root=self.root)
        self.assertIn("**Owner:** alex", active.read_text())

    def test_duplicate_id_rejected(self):
        tasks.new_card("TASK-007", "Demo", self.root)
        with self.assertRaises(ValueError):
            tasks.new_card("TASK-007", "Other", self.root)

    def test_short_filename_can_be_claimed_and_blocks_duplicate_creation(self):
        card = self.root / "ready" / "TASK-001.md"
        card.write_text("# TASK-001: Foundation\n\n- **Owner:** unclaimed\n", encoding="utf-8")

        active = tasks.relocate("TASK-001", "active", owner="alex", root=self.root)
        self.assertEqual(active, self.root / "active" / card.name)
        self.assertIn("**Owner:** alex", active.read_text(encoding="utf-8"))
        self.assertFalse(card.exists())
        with self.assertRaisesRegex(ValueError, "already exists"):
            tasks.new_card("TASK-001", "Duplicate", self.root)

    def test_blocked_requires_reason(self):
        tasks.new_card("TASK-002", "API", self.root)
        with self.assertRaises(ValueError):
            tasks.relocate("TASK-002", "blocked", root=self.root)
        blocked = tasks.relocate("TASK-002", "blocked", reason="waiting for DB", root=self.root)
        self.assertIn("waiting for DB", blocked.read_text())


if __name__ == "__main__":
    unittest.main()

