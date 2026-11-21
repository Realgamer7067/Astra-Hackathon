#!/usr/bin/env python3
"""Behavioral tests for hackathon-win helper scripts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )


class ScriptTests(unittest.TestCase):
    def test_every_public_script_has_help(self) -> None:
        for path in SCRIPTS.glob("*.py"):
            with self.subTest(script=path.name):
                result = run_script(path.name, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout.lower())

    def test_score_ideas_ranks_and_honors_fatal_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "ideas.json"
            base = {
                key: 5
                for key in (
                    "rubric_fit demo_impact feasibility originality visual_potential story_strength "
                    "technical_depth sponsor_fit usefulness time_to_mvp differentiation failure_risk "
                    "complexity_cost dependency_risk"
                ).split()
            }
            source.write_text(
                json.dumps(
                    {
                        "ideas": [
                            {"name": "High", "scores": {**base, "rubric_fit": 10}},
                            {"name": "Fatal", "fatal_pass": False, "scores": {k: 10 for k in base}},
                            {"name": "Low", "scores": {**base, "rubric_fit": 1}},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = run_script("score-ideas.py", str(source), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            ranking = json.loads(result.stdout)["ranking"]
            self.assertEqual(ranking[0]["name"], "High")
            self.assertFalse(ranking[-1]["fatal_pass"])

    def test_score_ideas_changes_with_event_weights(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "weighted.json"
            weights = {key: 0 for key in (
                "rubric_fit demo_impact feasibility originality visual_potential story_strength "
                "technical_depth sponsor_fit usefulness time_to_mvp differentiation failure_risk "
                "complexity_cost dependency_risk"
            ).split()}
            weights.update({"originality": 4, "technical_depth": 3, "usefulness": 2, "story_strength": 1})
            source.write_text(
                json.dumps(
                    {
                        "weights": weights,
                        "ideas": [
                            {
                                "name": "Polished commodity",
                                "scores": {
                                    "originality": 2,
                                    "technical_depth": 3,
                                    "usefulness": 6,
                                    "story_strength": 10,
                                },
                            },
                            {
                                "name": "Novel working core",
                                "scores": {
                                    "originality": 9,
                                    "technical_depth": 9,
                                    "usefulness": 7,
                                    "story_strength": 4,
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = run_script("score-ideas.py", str(source), "--strict", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            ranking = json.loads(result.stdout)["ranking"]
            self.assertEqual(ranking[0]["name"], "Novel working core")

    def test_deadline_boundaries(self) -> None:
        cases = [
            ("2026-01-02T00:00:01+00:00", ">24h"),
            ("2026-01-02T00:00:00+00:00", "12-24h"),
            ("2026-01-01T06:00:00+00:00", "6-12h"),
            ("2026-01-01T02:00:00+00:00", "1-3h"),
            ("2026-01-01T00:30:00+00:00", "<1h"),
        ]
        for deadline, expected in cases:
            with self.subTest(deadline=deadline):
                result = run_script(
                    "deadline-audit.py",
                    deadline,
                    "--now",
                    "2026-01-01T00:00:00+00:00",
                    "--json",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["mode"], expected)

    def test_rubric_audit_caps_unproven_strength(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rubric = Path(tmp) / "RUBRIC.md"
            rubric.write_text(
                "| Criterion | Weight | What Judges Want | Our Evidence | Demo Moment | Current Strength | Missing Work |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| Innovation | 40% | Novel proof | TBD | TBD | 5 | Build proof |\n"
                "| Implementation | 60% | Works | Test + demo | Result reveal | 4 | Fix edge |\n",
                encoding="utf-8",
            )
            result = run_script("rubric-audit.py", str(rubric), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            innovation = next(row for row in data["criteria"] if row["criterion"] == "Innovation")
            self.assertEqual(innovation["effective_strength"], 1.0)
            self.assertIn("no evidence", innovation["issues"])

    def test_submission_audit_incomplete_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tracker = root / "SUBMISSION.md"
            tracker.write_text("# Submission\n- [ ] Upload video\nStatus: TBD\n", encoding="utf-8")
            incomplete = run_script("submission-audit.py", str(root), "--minimal", "--json")
            self.assertEqual(incomplete.returncode, 1)
            self.assertGreater(json.loads(incomplete.stdout)["blocker_count"], 0)
            tracker.write_text("# Submission\n- [x] Upload video\nStatus: submitted\n", encoding="utf-8")
            complete = run_script("submission-audit.py", str(root), "--minimal", "--json")
            self.assertEqual(complete.returncode, 0, complete.stderr)
            self.assertEqual(json.loads(complete.stdout)["blocker_count"], 0)

    def test_project_status_is_read_only_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "README.md").write_text("TODO: demo", encoding="utf-8")
            result = run_script("project-status.py", str(root), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["todo_count"], 1)
            self.assertEqual(data["manifests"][0]["path"], "package.json")


if __name__ == "__main__":
    unittest.main()
