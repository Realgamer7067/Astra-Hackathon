"""Regression tests from the independent ZIP refinement; no network access."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

def run(name, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)],
                          capture_output=True, text=True, timeout=10)

class EdgeCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def ideas(self, data, *args):
        return run("score-ideas.py", self.put("ideas.json", json.dumps(data)), *args, "--json")

    def rubric(self, rows, *args):
        header = "| Criterion | Weight | What Judges Want | Our Evidence | Demo Moment | Current Strength | Missing Work |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        return run("rubric-audit.py", self.put("RUBRIC.md", header + rows), *args, "--json")

    def test_missing_scores_fail_closed(self):
        self.assertEqual(self.ideas([{"name":"Unassessed", "scores":{"rubric_fit":10}}]).returncode, 2)

    def test_partial_scoring_penalizes_unknown_risk(self):
        result = self.ideas([{"name":"Unassessed", "scores":{"rubric_fit":10}}], "--allow-missing")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["ranking"][0]["contributions"]["failure_risk"], -10)
        self.assertTrue(data["provisional"])

    def test_invalid_idea_values_are_rejected(self):
        for field, value in [("fatal_pass", "false"), ("name", None), ("eligible", 0)]:
            with self.subTest(field=field):
                item = {"name":"Valid", "scores":{}, field:value}
                self.assertEqual(self.ideas([item], "--allow-missing").returncode, 2)
        for value in [float("nan"), float("inf"), True]:
            with self.subTest(weight=value):
                self.assertEqual(self.ideas({"weights":{"rubric_fit":value},"ideas":[{"name":"A","scores":{}}]}, "--allow-missing").returncode, 2)

    def test_top_must_be_positive(self):
        for value in [0, -1]:
            self.assertEqual(self.ideas([{"name":"A","scores":{}}], "--top", value, "--allow-missing").returncode, 2)

    def test_no_eligible_ideas_is_not_success(self):
        result = self.ideas([{"name":"A","scores":{},"fatal_pass":False}], "--allow-missing")
        self.assertEqual(result.returncode, 1)

    def test_unknown_weights_do_not_invent_readiness(self):
        result = self.rubric("| Innovation | UNKNOWN | New | proof | result | 5 | none |\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(json.loads(result.stdout)["readiness_percent"])
        self.assertEqual(self.rubric("| Innovation | UNKNOWN | New | proof | result | 5 | none |\n", "--fail-below", 90).returncode, 1)

    def test_bad_rubric_numbers_fail_clearly(self):
        for weight, strength in [("-40%", "4"), ("40%", "-1"), ("40%", "6"), ("about 40%", "4")]:
            with self.subTest(weight=weight, strength=strength):
                result = self.rubric(f"| Innovation | {weight} | New | proof | result | {strength} | next |\n")
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)

    def test_escaped_pipe_does_not_shift_rubric(self):
        result = self.rubric("| Innovation | 100% | New | source \\| demo | result | 4 | improve |\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["readiness_percent"], 80)

    def test_short_and_extra_rubric_rows_rejected(self):
        for row in ["| Innovation | 100% |", "| Innovation | 100% | New | proof | result | 4 | next | extra |"]:
            self.assertEqual(self.rubric(row+"\n").returncode, 2)

    def test_partial_weight_total_blocks_threshold(self):
        result = self.rubric("| Innovation | 40% | New | proof | result | 5 | none |\n", "--fail-below", 90)
        self.assertEqual(result.returncode, 1)
        self.assertIsNone(json.loads(result.stdout)["readiness_percent"])

    def test_custom_submission_path_replaces_default(self):
        self.put("CUSTOM.md", "# Submission\nStatus: submitted\n")
        result = run("submission-audit.py", self.root, "--submission", "CUSTOM.md", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("SUBMISSION.md", json.loads(result.stdout)["required_files"])

    def test_empty_or_directory_deliverables_fail(self):
        self.put("SUBMISSION.md", "Status: submitted\n")
        self.put("video.mp4", "")
        (self.root / "screenshots").mkdir()
        for target in ["video.mp4", "screenshots"]:
            self.assertEqual(run("submission-audit.py", self.root, "--minimal", "--require", target).returncode, 1)

    def test_submission_unknown_root_and_traversal_fail(self):
        for args in [(self.root / "absent",), (self.root, "--submission", "../outside.md")]:
            self.assertEqual(run("submission-audit.py", *args).returncode, 2)

    def test_submission_saved_draft_is_not_submitted(self):
        for value in ["draft", "saved", "pending", ""]:
            self.put("SUBMISSION.md", f"# Submission\nStatus: {value}\n")
            self.assertEqual(run("submission-audit.py", self.root, "--minimal").returncode, 1)

    def test_submission_unknown_late_edits_is_warning(self):
        self.put("SUBMISSION.md", "Status: submitted\n- Late edits allowed: UNKNOWN\n")
        self.assertEqual(run("submission-audit.py", self.root, "--minimal").returncode, 0)

    def test_deadline_at_cutoff_is_expired(self):
        result = run("deadline-audit.py", "2026-01-01T00:00:00Z", "--now", "2026-01-01T00:00:00Z", "--json")
        self.assertEqual(result.returncode, 1)

    def test_deadline_date_only_and_dst_ambiguity_rejected(self):
        for timestamp in ["2026-11-01T01:30:00", "2026-03-08T02:30:00", "2026-01-01"]:
            with self.subTest(timestamp=timestamp):
                self.assertEqual(run("deadline-audit.py", timestamp, "--timezone", "America/New_York").returncode, 2)

    def test_deadline_conflicting_fields_rejected(self):
        path = self.put("HACKATHON.md", "Deadline: 2026-01-01T01:00:00Z\nDeadline: 2026-01-01T03:00:00Z\n")
        self.assertEqual(run("deadline-audit.py", "--from-file", path).returncode, 2)

    def test_status_never_echoes_source_or_reads_sensitive_files(self):
        self.put(".env", "# TODO: SYNTHETIC_SECRET_NEVER_REAL\n")
        self.put("app.py", "# TODO: SYNTHETIC_SOURCE_TOKEN\n")
        result = run("project-status.py", self.root, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("SYNTHETIC_", result.stdout)
        self.assertEqual(json.loads(result.stdout)["todo_count"], 1)

    def test_status_finds_nested_manifests(self):
        self.put("apps/web/package.json", "{}")
        result = run("project-status.py", self.root, "--json")
        self.assertIn("apps/web/package.json", [r["path"] for r in json.loads(result.stdout)["manifests"]])

    def test_status_skips_file_symlinks(self):
        target = self.put("target.txt", "TODO: external\n")
        try:
            (self.root / "alias.py").symlink_to(target)
        except OSError:
            self.skipTest("symlink privilege unavailable")
        result = run("project-status.py", self.root, "--json")
        self.assertEqual(json.loads(result.stdout)["todo_count"], 1)

    def test_invalid_utf8_is_a_clear_error(self):
        path = self.root / "bad.md"
        path.write_bytes(b"\xff")
        for name, args in [("rubric-audit.py", [path]), ("score-ideas.py", [path]),
                           ("deadline-audit.py", ["--from-file", path]),
                           ("submission-audit.py", [self.root, "--submission", "bad.md", "--minimal"])]:
            result = run(name, *args)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_exact_custom_weights_and_duplicate_names(self):
        data = {"weights":{"innovation":40,"implementation":30,"impact":20,"presentation":10},
                "ideas":[{"name":"A","fatal_pass":True,"scores":{"innovation":8,"implementation":7,"impact":7,"presentation":6}}]}
        result = self.ideas(data, "--replace-weights")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["ranking"][0]["score"], 730)
        data["ideas"].append(data["ideas"][0])
        self.assertEqual(self.ideas(data, "--replace-weights").returncode, 2)

    def test_scoring_overflow_has_clear_error(self):
        result = self.ideas({"weights":{"a":1e308},"ideas":[{"name":"A","scores":{"a":10}}]}, "--replace-weights")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_submission_table_checks_status_and_judge_view(self):
        header = "Status: submitted\n\n| Item | Status | Verified from judge view |\n| --- | --- | --- |\n"
        for status, verified, expected in [("ready", "NO", 1), ("pending", "YES", 1), ("ready", "YES", 0), ("N/A — not required by official rules", "NO", 0)]:
            self.put("SUBMISSION.md", header+f"| Video | {status} | {verified} |\n")
            result = run("submission-audit.py", self.root, "--minimal")
            self.assertEqual(result.returncode, expected, result.stdout)

    def test_rubric_weights_not_silently_converted(self):
        result = self.rubric("| A | 1 | proof | source | demo | 5 | none |\n| B | 99 | proof | source | demo | 0 | fix |\n")
        self.assertEqual(json.loads(result.stdout)["readiness_percent"], 1)

    def test_india_offset_deadline(self):
        result = run("deadline-audit.py", "2026-09-12T18:00:00+05:30", "--now", "2026-09-12T10:30:00Z", "--json")
        self.assertEqual(json.loads(result.stdout)["hours_remaining"], 2)

if __name__ == "__main__":
    unittest.main()
