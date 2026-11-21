"""Run the shared foundation checks with the pinned local project environments."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
UV = shutil.which("uv") or "uv"
NPM = shutil.which("npm") or "npm"
CHECKS = {
    "format": [
        [UV, "run", "--locked", "ruff", "format", "--check", "services/api"],
        [NPM, "run", "format:check"],
    ],
    "lint": [[UV, "run", "--locked", "ruff", "check", "services/api"], [NPM, "run", "lint"]],
    "typecheck": [[UV, "run", "--locked", "mypy", "services/api/app"], [NPM, "run", "typecheck"]],
    "unit": [
        [
            UV,
            "run",
            "--locked",
            "pytest",
            "-q",
            "services/api/tests/test_models.py",
            "services/api/tests/test_collision.py",
        ],
        [NPM, "test"],
    ],
    "integration": [
        [
            UV,
            "run",
            "--locked",
            "pytest",
            "-q",
            "services/api/tests/test_api.py",
            "services/api/tests/test_scenarios.py",
        ],
        [NPM, "run", "contracts:check"],
    ],
    "security": [
        [UV, "run", "--locked", "bandit", "-q", "-r", "services/api/app"],
        [NPM, "audit", "--audit-level=high"],
    ],
    "build": [
        [UV, "run", "--locked", "python", "-m", "compileall", "-q", "services/api/app"],
        [NPM, "run", "build"],
    ],
}


def main() -> int:
    for argv in CHECKS[sys.argv[1]]:
        result = subprocess.run(argv, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
