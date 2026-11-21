#!/usr/bin/env python3
"""Calculate hackathon time remaining and select an operating mode."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


MODES = [
    (
        ">24h",
        ["prove the riskiest assumption", "establish MVP and visual direction", "deploy a thin path"],
        ["unbounded research", "production-only infrastructure"],
    ),
    (
        "12-24h",
        ["finish MVP and primary integration", "establish UI identity", "deploy early"],
        ["speculative experiments", "broad feature expansion"],
    ),
    (
        "6-12h",
        ["finish Golden Path", "seed demo data and fallbacks", "polish and deploy"],
        ["architecture changes unless broken", "framework migration"],
    ),
    (
        "3-6h",
        ["begin feature freeze", "fix demo and rubric gaps", "capture screenshots and start pitch"],
        ["major new features", "risky schema or infrastructure changes"],
    ),
    (
        "1-3h",
        ["secure submission and fallback", "rehearse demo/pitch", "verify links and deployment"],
        ["major new features", "architecture work", "nonessential refactors"],
    ),
    (
        "<1h",
        ["submit valid version", "ensure demo opens", "capture fallback evidence"],
        ["all non-catastrophic changes", "experiments", "polish that risks stability"],
    ),
]


def parse_datetime(value: str, timezone_name: str | None) -> datetime:
    candidate = value.strip().replace("Z", "+00:00")
    if not re.search(r"[T ]\d{2}:\d{2}", candidate):
        print("error: include an explicit time, not only a date", file=sys.stderr)
        raise SystemExit(2)
    try:
        result = datetime.fromisoformat(candidate)
    except ValueError:
        print(
            f"error: {value!r} is not ISO 8601; example: 2026-09-12T18:00:00+05:30",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if result.tzinfo is None:
        if not timezone_name:
            print("error: naive time requires --timezone, for example Asia/Kolkata", file=sys.stderr)
            raise SystemExit(2)
        try:
            zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            print(f"error: timezone unavailable: {timezone_name!r}; use an explicit UTC offset or install tzdata", file=sys.stderr)
            raise SystemExit(2)
        candidates = [result.replace(tzinfo=zone, fold=fold) for fold in (0, 1)]
        valid = [dt for dt in candidates if dt.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == result]
        if not valid or len({dt.utcoffset() for dt in valid}) != 1:
            print("error: ambiguous or nonexistent local time; provide the verified UTC offset", file=sys.stderr)
            raise SystemExit(2)
        result = valid[0]
    return result


def deadline_from_file(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    pattern = re.compile(r"^\s*[-*]?\s*Deadline(?:\s*\([^)]*\))?\s*:\s*(.+?)\s*$", re.I)
    values = []
    for line in lines:
        match = pattern.match(line)
        if match and match.group(1).strip().lower() not in {"tbd", "unknown"}:
            values.append(match.group(1).strip())
    if len(set(values)) > 1:
        print("error: conflicting Deadline fields; resolve the authoritative cutoff", file=sys.stderr)
        raise SystemExit(2)
    if values:
        return values[0]
    print(f"error: no resolved 'Deadline: ...' field found in {path}", file=sys.stderr)
    raise SystemExit(2)


def select_mode(hours: float) -> tuple[str, list[str], list[str]]:
    if hours > 24:
        return MODES[0]
    if hours >= 12:
        return MODES[1]
    if hours >= 6:
        return MODES[2]
    if hours >= 3:
        return MODES[3]
    if hours >= 1:
        return MODES[4]
    return MODES[5]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate remaining time and the corresponding hackathon operating mode."
    )
    parser.add_argument("deadline", nargs="?", help="ISO 8601 deadline with UTC offset")
    parser.add_argument("--from-file", type=Path, help="read a Deadline field from HACKATHON.md")
    parser.add_argument("--timezone", help="IANA timezone for naive timestamps")
    parser.add_argument("--now", help="override current time for testing (ISO 8601)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if bool(args.deadline) == bool(args.from_file):
        print("error: provide exactly one of deadline or --from-file", file=sys.stderr)
        return 2
    deadline_text = args.deadline or deadline_from_file(args.from_file)
    deadline = parse_datetime(deadline_text, args.timezone)
    now = parse_datetime(args.now, args.timezone) if args.now else datetime.now(timezone.utc)
    hours = (deadline.astimezone(timezone.utc) - now.astimezone(timezone.utc)).total_seconds() / 3600
    expired = hours <= 0
    mode, priorities, prohibited = select_mode(max(0.0, hours))
    if expired:
        mode = "deadline-passed"
        priorities = ["verify whether late submission or organizer recovery is possible"]
        prohibited = ["new features", "unverified claims about submission status"]
    result = {
        "deadline": deadline.isoformat(),
        "now": now.isoformat(),
        "hours_remaining": round(hours, 3),
        "mode": mode,
        "priorities": priorities,
        "do_not_start": prohibited,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Deadline: {result['deadline']}")
        print(f"Remaining: {hours:.2f} hours")
        print(f"Mode: {mode}")
        print("Prioritize: " + "; ".join(priorities))
        print("Do not start: " + "; ".join(prohibited))
    return 1 if expired else 0


if __name__ == "__main__":
    raise SystemExit(main())
