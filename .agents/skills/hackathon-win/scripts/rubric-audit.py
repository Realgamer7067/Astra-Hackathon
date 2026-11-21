#!/usr/bin/env python3
"""Audit a RUBRIC.md evidence table and rank scoring gaps."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path


REQUIRED = [
    "criterion",
    "weight",
    "what judges want",
    "our evidence",
    "demo moment",
    "current strength",
    "missing work",
]
EMPTY = {"", "-", "tbd", "todo", "unknown", "none", "n/a", "not started"}


def split_row(line: str) -> list[str]:
    return [cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def empty(value: str) -> bool:
    cleaned = re.sub(r"[`*_]", "", value).strip().lower()
    return cleaned in EMPTY


def parse_weight(value: str) -> float | None:
    text = value.strip().strip("`*").strip().lower()
    if empty(text):
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%?", text)
    if not match:
        raise ValueError(f"invalid weight {value!r}; use percentage points, e.g. 40 or 40%, or UNKNOWN")
    number = float(match.group(1))
    if not math.isfinite(number) or not 0 <= number <= 100:
        raise ValueError("weights must be between 0 and 100 percentage points")
    return number


def parse_strength(value: str) -> float:
    if empty(value):
        return 0.0
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:\s*/\s*5)?", value.strip().strip("`*"))
    if not match:
        raise ValueError(f"invalid strength {value!r}; use a number from 0 to 5")
    number = float(match.group(1))
    if not 0 <= number <= 5:
        raise ValueError("strength must be between 0 and 5")
    return number


def parse_table(path: Path) -> list[dict[str, str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    for index, line in enumerate(lines):
        if "|" not in line:
            continue
        headers = [re.sub(r"[`*_]", "", c).strip().lower() for c in split_row(line)]
        if all(name in headers for name in REQUIRED):
            rows = []
            for candidate in lines[index + 1 :]:
                if "|" not in candidate:
                    if rows:
                        break
                    continue
                cells = split_row(candidate)
                if is_separator(cells):
                    continue
                if len(cells) != len(headers):
                    raise ValueError("rubric row has wrong cell count; escape literal pipes as \\|")
                rows.append(dict(zip(headers, cells)))
            if not rows:
                print("error: rubric table has no data rows", file=sys.stderr)
                raise SystemExit(2)
            return rows
    print("error: no rubric table with the required columns was found", file=sys.stderr)
    raise SystemExit(2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit RUBRIC.md for missing evidence and weighted readiness.",
        epilog="This checks the evidence document only; it cannot verify the application or claims.",
    )
    parser.add_argument("rubric", nargs="?", type=Path, default=Path("RUBRIC.md"))
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--fail-below", type=float, metavar="PERCENT", help="exit 1 below readiness threshold"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fail_below is not None and (not math.isfinite(args.fail_below) or not 0 <= args.fail_below <= 100):
        raise ValueError("--fail-below must be between 0 and 100")
    rows = parse_table(args.rubric)
    names = [row["criterion"].strip().lower() for row in rows]
    if len(set(names)) != len(names) or any(empty(name) for name in names):
        raise ValueError("criteria must have unique non-placeholder names")
    parsed_weights = [parse_weight(row["weight"]) for row in rows]
    findings = []
    weighted_strength = 0.0
    total_weight = 0.0

    for row, parsed_weight in zip(rows, parsed_weights):
        weight = parsed_weight
        strength = parse_strength(row["current strength"])
        evidence_missing = empty(row["our evidence"])
        demo_missing = empty(row["demo moment"])
        missing_work_missing = empty(row["missing work"])
        effective = strength
        issues = []
        if evidence_missing:
            effective = min(effective, 1.0)
            issues.append("no evidence")
        if demo_missing:
            effective = min(effective, 2.0)
            issues.append("no demo moment")
        if missing_work_missing and effective < 5:
            issues.append("no next action")
        if parsed_weight is None:
            issues.append("weight unknown")
        severity = None if weight is None else weight * (5.0 - effective) / 5.0
        if weight is not None:
            weighted_strength += weight * effective / 5.0
            total_weight += weight
        findings.append(
            {
                "criterion": row["criterion"],
                "weight": weight,
                "reported_strength": strength,
                "effective_strength": effective,
                "gap_severity": None if severity is None else round(severity, 3),
                "issues": issues,
                "missing_work": row["missing work"],
            }
        )

    complete = all(w is not None for w in parsed_weights) and math.isclose(total_weight, 100, abs_tol=0.1)
    readiness = round(100.0 * weighted_strength / total_weight, 2) if complete else None
    findings.sort(key=lambda item: (item["gap_severity"] is None, item["gap_severity"] or 0), reverse=True)
    warnings = [] if complete else ["No aggregate readiness: resolve all weights and make percentage points sum to 100."]
    result = {"readiness_percent": readiness, "criteria": findings, "warnings": warnings,
              "known_weight_total": total_weight, "document_only": True}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Documented rubric readiness: " + (f"{readiness:.1f}%" if readiness is not None else "UNKNOWN"))
        for warning in warnings:
            print(f"warning: {warning}")
        print("Highest weighted gaps:")
        for item in findings:
            issues = ", ".join(item["issues"]) or "documented"
            print(
                f"- {item['criterion']}: severity {item['gap_severity']}; "
                f"strength {item['effective_strength']:.1f}/5; {issues}; "
                f"next: {item['missing_work']}"
            )
    if args.fail_below is not None and (readiness is None or readiness < args.fail_below):
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
