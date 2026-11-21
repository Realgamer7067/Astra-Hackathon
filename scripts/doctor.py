#!/usr/bin/env python3
"""Cross-platform onboarding and tool/adapter checks; optional confirmed installers."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ("claude", "codex", "opencode", "gemini", "agy", "cursor")


def install_command(binary: str) -> list[str] | None:
    system = platform.system().lower()
    if system == "windows" and shutil.which("winget"):
        ids = {"git": "Git.Git", "gh": "GitHub.cli"}
        return ["winget", "install", "--id", ids[binary], "--exact", "--source", "winget"]
    if system == "linux" and shutil.which("pacman"):
        packages = {"git": "git", "gh": "github-cli"}
        return ["sudo", "pacman", "-S", "--needed", packages[binary]]
    if system == "darwin" and shutil.which("brew"):
        return ["brew", "install", binary]
    return None


def run_optional_installer(binary: str) -> None:
    command = install_command(binary)
    if not command:
        print(f"No supported installer for {binary}; use your OS's official package manager")
        return
    print(f"Optional install command: {' '.join(command)}")
    response = input(f"Run this command to install {binary}? [y/N] ").strip().lower()
    if response not in ("y", "yes"):
        print("Skipped")
        return
    try:
        code = subprocess.run(command, check=False).returncode
    except OSError as exc:
        print(f"Installer failed: {exc}")
        return
    print("Installed successfully" if code == 0 else f"Install exited {code}; please check the output")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Offer to install only missing git/gh, with an explicit confirmation for each")
    parser.add_argument("--strict", action="store_true", help="Fail when git or gh is missing")
    args = parser.parse_args(argv)

    print(f"Python: {sys.version.split()[0]} / {platform.system()} {platform.release()}")
    for binary in ("git", "gh"):
        location = shutil.which(binary)
        print(f"{'OK' if location else 'MISSING'} {binary}: {location or 'not found'}")
        if not location and args.install:
            run_optional_installer(binary)

    print("\nOptional AI coding clients (you only need the ones you actually use):")
    for client in AGENTS:
        print(f"  {client:9} {'found' if shutil.which(client) else 'not detected or app-only'}")
    print("  Copilot is typically installed through a supported IDE/GitHub integration.")

    print("\nRepository entry points:")
    files = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursor/rules/repository.mdc", ".github/copilot-instructions.md")
    missing = [name for name in files if not (ROOT / name).is_file()]
    for name in files:
        print(f"  {'OK' if name not in missing else 'MISSING'} {name}")
    print("\nShared skills: see .agents/skills/README.md for bundled snapshots; verify discovery in your chosen agent.")
    for path in (".agents/skills", ".claude/skills", ".opencode/skills", ".gemini/skills", ".cursor/skills"):
        directory = ROOT / path
        if directory.exists():
            print(f"  {path}: installed locally; verify discovery in your chosen agent")
    print("Cloud agent setup: verify it can access this repo and GitHub PRs; instructions alone cannot authenticate.")

    if missing:
        return 1
    if args.strict and (not shutil.which("git") or not shutil.which("gh")):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

