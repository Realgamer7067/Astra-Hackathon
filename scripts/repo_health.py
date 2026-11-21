#!/usr/bin/env python3
"""Dependency-free structural checks for the stack-agnostic starter."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATES = ("planned", "ready", "active", "review", "blocked", "done")
REQUIRED = (
    "README.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".gitignore",
    ".github/workflows/repo-health.yml", ".github/pull_request_template.md",
    ".github/copilot-instructions.md", ".cursor/rules/repository.mdc",
    "docs/WORKFLOW.md", "docs/PROJECT_BRIEF.md", "docs/ARCHITECTURE.md",
    "docs/CONTRACTS.md", "docs/DECISIONS.md", "docs/QUALITY.md",
    "docs/REVIEW_POLICY.md", "docs/GITHUB_SETUP.md", "docs/DEMO.md",
    "tasks/_TEMPLATE.md", "prompts/KICKOFF.md", "prompts/MAIN_AGENT.md",
    "prompts/TEAMMATE_AGENT.md", "prompts/REVIEW_AGENT.md",
    "prompts/REVIEW_ALL_PRS.md", "scripts/run_project_checks.py",
)
ID_RE = re.compile(r"^(TASK-\d{3,})(?:-[a-z0-9-]+)?\.md$")


def inspect(root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    for item in REQUIRED:
        if not (root / item).is_file():
            issues.append(f"Missing required file: {item}")

    adapters = {
        "CLAUDE.md": "@AGENTS.md",
        "GEMINI.md": "AGENTS.md",
        ".cursor/rules/repository.mdc": "AGENTS.md",
        ".github/copilot-instructions.md": "AGENTS.md",
    }
    for file, token in adapters.items():
        path = root / file
        if path.is_file() and token not in path.read_text(encoding="utf-8"):
            issues.append(f"Adapter {file} must reference {token}")

    known: dict[str, str] = {}
    for status in STATES:
        directory = root / "tasks" / status
        if not directory.is_dir():
            issues.append(f"Missing task status directory: tasks/{status}/")
            continue
        for card in directory.glob("*.md"):
            match = ID_RE.fullmatch(card.name)
            if not match:
                issues.append(f"Invalid task filename: {card.relative_to(root)}")
                continue
            task_id = match.group(1)
            if task_id in known:
                issues.append(f"Duplicate task ID {task_id}: {known[task_id]} and {card.relative_to(root)}")
            known[task_id] = str(card.relative_to(root))
            content = card.read_text(encoding="utf-8")
            if not content.startswith(f"# {task_id}:"):
                issues.append(f"Task heading must match filename: {card.relative_to(root)}")
            owner = re.search(r"(?m)^- \*\*Owner:\*\* (.+)$", content)
            if owner is None:
                issues.append(f"Task missing Owner: {card.relative_to(root)}")
            elif status in ("active", "review", "done") and owner.group(1).strip().lower() == "unclaimed":
                issues.append(f"Task in {status} must have a claimed owner: {card.relative_to(root)}")
            elif status == "ready" and owner.group(1).strip().lower() != "unclaimed":
                issues.append(f"Ready task should be unclaimed: {card.relative_to(root)}")
            if status == "ready":
                if "## Acceptance criteria" not in content or "- [ ]" not in content:
                    issues.append(f"Ready task needs concrete acceptance criteria: {card.relative_to(root)}")
                if "Exact user-observable outcome" in content or "Describe the exact user-visible result" in content:
                    issues.append(f"Ready task still contains placeholders: {card.relative_to(root)}")
    return issues


def main() -> int:
    issues = inspect()
    if issues:
        print("Repository health: FAILED")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    count = sum(len(list((ROOT / "tasks" / status).glob("*.md"))) for status in STATES)
    print(f"Repository health: PASSED ({count} task cards; no stack assumed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

