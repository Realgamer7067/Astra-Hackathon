"""The reviewer merge helper must fail closed and never merge by default."""

import json
import sys
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import merge_checked  # noqa: E402


def gh_result(payload, code=0):
    return CompletedProcess(args=["gh"], returncode=code, stdout=payload, stderr="")


class MergeGuardTests(unittest.TestCase):
    def setUp(self):
        self.pr = {
            "number": 4, "state": "OPEN", "isDraft": False, "baseRefName": "main",
            "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN", "reviewDecision": "APPROVED",
            "headRefOid": "a" * 40, "statusCheckRollup": [{"name": "verify", "conclusion": "SUCCESS"}],
        }

    def test_default_only_dry_runs(self):
        with patch.object(sys, "argv", ["merge_checked.py", "4"]), patch.object(merge_checked, "gh", side_effect=[gh_result(json.dumps(self.pr)), gh_result("checks ok")]) as mocked:
            self.assertEqual(0, merge_checked.main())
            self.assertEqual(2, mocked.call_count)  # No gh pr merge

    def test_execute_binds_review_to_commit(self):
        for reviewed, expected in [(None, 1), ("b" * 40, 1), ("a" * 40, 0)]:
            argv = ["merge_checked.py", "4", "--execute"]
            if reviewed:
                argv.extend(["--reviewed-sha", reviewed])
            responses = [gh_result(json.dumps(self.pr)), gh_result("checks ok"), gh_result("merged")]
            with self.subTest(reviewed=reviewed), patch.object(sys, "argv", argv), patch.object(merge_checked, "gh", side_effect=responses) as mocked:
                self.assertEqual(expected, merge_checked.main())
                if expected:
                    self.assertEqual(2, mocked.call_count)
                else:
                    mocked.assert_called_with("pr", "merge", "4", "--squash", "--delete-branch", "--match-head-commit", reviewed)

    def test_refuses_missing_approval(self):
        self.pr["reviewDecision"] = "REVIEW_REQUIRED"
        with patch.object(sys, "argv", ["merge_checked.py", "4", "--execute", "--reviewed-sha", "a" * 40]), patch.object(merge_checked, "gh", side_effect=[gh_result(json.dumps(self.pr)), gh_result("checks ok")]) as mocked:
            self.assertEqual(1, merge_checked.main())
            self.assertEqual(2, mocked.call_count)

    def test_refuses_failing_required_checks(self):
        with patch.object(sys, "argv", ["merge_checked.py", "4", "--execute", "--reviewed-sha", "a" * 40]), patch.object(merge_checked, "gh", side_effect=[gh_result(json.dumps(self.pr)), gh_result("", code=1)]) as mocked:
            self.assertEqual(1, merge_checked.main())
            self.assertEqual(2, mocked.call_count)


if __name__ == "__main__":
    unittest.main()

