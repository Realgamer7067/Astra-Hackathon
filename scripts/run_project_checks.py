#!/usr/bin/env python3
"""Run project-specific CI commands after stack selection; no shell interpolation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CHECKS = ("format", "lint", "typecheck", "unit", "integration", "security", "build")
SOURCE_DIRS = ("apps", "src", "packages", "frontend", "backend", "api", "web", "services", "client", "server")
SOURCE_FILES = ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "requirements.txt", "app.py", "main.py")


def app_code_exists(root: Path) -> bool:
    return any((root / name).exists() for name in SOURCE_DIRS + SOURCE_FILES)


def validate_config(value: object) -> dict[str, list[str]]:
    if not isinstance(value, dict) or not isinstance(value.get("commands"), dict):
        raise ValueError("Expected JSON object containing 'commands' mapping")
    commands = value["commands"]
    missing = [name for name in REQUIRED_CHECKS if name not in commands]
    if missing:
        raise ValueError(f"Missing mandatory checks: {', '.join(missing)}")
    for name, args in commands.items():
        if not isinstance(name, str) or not isinstance(args, list) or not args or not all(isinstance(x, str) and x.strip() for x in args):
            raise ValueError(f"Check {name!r} must be a nonempty array of nonempty argv strings")
        if args[0] in ("echo", "true", "false") or any("PLACEHOLDER" in a or "<" in a for a in args):
            raise ValueError(f"Check {name!r} appears to be a placeholder, not a real check")
    return commands


def main() -> int:
    config_file = ROOT / "project-checks.json"
    if not config_file.exists():
        if app_code_exists(ROOT):
            print("FAIL: application code exists but project-checks.json is missing; configure it before coding")
            return 1
        print("Project checks: not configured because template contains no app code (expected at startup)")
        return 0

    try:
        commands = validate_config(json.loads(config_file.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid project-checks.json: {exc}")
        return 1

    for name, args in commands.items():
        print(f"Running {name}: {' '.join(args)}", flush=True)
        try:
            result = subprocess.run(args, cwd=ROOT, timeout=300, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"FAILED {name}: {exc}")
            return 1
        if result.returncode:
            print(f"FAILED {name}: exit {result.returncode}")
            return result.returncode
        print(f"PASS {name}", flush=True)
    print("All configured project checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

