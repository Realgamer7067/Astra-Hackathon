#!/usr/bin/env python3
"""Conservative on-demand GitHub merge guard for the independent reviewer."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", help="GitHub PR number")
    parser.add_argument("--execute", action="store_true", help="Actually merge; default is a dry-run")
    parser.add_argument("--reviewed-sha", help="Full head commit inspected by the reviewer")
    args = parser.parse_args()
    if not args.pr.isdigit():
        print("PR must be a numeric ID", file=sys.stderr)
        return 2
    fields = "number,state,isDraft,baseRefName,mergeable,mergeStateStatus,reviewDecision,headRefOid,statusCheckRollup"
    result = gh("pr", "view", args.pr, "--json", fields)
    if result.returncode:
        print(f"Cannot inspect PR #{args.pr}: {result.stderr.strip()}", file=sys.stderr)
        return 1
    try:
        pr = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("GitHub returned invalid PR JSON", file=sys.stderr)
        return 1

    blockers: list[str] = []
    if pr.get("state") != "OPEN" or pr.get("isDraft"):
        blockers.append("PR must be open and not draft")
    if pr.get("baseRefName") != "main":
        blockers.append("Only PRs targeting main are supported")
    if pr.get("mergeable") != "MERGEABLE":
        blockers.append("GitHub reports conflicts or unknown mergeability")
    if pr.get("reviewDecision") != "APPROVED":
        blockers.append("A formal non-author GitHub approval is required")
    if pr.get("mergeStateStatus") != "CLEAN":
        blockers.append("PR is not CLEAN under GitHub merge policy")
    if not pr.get("statusCheckRollup"):
        blockers.append("No status checks found; configure CI / branch protection first")
    sha = pr.get("headRefOid")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        blockers.append("Cannot verify the exact PR head commit")

    if args.execute and not args.reviewed_sha:
        blockers.append("Supply the commit you inspected with --reviewed-sha")
    if args.reviewed_sha and args.reviewed_sha != sha:
        blockers.append("PR head differs from the reviewed commit. Review the new diff.")

    checks = gh("pr", "checks", args.pr, "--required")
    if checks.returncode:
        blockers.append("Required checks have not passed or are not configured")

    if blockers:
        print(f"PR #{args.pr}: merge BLOCKED")
        for item in blockers:
            print(f"  - {item}")
        if checks.stdout.strip():
            print(checks.stdout.strip())
        return 1

    command = ["pr", "merge", args.pr, "--squash", "--delete-branch", "--match-head-commit", sha]
    print(f"Preflight passed for PR #{args.pr} at {sha}")
    if not args.execute:
        print("Dry run only. Re-run with --execute --reviewed-sha <SHA> after reviewing this commit.")
        return 0
    merge = gh(*command)
    if merge.stdout.strip():
        print(merge.stdout.strip())
    if merge.returncode:
        print(f"Merge failed; do not bypass: {merge.stderr.strip()}", file=sys.stderr)
        return merge.returncode
    print(f"GitHub accepted merge for PR #{args.pr}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

