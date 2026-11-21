#!/usr/bin/env python3
"""Index kernel source/history evidence with an explicit source snapshot.

By default, literal source searches use the committed tree at ``HEAD`` while
history searches use all refs. ``--working-tree`` is explicit and requires an
output file so the tracked diff, status, submodule state, and source-like
untracked files can be preserved beside the report.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass


SOURCE_SUFFIXES = {
    ".c",
    ".h",
    ".s",
    ".S",
    ".rs",
    ".dts",
    ".dtsi",
    ".dtso",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".patch",
    ".diff",
    ".sh",
    ".py",
}


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def git(tree: pathlib.Path, args: list[str], timeout: int) -> CommandResult:
    argv = ["git", "-C", str(tree), *args]
    try:
        proc = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CommandResult(argv, proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return CommandResult(argv, 124, stdout, stderr, timed_out=True)


def git_bytes(tree: pathlib.Path, args: list[str], timeout: int) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(tree), *args],
        check=False,
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode(errors="replace").strip())
    return proc.stdout


def require_git(result: CommandResult, parser: argparse.ArgumentParser, what: str) -> str:
    if result.timed_out:
        parser.error(f"{what} timed out")
    if result.returncode != 0:
        parser.error(f"{what} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def md(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def sanitize_remote(value: str) -> str:
    value = re.sub(r"(https?://)[^/@\s]+@", r"\1<redacted>@", value)
    value = re.sub(
        r"([?&](?:access_token|auth|key|password|token)=)[^&\s]+",
        r"\1<redacted>",
        value,
        flags=re.IGNORECASE,
    )
    return value


def lines(value: str) -> list[str]:
    return [line for line in value.splitlines() if line.strip()]


def limited(items: list[str], maximum: int) -> tuple[list[str], int]:
    return items[:maximum], max(0, len(items) - maximum)


def is_within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def command_note(result: CommandResult) -> str:
    if result.timed_out:
        return f"Timed out after the configured limit; results may be incomplete. {md(result.stderr)}"
    if result.returncode not in (0, 1):
        return f"Git exited {result.returncode}: {md(result.stderr)}"
    return ""


def table_rows(raw: list[str], columns: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in raw:
        parts = line.split("\x1f")
        if len(parts) < columns:
            parts += [""] * (columns - len(parts))
        rows.append(parts[:columns])
    return rows


def relevant_untracked(path: pathlib.PurePosixPath) -> bool:
    name = path.name
    return (
        name.startswith("Kconfig")
        or name.startswith("Makefile")
        or name.endswith("defconfig")
        or name.endswith(".config")
        or path.suffix in SOURCE_SUFFIXES
    )


def sha256_path(path: pathlib.Path) -> tuple[str, str]:
    if path.is_symlink():
        target = os.readlink(path)
        return hashlib.sha256(os.fsencode(target)).hexdigest(), "symlink-target"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest(), "file"


def write_atomic(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            handle.write(content)
            temp_name = pathlib.Path(handle.name)
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            temp_name.unlink(missing_ok=True)


def capture_working_tree(
    tree: pathlib.Path,
    repo_root: pathlib.Path,
    final_dir: pathlib.Path,
    timeout: int,
    head: str,
) -> dict[str, object]:
    if final_dir.exists():
        raise ValueError(f"working-tree evidence directory already exists: {final_dir}")
    final_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix=f".{final_dir.name}.", dir=final_dir.parent))
    try:
        try:
            tree_path = tree.relative_to(repo_root).as_posix() or "."
        except ValueError as exc:
            raise RuntimeError("tree is not contained by its reported Git toplevel") from exc
        pathspec = ["--", tree_path]

        status = git(repo_root, ["status", "--porcelain=v1", "-uall", *pathspec], timeout)
        tracked = git(repo_root, ["diff", "--binary", head, *pathspec], timeout)
        submodules = git(repo_root, ["submodule", "status", "--recursive", *pathspec], timeout)
        for result, name in ((status, "status"), (tracked, "tracked diff")):
            if result.returncode != 0:
                raise RuntimeError(f"cannot capture working-tree {name}: {result.stderr.strip()}")

        (temp_dir / "working-tree.status").write_text(status.stdout, encoding="utf-8")
        (temp_dir / "tracked.patch").write_text(tracked.stdout, encoding="utf-8")
        (temp_dir / "submodules.status").write_text(
            submodules.stdout if submodules.returncode == 0 else submodules.stderr,
            encoding="utf-8",
        )

        submodule_worktrees = git(
            repo_root,
            [
                "submodule",
                "foreach",
                "--recursive",
                "--quiet",
                'printf "submodule=%s\\n" "$displaypath"; git rev-parse HEAD; git status --porcelain=v1 -uall',
            ],
            timeout,
        )
        (temp_dir / "submodule-worktrees.status").write_text(
            submodule_worktrees.stdout if submodule_worktrees.returncode == 0 else submodule_worktrees.stderr,
            encoding="utf-8",
        )

        raw_untracked = git_bytes(
            repo_root,
            ["ls-files", "--others", "--exclude-standard", "-z", *pathspec],
            timeout,
        )
        untracked_names = [os.fsdecode(item) for item in raw_untracked.split(b"\0") if item]
        copied: list[dict[str, str]] = []
        snapshot_root = temp_dir / "untracked-sources"
        for raw_name in untracked_names:
            relative = pathlib.PurePosixPath(raw_name)
            if relative.is_absolute() or ".." in relative.parts or not relevant_untracked(relative):
                continue
            source = repo_root.joinpath(*relative.parts)
            if not source.exists() and not source.is_symlink():
                raise RuntimeError(f"untracked source changed while being captured: {raw_name}")
            destination = snapshot_root.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination, follow_symlinks=False)
            digest, kind = sha256_path(destination)
            copied.append({"path": raw_name, "sha256": digest, "kind": kind})

        hash_lines = [
            f"{item['sha256']}  {item['path']} [{item['kind']}]" for item in copied
        ]
        (temp_dir / "untracked-sources.sha256").write_text(
            "\n".join(hash_lines) + ("\n" if hash_lines else ""), encoding="utf-8"
        )
        sidecar_names = (
            "working-tree.status",
            "tracked.patch",
            "submodules.status",
            "submodule-worktrees.status",
            "untracked-sources.sha256",
        )
        sidecar_sha256 = {
            name: sha256_path(temp_dir / name)[0] for name in sidecar_names
        }
        metadata: dict[str, object] = {
            "format_version": 2,
            "captured_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(repo_root),
            "tree": str(tree),
            "tree_pathspec": tree_path,
            "head": head,
            "tracked_patch": "tracked.patch",
            "status": "working-tree.status",
            "submodule_state": "submodules.status",
            "submodule_worktrees": "submodule-worktrees.status",
            "sidecar_sha256": sidecar_sha256,
            "untracked_source_count": len(copied),
            "untracked_sources": copied,
            "claim_limit": (
                "Tracked changes and source-like untracked files are preserved; ignored and "
                "non-source untracked files are listed by status but not copied."
            ),
        }
        (temp_dir / "manifest.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temp_dir.rename(final_dir)
        return metadata
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Index source and Git history evidence in a local kernel tree."
    )
    parser.add_argument("--tree", required=True, type=pathlib.Path, help="Git worktree to inspect")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--revision",
        help="Committed source snapshot for literal searches (default: HEAD)",
    )
    source_group.add_argument(
        "--working-tree",
        action="store_true",
        help="Search tracked files plus source-like untracked non-ignored files and preserve their evidence",
    )
    parser.add_argument(
        "--term",
        action="append",
        default=[],
        help="Non-empty literal source/history term; repeat as needed",
    )
    parser.add_argument(
        "--author",
        action="append",
        default=[],
        help="Non-empty Git author name/email pattern; repeat as needed",
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        default=[],
        help="Restrict searches with a non-escaping Git pathspec; repeat as needed",
    )
    parser.add_argument("--max-matches", type=int, default=80)
    parser.add_argument("--max-commits", type=int, default=50)
    parser.add_argument("--timeout", type=int, default=120, help="Seconds per Git command")
    parser.add_argument("--output", type=pathlib.Path, help="Write Markdown here instead of stdout")
    parser.add_argument(
        "--evidence-dir",
        type=pathlib.Path,
        help="Working-tree sidecars (default: OUTPUT.evidence); valid only with --working-tree",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing --output file")
    args = parser.parse_args()

    tree = args.tree.expanduser().resolve()
    if not tree.is_dir():
        parser.error(f"tree does not exist or is not a directory: {tree}")
    if not args.term and not args.author:
        parser.error("provide at least one --term or --author")
    for label, values in (("term", args.term), ("author", args.author)):
        for value in values:
            if not value.strip():
                parser.error(f"--{label} must not be empty or whitespace")
    for path in args.paths:
        candidate = pathlib.PurePosixPath(path)
        if not path.strip() or candidate.is_absolute() or ".." in candidate.parts:
            parser.error(f"--path must be a non-empty repository-relative path: {path!r}")
    if args.max_matches < 1 or args.max_commits < 1 or args.timeout < 1:
        parser.error("limits and timeout must be positive")

    output = args.output.expanduser().resolve() if args.output else None
    if output and (output.exists() or output.is_symlink()) and not args.force:
        parser.error(f"output exists; use --force to replace it: {output}")
    if output and output.exists() and output.is_dir():
        parser.error(f"output is a directory, not a report file: {output}")
    if args.evidence_dir and not args.working_tree:
        parser.error("--evidence-dir is valid only with --working-tree")
    if args.working_tree and output is None:
        parser.error("--working-tree requires --output so its evidence can be preserved")

    inside = git(tree, ["rev-parse", "--is-inside-work-tree"], args.timeout)
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        parser.error(f"not a Git worktree: {tree}")
    repo_root = pathlib.Path(
        require_git(git(tree, ["rev-parse", "--show-toplevel"], args.timeout), parser, "Git toplevel lookup")
    ).resolve()
    head = require_git(git(tree, ["rev-parse", "HEAD"], args.timeout), parser, "HEAD lookup")
    branch = git(tree, ["branch", "--show-current"], args.timeout).stdout.strip() or "(detached)"
    shallow = git(tree, ["rev-parse", "--is-shallow-repository"], args.timeout).stdout.strip()
    remotes = lines(git(tree, ["remote", "-v"], args.timeout).stdout)
    status = lines(git(tree, ["status", "--porcelain=v1", "-uall"], args.timeout).stdout)
    pathspec = ["--", *args.paths] if args.paths else []

    evidence_dir: pathlib.Path | None = None
    evidence_metadata: dict[str, object] | None = None
    if args.working_tree:
        assert output is not None
        evidence_dir = (
            args.evidence_dir.expanduser().resolve()
            if args.evidence_dir
            else pathlib.Path(f"{output}.evidence")
        )
        if is_within(evidence_dir, repo_root):
            parser.error(
                "working-tree evidence must be outside the inspected Git worktree "
                "so generated sidecars cannot contaminate capture or search results"
            )
        if is_within(output, evidence_dir) or is_within(evidence_dir, output):
            parser.error("--output and --evidence-dir must not contain one another")
        try:
            evidence_metadata = capture_working_tree(
                tree, repo_root, evidence_dir, args.timeout, head
            )
        except (OSError, RuntimeError, ValueError) as exc:
            parser.error(str(exc))
        source_mode = "working tree (tracked plus source-like untracked non-ignored files)"
        source_selector = "checked-out working tree"
        describe = git(tree, ["describe", "--always", "--dirty", "--tags"], args.timeout).stdout.strip()
        source_revision: str | None = None
    else:
        requested_revision = args.revision or "HEAD"
        source_commit = require_git(
            git(tree, ["rev-parse", "--verify", f"{requested_revision}^{{commit}}"], args.timeout),
            parser,
            f"revision {requested_revision!r}",
        )
        source_mode = "committed tree object"
        source_selector = source_commit
        describe = git(tree, ["describe", "--always", "--tags", source_commit], args.timeout).stdout.strip()
        source_revision = source_commit

    out: list[str] = [
        "# Kernel evidence index",
        "",
        "> Automated matches are leads, not proof. Inspect bindings, source context, ancestry,",
        "> target-device evidence, and patch review history before drawing conclusions.",
        "",
        "## Repository and search identity",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Tree | {md(str(tree))} |",
        f"| HEAD at collection | {md(head)} |",
        f"| Branch | {md(branch)} |",
        f"| Describe | {md(describe)} |",
        f"| Source-search mode | {md(source_mode)} |",
        f"| Source-search selector | {md(source_selector)} |",
        "| History-search scope | All refs (`git log --all`) |",
        f"| Shallow | {md(shallow)} |",
        f"| Repository dirty paths at collection | {len(status)} |",
        f"| Generated UTC | {dt.datetime.now(dt.timezone.utc).isoformat()} |",
        f"| Path restrictions | {md(', '.join(args.paths) if args.paths else '(none)')} |",
        "",
        "### Remotes",
        "",
    ]
    out.extend([f"- {md(sanitize_remote(remote))}" for remote in remotes] or ["- (none)"])
    if shallow == "true":
        out += ["", "**Warning:** history is shallow, so negative history results are incomplete."]
    if not args.working_tree and status:
        out += [
            "",
            "**Working-tree boundary:** dirty files were not searched. Literal source results use the committed selector above.",
        ]
    if evidence_dir and evidence_metadata is not None:
        out += [
            "",
            "### Working-tree evidence",
            "",
            f"- Evidence directory: `{md(str(evidence_dir))}`",
            f"- Relevant untracked sources copied: {evidence_metadata['untracked_source_count']}",
            "- Tracked patch, full `status -uall`, submodule state, copied-source hashes, and a JSON manifest are preserved.",
        ]

    for term in args.term:
        out += ["", f"## Literal term: {md(term)}", ""]
        source_args = ["grep", "-n", "--full-name", "-I", "-F"]
        if args.working_tree:
            tracked_source = git(tree, [*source_args, "-e", term, *pathspec], args.timeout)
            with_untracked = git(
                tree,
                [*source_args, "--untracked", "-e", term, *pathspec],
                args.timeout,
            )
            assert evidence_metadata is not None
            untracked_prefixes = tuple(
                f"{item['path']}:" for item in evidence_metadata["untracked_sources"]
            )
            combined_lines = lines(tracked_source.stdout)
            if untracked_prefixes:
                combined_lines.extend(
                    line
                    for line in lines(with_untracked.stdout)
                    if line.startswith(untracked_prefixes)
                )
            source_lines_all = list(dict.fromkeys(combined_lines))
            source_results = (tracked_source, with_untracked)
        else:
            assert source_revision is not None
            source = git(
                tree,
                [*source_args, "-e", term, source_revision, *pathspec],
                args.timeout,
            )
            source_lines_all = lines(source.stdout)
            source_results = (source,)
        source_lines, source_omitted = limited(source_lines_all, args.max_matches)
        out += [f"### Source matches — {md(source_mode)}", ""]
        for note in dict.fromkeys(command_note(result) for result in source_results):
            if note:
                out.append(f"- Warning: {note}")
        if source_lines:
            out += ["| Location and matching line |", "|---|"]
            out += [f"| {md(line)} |" for line in source_lines]
            if source_omitted:
                out.append(f"| … {source_omitted} additional matches omitted |")
        else:
            out.append("- No matches in the selected source snapshot/path restriction.")

        log_format = "%H%x1f%aI%x1f%an <%ae>%x1f%s"
        messages = git(
            tree,
            [
                "log",
                "--all",
                "--regexp-ignore-case",
                "--fixed-strings",
                f"--grep={term}",
                f"--max-count={args.max_commits}",
                f"--format={log_format}",
                *pathspec,
            ],
            args.timeout,
        )
        out += ["", "### Commit-message matches — all refs", ""]
        note = command_note(messages)
        if note:
            out.append(f"- Warning: {note}")
        message_rows = table_rows(lines(messages.stdout), 4)
        if message_rows:
            out += ["| Commit | Date | Author | Subject |", "|---|---|---|---|"]
            out += [
                f"| {md(commit)} | {md(date)} | {md(author)} | {md(subject)} |"
                for commit, date, author, subject in message_rows
            ]
        else:
            out.append("- No commit-message matches in all refs/path restriction.")

        pickaxe = git(
            tree,
            [
                "log",
                "--all",
                f"-S{term}",
                "--pickaxe-all",
                f"--max-count={args.max_commits}",
                f"--format={log_format}",
                *pathspec,
            ],
            args.timeout,
        )
        out += ["", "### Pickaxe (-S) history — all refs", ""]
        note = command_note(pickaxe)
        if note:
            out.append(f"- Warning: {note}")
        pickaxe_rows = table_rows(lines(pickaxe.stdout), 4)
        if pickaxe_rows:
            out += ["| Commit | Date | Author | Subject |", "|---|---|---|---|"]
            out += [
                f"| {md(commit)} | {md(date)} | {md(author)} | {md(subject)} |"
                for commit, date, author, subject in pickaxe_rows
            ]
        else:
            out.append("- No -S history matches in all refs/path restriction.")

    for author_pattern in args.author:
        history = git(
            tree,
            [
                "log",
                "--all",
                f"--author={author_pattern}",
                f"--max-count={args.max_commits}",
                "--format=%H%x1f%aI%x1f%an <%ae>%x1f%s",
                *pathspec,
            ],
            args.timeout,
        )
        out += ["", f"## Author pattern: {md(author_pattern)} — all refs", ""]
        note = command_note(history)
        if note:
            out.append(f"- Warning: {note}")
        rows = table_rows(lines(history.stdout), 4)
        if rows:
            out += ["| Commit | Date | Author | Subject |", "|---|---|---|---|"]
            out += [
                f"| {md(commit)} | {md(date)} | {md(author)} | {md(subject)} |"
                for commit, date, author, subject in rows
            ]
        else:
            out.append(
                "- No author matches. Check alternate emails, co-authorship, lore, squashes, "
                "and whether the repository contains complete history."
            )

    out += [
        "",
        "## Manual follow-up",
        "",
        "- Inspect each candidate with git show and its parent.",
        "- Check equivalent/rebased patches with range-diff or stable patch-id.",
        "- Read bindings, driver probe paths, lore review and current upstream state.",
        "- Correlate every board claim with exact target-device evidence.",
        "",
    ]
    rendered = "\n".join(out)

    if output:
        write_atomic(output, rendered)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
