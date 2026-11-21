#!/usr/bin/env python3
"""Generate a compact, read-only snapshot of a hackathon repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "target",
    "vendor",
    ".ssh", ".aws", ".azure", ".config", "secrets", "credentials",
}
MANIFESTS = {
    "package.json": "Node/JavaScript",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "Yarn",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "pubspec.yaml": "Flutter/Dart",
    "composer.json": "PHP",
}
PROJECT_DOCS = [
    "HACKATHON.md",
    "HACKATHON_STATE.md",
    "RUBRIC.md",
    "BUILD_PLAN.md",
    "ARCHITECTURE.md",
    "COMPETITION.md",
    "DEMO.md",
    "PITCH.md",
    "SUBMISSION.md",
    "POST_HACKATHON.md",
]
DEPLOY_FILES = [
    "vercel.json",
    "netlify.toml",
    "railway.json",
    "render.yaml",
    "wrangler.toml",
    "fly.toml",
    "Dockerfile",
    ".openai/hosting.json",
]


def git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(root), *args],
            text=True,
            encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def walk_files(root: Path):
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS and not name.startswith(".cache")
                         and not (Path(current) / name).is_symlink())
        for name in sorted(files):
            path = Path(current) / name
            if path.is_file() and not path.is_symlink():
                yield path


def find_todos(root: Path, limit: int) -> tuple[int, list[dict[str, object]]]:
    pattern = re.compile(r"\b(TODO|FIXME|HACK)\b", re.I)
    count = 0
    samples = []
    for path in walk_files(root):
        if path.name.startswith(".env") or path.suffix.lower() not in {".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".rs", ".go", ".c", ".cpp", ".h", ".java", ".sh"}:
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                count += 1
                if len(samples) < limit:
                    samples.append(
                        {
                            "path": path.relative_to(root).as_posix(),
                            "line": number,
                            "marker": pattern.search(line).group().upper(),
                        }
                    )
    return count, samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect repository, manifests, hackathon docs, Git state, and TODO markers."
    )
    parser.add_argument("root", nargs="?", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--recent", type=int, default=5, help="number of recent commits (default: 5)")
    parser.add_argument("--max-todos", type=int, default=10, help="maximum TODO samples")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    files = list(walk_files(root))
    relative = {path.relative_to(root).as_posix() for path in files}
    manifests = [
        {"path": name, "ecosystem": MANIFESTS[Path(name).name]}
        for name in sorted(relative)
        if Path(name).name in MANIFESTS
    ]
    docs = {name: (name in relative) for name in PROJECT_DOCS}
    deploy = [name for name in DEPLOY_FILES if name in relative]
    env_examples = sorted(
        name for name in relative if name.endswith((".env.example", "env.example", ".env.sample"))
    )
    todo_count, todo_samples = find_todos(root, max(0, args.max_todos))
    git_root = git(root, "rev-parse", "--show-toplevel")
    own_repo = git_root is not None and Path(git_root).resolve() == root
    branch = git(root, "branch", "--show-current") if own_repo else None
    status = git(root, "status", "--short") if own_repo else None
    recent = git(root, "log", f"-{max(0, args.recent)}", "--pretty=format:%h %cs") if own_repo else None
    result = {
        "root": str(root),
        "file_count_excluding_build_and_vendor_dirs": len(files),
        "git": {
            "repository": own_repo,
            "parent_repository_detected": git_root is not None and not own_repo,
            "branch": branch,
            "dirty_entries": status.splitlines() if status else [],
            "recent_commits": recent.splitlines() if recent else [],
        },
        "manifests": manifests,
        "hackathon_documents": docs,
        "deployment_files": deploy,
        "environment_examples": env_examples,
        "todo_count": todo_count,
        "todo_samples": todo_samples,
        "next_checks": [
            "read repository instructions and state files",
            "recalculate the authoritative deadline",
            "run the application and Golden Path when useful",
            "verify deployment and submission externally",
        ],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"# Project snapshot: {root.name}")
        print(f"Files inspected: {len(files)}")
        print(f"Git branch: {branch or 'not detected'}")
        print(f"Dirty entries: {len(result['git']['dirty_entries'])}")
        print("Manifests: " + (", ".join(item["path"] for item in manifests) or "none detected"))
        print("Deployment config: " + (", ".join(deploy) or "none detected"))
        present_docs = [name for name, present in docs.items() if present]
        missing_docs = [name for name, present in docs.items() if not present]
        print("Hackathon docs present: " + (", ".join(present_docs) or "none"))
        print("Hackathon docs missing: " + (", ".join(missing_docs) or "none"))
        print(f"TODO/FIXME/HACK markers: {todo_count}")
        for item in todo_samples:
            print(f"- {item['path']}:{item['line']} {item['marker']}")
        if result["git"]["recent_commits"]:
            print("Recent commits:")
            for line in result["git"]["recent_commits"]:
                print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
