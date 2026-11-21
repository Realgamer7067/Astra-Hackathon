#!/usr/bin/env python3
"""Git-friendly task card operations; never commits/pushes automatically."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "tasks"
STATES = ("planned", "ready", "active", "review", "blocked", "done")


def find_card(task_id: str, root: Path = ROOT) -> tuple[str, Path]:
    if not re.fullmatch(r"TASK-\d{3,}", task_id):
        raise ValueError("Use an ID such as TASK-001")
    results = [(state, file) for state in STATES for file in (root / state).glob(f"{task_id}-*.md")]
    if len(results) != 1:
        raise ValueError(f"Expected exactly one card for {task_id}; found {len(results)}")
    return results[0]


def new_card(task_id: str, title: str, root: Path = ROOT) -> Path:
    if not re.fullmatch(r"TASK-\d{3,}", task_id):
        raise ValueError("Use an ID such as TASK-001")
    if "\n" in title or "\r" in title:
        raise ValueError("Task title must be a single line")
    if any(any((root / state).glob(f"{task_id}-*.md")) for state in STATES):
        raise ValueError(f"{task_id} already exists")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    if not slug:
        raise ValueError("Title must contain letters or numbers")
    content = (root / "_TEMPLATE.md").read_text(encoding="utf-8")
    content = content.replace("TASK-XXX: Short, user-visible feature title", f"{task_id}: {title}")
    dest = root / "planned" / f"{task_id}-{slug}.md"
    if dest.exists():
        raise ValueError(f"Task already exists at {dest}")
    dest.write_text(content, encoding="utf-8")
    return dest


def relocate(task_id: str, state_to: str, owner: str | None = None, reason: str | None = None, root: Path = ROOT) -> Path:
    if owner and ("\n" in owner or "\r" in owner):
        raise ValueError("Owner must be a single line")
    if reason and ("\n" in reason or "\r" in reason):
        raise ValueError("Blocked reason must be a single line")
    state_from, source = find_card(task_id, root)
    if state_from == state_to:
        raise ValueError(f"{task_id} is already {state_to}")
    if state_to == "active" and (state_from != "ready" or not owner):
        raise ValueError("Claim from ready using --owner <human-name>")
    if state_to == "blocked" and not reason:
        raise ValueError("Moving a task to blocked requires --reason")
    content = source.read_text(encoding="utf-8")
    if state_to == "ready":
        if "Exact user-observable outcome" in content or "Describe the exact user-visible result" in content:
            raise ValueError("Fill concrete acceptance criteria and target behavior before promoting to ready")
        content = re.sub(r"(?m)^- \*\*Owner:\*\* .+$", "- **Owner:** unclaimed", content)
    elif state_to == "active":
        content, count = re.subn(r"(?m)^- \*\*Owner:\*\* .+$", f"- **Owner:** {owner}", content)
        if count != 1:
            raise ValueError("Task has no unique Owner field")
    elif state_to in ("review", "done") and "**Owner:** unclaimed" in content:
        raise ValueError("Cannot review/complete an unclaimed task")
    if state_to == "done" and "- **PR:** none" in content:
        raise ValueError("Add a verified merged PR reference to card before marking done")
    if reason:
        content = content.rstrip() + f"\n\n- Blocked reason: {reason}\n"
    target = root / state_to / source.name
    if target.exists():
        raise ValueError(f"Destination already exists: {target}")
    target.write_text(content, encoding="utf-8")
    source.unlink()
    return target


def list_cards(root: Path = ROOT) -> str:
    rows: list[str] = []
    for state in STATES:
        for card in sorted((root / state).glob("TASK-*.md")):
            content = card.read_text(encoding="utf-8")
            title = content.splitlines()[0].removeprefix("# ")
            match = re.search(r"(?m)^- \*\*Owner:\*\* (.+)$", content)
            owner = match.group(1) if match else "(unknown)"
            rows.append(f"{state:7} | {owner:16} | {title}")
    return "\n".join(rows) or "No task cards yet. Main agent: run kickoff and create cards."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    n = sub.add_parser("new")
    n.add_argument("id")
    n.add_argument("--title", required=True)
    c = sub.add_parser("claim")
    c.add_argument("id")
    c.add_argument("--owner", required=True)
    m = sub.add_parser("move")
    m.add_argument("id")
    m.add_argument("--to", required=True, choices=STATES)
    m.add_argument("--reason")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "list":
            print(list_cards())
        elif args.cmd == "new":
            print(new_card(args.id, args.title))
        elif args.cmd == "claim":
            print(relocate(args.id, "active", owner=args.owner))
        else:
            print(relocate(args.id, args.to, reason=args.reason))
    except (ValueError, OSError) as exc:
        print(f"Task operation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

