#!/usr/bin/env python3
"""Check local hackathon submission artifacts for obvious blockers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_FILES = [
    "README.md",
    "HACKATHON.md",
    "RUBRIC.md",
    "ARCHITECTURE.md",
    "DEMO.md",
    "PITCH.md",
    "SUBMISSION.md",
]
PLACEHOLDER = re.compile(r"\b(TBD|TODO|UNKNOWN|NOT STARTED|NOT SUBMITTED|NOT RUN)\b", re.I)
INCOMPLETE_STATUS = re.compile(r"\b(NOT STARTED|BLOCKED|MISSING|UNKNOWN|NOT SUBMITTED)\b", re.I)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit local submission documents, placeholders, and checklists.",
        epilog=(
            "This does not verify remote permissions, deployment health, video playback, or that "
            "a submission platform accepted the entry; inspect those manually."
        ),
    )
    parser.add_argument("root", nargs="?", type=Path, default=Path("."), help="project root")
    parser.add_argument(
        "--submission", default="SUBMISSION.md", help="submission tracker relative to root"
    )
    parser.add_argument(
        "--require", action="append", default=[], metavar="PATH", help="event-required nonempty regular file relative to root"
    )
    parser.add_argument(
        "--minimal", action="store_true", help="omit advisory internal-document checks"
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--no-fail", action="store_true", help="always exit zero after reporting")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise ValueError("project root must be an existing directory")
    required = list(dict.fromkeys([args.submission] + args.require))
    resolved = {}
    for name in required:
        path = (root / name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(root):
            raise ValueError("required files must be relative paths inside the project root")
        resolved[name] = path
    missing = [name for name, path in resolved.items() if not path.is_file() or path.stat().st_size == 0]
    advisory = [] if args.minimal else [name for name in DEFAULT_FILES if name != "SUBMISSION.md" and not (root / name).is_file()]

    tracker = resolved[args.submission]
    placeholders = []
    unchecked = []
    incomplete_rows = []
    warnings = []
    statuses = []
    status_column = None
    verification_column = None
    if tracker.is_file():
        try:
            lines = tracker.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            print(f"error: cannot read {tracker}: {exc}", file=sys.stderr)
            return 2
        for number, line in enumerate(lines, start=1):
            status_match = re.match(r"^\s*[-*]?\s*(?:Current )?Status\s*:\s*(.*?)\s*$", line, re.I)
            if status_match:
                statuses.append(status_match.group(1).lower())
            if re.match(r"^\s*[-*]?\s*Late edits allowed:", line, re.I) and PLACEHOLDER.search(line):
                warnings.append("Late-edit permission unknown: do not assume edits are allowed after submitting.")
                continue
            if line.strip().startswith("|"):
                cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
                lowered = [c.lower() for c in cells]
                if "status" in lowered:
                    status_column = lowered.index("status")
                    verification_column = lowered.index("verified from judge view") if "verified from judge view" in lowered else None
                    continue
                if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    continue
                if status_column is not None:
                    status_value = lowered[status_column] if status_column < len(lowered) else ""
                    if status_value.startswith("n/a") and len(status_value) > 3:
                        warnings.append(f"Line {number}: N/A exemption recorded; verify its official basis.")
                        continue
                    verified = verification_column is None or (verification_column < len(lowered) and lowered[verification_column] in {"yes", "verified", "pass"})
                    if status_value not in {"done", "ready", "complete", "submitted", "accepted", "verified"} or not verified:
                        incomplete_rows.append({"line": number, "text": line.strip()})
            else:
                status_column = verification_column = None
            if PLACEHOLDER.search(line):
                placeholders.append({"line": number, "text": line.strip()})
            if re.search(r"^\s*[-*]\s*\[\s\]", line):
                unchecked.append({"line": number, "text": line.strip()})
            if line.strip().startswith("|") and INCOMPLETE_STATUS.search(line) and not any(item["line"] == number for item in incomplete_rows):
                incomplete_rows.append({"line": number, "text": line.strip()})

    status_ok = bool(statuses) and all(status in {"submitted", "accepted", "confirmed"} for status in statuses)
    problem_lines = {item["line"] for group in (placeholders, unchecked, incomplete_rows) for item in group}
    blockers = len(missing) + len(problem_lines) + (0 if status_ok else 1)
    result = {
        "root": str(root),
        "required_files": required,
        "missing_files": missing,
        "advisory_missing_documents": advisory,
        "reported_submission_status": statuses,
        "status_recorded_as_submitted": status_ok,
        "warnings": warnings,
        "placeholder_lines": placeholders,
        "unchecked_items": unchecked,
        "incomplete_rows": incomplete_rows,
        "blocker_count": blockers,
        "manual_checks": [
            "submission accepted, not only saved",
            "deadline and track selections verified from official source",
            "repository/deployment/video permissions verified from judge view",
            "all links open and deployment is healthy",
        ],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Submission audit: {blockers} local blocker(s)")
        if missing:
            print("Missing/empty/non-file deliverables: " + ", ".join(missing))
        if not status_ok:
            print("Submission status absent, conflicting, or not submitted. A draft is not an accepted entry.")
        if advisory:
            print("Advisory only; internal docs absent: " + ", ".join(advisory))
        for warning in warnings:
            print("warning: " + warning)
        for label, values in (
            ("Placeholder", placeholders),
            ("Unchecked", unchecked),
            ("Incomplete row", incomplete_rows),
        ):
            for item in values:
                print(f"{label} line {item['line']}: {item['text']}")
        print("Manual verification still required:")
        for check in result["manual_checks"]:
            print(f"- {check}")
    if blockers and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
