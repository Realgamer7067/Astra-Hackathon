#!/usr/bin/env python3
"""Inventory Linux kernel changes without repairing or writing the source tree.

Python 3.10+, Git 2.36+, Linux/POSIX. Run against a quiescent read-only source
mount for enforced isolation. Writes only a new external audit directory.
This is a coverage aid, not a semantic reviewer or tamper-proof attestation.
"""
import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

IMMUTABLE = ["id", "phase", "kind", "path", "old_line", "new_line", "change", "text_sha256", "excerpt"]
REVIEW = ["verdict", "evidence_a", "evidence_b", "rationale", "follow_up"]
FIELDS = IMMUTABLE + REVIEW
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$")
MAX_READ = 4 * 1024 * 1024
FORMAT_VERSION = 2
GIT_SETTINGS = {
    "core.quotePath": "true", "color.ui": "false", "core.fsmonitor": "false",
    "core.hooksPath": "/dev/null", "core.attributesFile": "/dev/null",
    "core.excludesFile": "/dev/null", "core.untrackedCache": "false",
    "core.ignoreCase": "false", "core.trustctime": "true", "core.checkStat": "default", "core.ignoreStat": "false",
    "core.fileMode": "true", "core.symlinks": "true", "core.autocrlf": "false",
    "core.pager": "cat", "diff.noprefix": "false", "diff.mnemonicPrefix": "false",
    "diff.relative": "false", "diff.ignoreSubmodules": "none",
    "diff.suppressBlankEmpty": "false", "diff.algorithm": "myers",
    "protocol.allow": "never", "gc.auto": "0", "maintenance.auto": "false",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def git(repo, *args, check=True, data=None):
    # Discard inherited Git redirects/config injection, but preserve the host's
    # executable path. The executable/runtime themselves must be trusted.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_ATTR_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0",
                "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0",
                "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1",
                "LC_ALL": "C"})
    cmd = ["git"]
    for key, value in GIT_SETTINGS.items():
        cmd.extend(["-c", f"{key}={value}"])
    cmd.extend(["-C", str(repo), *args])
    p = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env, timeout=300)
    if check and p.returncode:
        # Git can echo private paths; never include remote URLs/config values.
        raise RuntimeError(f"Git {args[0]} failed ({p.returncode}): " +
                           p.stderr.decode(errors="replace")[:2000])
    return p


def decode_git_path(text):
    if text == "/dev/null":
        return ""
    if text.startswith('"'):
        try:
            raw = ast.literal_eval(text).encode("latin-1", "surrogateescape")
            text = raw.decode("utf-8", "surrogateescape")
        except (ValueError, SyntaxError, UnicodeError) as exc:
            raise ValueError("Cannot safely decode quoted Git path") from exc
    if text.startswith(("a/", "b/")):
        path = text[2:]
        if path and not Path(path).is_absolute() and ".." not in Path(path).parts:
            return path
    raise ValueError(f"Unknown diff path format: {text!r}")


def header_paths(header):
    quoted = re.fullmatch(r'("(?:\\.|[^"\\])*") ("(?:\\.|[^"\\])*")', header)
    if quoted:
        old, new = map(decode_git_path, quoted.groups())
    else:
        # --no-renames means both header paths are identical. This also handles
        # a literal ' b/' within a filename without guessing a separator.
        width = (len(header) - 5) // 2
        old_raw, new_raw = header[:width + 2], header[width + 3:]
        if header[width + 2:width + 3] != " ":
            raise ValueError("Malformed diff header")
        old, new = decode_git_path(old_raw), decode_git_path(new_raw)
    if old != new:
        raise ValueError("Unexpected rename/copy header; inventory requires --no-renames")
    return old, new


def mkrow(phase, kind, path, old_line="", new_line="", change="", payload=""):
    return {"phase": phase, "kind": kind, "path": path, "old_line": str(old_line),
            "new_line": str(new_line), "change": change,
            "text_sha256": sha(payload.encode("utf-8", "surrogateescape")),
            "excerpt": payload[:240].replace("\r", "\\r").replace("\n", "\\n")}


def lf_lines(data):
    # Git and source line numbers count LF, not form-feed, VT, CR or U+2028.
    lines = data.decode("utf-8", "surrogateescape").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def parse_patch(phase, patch):
    result, curr = [], None
    old_no = new_no = old_left = new_left = 0
    last_content = False

    def flush():
        if old_left or new_left:
            raise ValueError("Truncated patch hunk")
        if curr is not None:
            path = curr["new"] or curr["old"]
            if not path:
                raise ValueError("Patch has no attributable path")
            result.append(mkrow(phase, "file-delta", path, change="metadata",
                                payload=" | ".join(curr["meta"])))
            for row in curr["events"]:
                row["path"] = path
                result.append(row)

    for line in lf_lines(patch):
        if line == "\\ No newline at end of file":
            if curr is None or not last_content:
                raise ValueError("Orphan no-newline marker")
            curr["events"].append(mkrow(phase, "file-ending", "", change="no-newline", payload=line))
            last_content = False
            continue
        if old_left or new_left:
            if line.startswith("+") and new_left:
                curr["events"].append(mkrow(phase, "line", "", new_line=new_no, change="+", payload=line[1:]))
                new_no += 1
                new_left -= 1
            elif line.startswith("-") and old_left:
                curr["events"].append(mkrow(phase, "line", "", old_line=old_no, change="-", payload=line[1:]))
                old_no += 1
                old_left -= 1
            elif line.startswith(" ") and old_left and new_left:
                old_no += 1
                new_no += 1
                old_left -= 1
                new_left -= 1
            else:
                raise ValueError("Malformed/truncated patch hunk; refusing partial coverage")
            last_content = True
            continue
        last_content = False
        if line.startswith("diff --git "):
            flush()
            old, new = header_paths(line[11:])
            curr = {"old": old, "new": new, "header_path": old,
                    "meta": [], "events": [], "binary": False}
        elif curr is None:
            if line:
                raise ValueError("Unexpected patch preamble")
        elif line.startswith(("--- ", "+++ ")):
            path = decode_git_path(line[4:].removesuffix("\t"))
            if path and path != curr["header_path"]:
                raise ValueError("Patch path headers disagree")
            curr["old" if line.startswith("--- ") else "new"] = path
        elif line.startswith("@@"):
            match = HUNK.fullmatch(line)
            if match is None or curr["binary"]:
                raise ValueError("Unsupported hunk header")
            old_no, new_no = int(match[1]), int(match[3])
            old_left = int(match[2]) if match[2] is not None else 1
            new_left = int(match[4]) if match[4] is not None else 1
            if not old_left and not new_left:
                raise ValueError("Empty hunk")
        elif line == "GIT binary patch" or line.startswith("Binary files "):
            curr["binary"] = True
            curr["meta"].append(line)
            curr["events"].append(mkrow(phase, "binary", "", change="requires-manual-binary-review", payload=line))
        elif curr["binary"]:
            # Payload is retained verbatim in patches/ and fingerprinted.
            continue
        elif line.startswith(("index ", "new file mode ", "deleted file mode ", "old mode ", "new mode ")):
            curr["meta"].append(line)
        elif line:
            raise ValueError(f"Unexpected patch record: {line[:80]!r}")
    flush()
    return result


def check_numstat(rows, raw, gitlinks=()):
    expected = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        added, deleted, path = record.split(b"\t", 2)
        path = os.fsdecode(path)
        if path in expected:
            old = expected[path]
            if b"-" in old or b"-" in (added, deleted):
                raise ValueError("Ambiguous repeated binary numstat")
            added, deleted = str(int(old[0]) + int(added)).encode(), str(int(old[1]) + int(deleted)).encode()
        expected[path] = (added, deleted)
    actual = {}
    for row in rows:
        if row["kind"] == "file-delta":
            actual.setdefault(row["path"], [0, 0, False])
        elif row["kind"] == "line":
            actual[row["path"]][0 if row["change"] == "+" else 1] += 1
        elif row["kind"] == "binary":
            actual[row["path"]][2] = True
    if set(expected) != set(actual):
        raise ValueError("Patch/numstat path mismatch; refusing incomplete inventory")
    for path, (added, deleted) in expected.items():
        a, d, binary = actual[path]
        if (added, deleted) == (b"-", b"-"):
            if not binary:
                raise ValueError("Binary change not represented")
        elif binary or (a, d) != (int(added), int(deleted)):
            events = [r for r in rows if r["path"] == path and r["kind"] == "line"]
            # Git emits a synthetic -dirty gitlink hunk but numstat says 0/0.
            dirty_link = (path in gitlinks and (added, deleted) == (b"0", b"0") and
                          (a, d) == (1, 1) and all(re.fullmatch(
                              r"Subproject commit [0-9a-f]{40,64}(?:-dirty)?", r["excerpt"]) for r in events))
            if not dirty_link:
                raise ValueError("Patch/numstat line count mismatch")


def file_metadata(path):
    st = path.lstat()
    item = {"mode": oct(stat.S_IMODE(st.st_mode)), "size": st.st_size}
    if stat.S_ISLNK(st.st_mode):
        target = os.readlink(path)
        data = os.fsencode(target)
        header = f"blob {len(data)}\0".encode()
        item.update(type="symlink", sha256=sha(data), target=target,
                    blob_sha1=hashlib.sha1(header + data).hexdigest(), blob_sha256=sha(header + data))
    elif stat.S_ISREG(st.st_mode):
        digest = hashlib.sha256()
        header = f"blob {st.st_size}\0".encode()
        blob1, blob256 = hashlib.sha1(header), hashlib.sha256(header)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as f:
            before = os.fstat(f.fileno())
            if not stat.S_ISREG(before.st_mode) or (st.st_dev, st.st_ino) != (before.st_dev, before.st_ino):
                raise RuntimeError("File changed type while hashing")
            for part in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(part)
                blob1.update(part)
                blob256.update(part)
            after = os.fstat(f.fileno())
        signature = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if signature(st) != signature(after) or signature(st) != signature(path.lstat()):
            raise RuntimeError("File changed while hashing")
        item.update(type="file", sha256=digest.hexdigest(), blob_sha1=blob1.hexdigest(), blob_sha256=blob256.hexdigest())
    else:
        raise RuntimeError(f"Unsupported directory/special file: {path}. Scope nested repositories separately; do not silently exclude them.")
    return item


def raw_paths(repo, *args):
    return [os.fsdecode(p) for p in git(repo, "ls-files", *args).stdout.split(b"\0") if p]


def safe_path(repo, rel):
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise ValueError("Invalid repository path")
    path = repo / p
    # Never traverse a symlinked parent into an external tree.
    for parent in path.parents:
        if parent == repo:
            break
        if parent.is_symlink():
            raise RuntimeError(f"Symlinked parent requires separate scope: {rel!r}")
    return path


def git_dir(repo, option):
    raw = git(repo, "rev-parse", "--path-format=absolute", option).stdout
    return Path(os.fsdecode(raw.removesuffix(b"\n"))).resolve(strict=True)


def preflight(repo):
    # Merely reading a split index can freshen sharedindex mtime/ctime, even
    # with optional locks disabled. Detect artifacts without opening the index.
    for option in ("--absolute-git-dir", "--git-common-dir"):
        if any(git_dir(repo, option).glob("sharedindex.*")):
            raise RuntimeError("Split-index artifacts require a separate nonsplit audit copy; reading them can write Git metadata")
    version = git(repo, "--version").stdout
    match = re.search(rb"git version (\d+)\.(\d+)", version)
    if not match or tuple(map(int, match.groups())) < (2, 36):
        raise RuntimeError("Git 2.36+ required for safe fsmonitor disabling")
    keys = git(repo, "config", "--name-only", "--list", "-z").stdout.split(b"\0")
    # Refuse normalization programs and on-demand network fetching rather than
    # relying on --no-ext-diff (which does not disable clean/process filters).
    for key in keys:
        lower = key.lower()
        if lower.startswith(b"filter.") or lower == b"extensions.partialclone" or lower.endswith(b".promisor"):
            raise RuntimeError("Configured filters/partial clone unsupported; use an authorized isolated complete source copy")
    if git(repo, "rev-parse", "--is-shallow-repository").stdout.strip() != b"false":
        raise RuntimeError("Shallow history cannot establish complete change coverage")
    for option in ("--absolute-git-dir", "--git-common-dir"):
        graft = git_dir(repo, option) / "info/grafts"
        if graft.exists() and graft.stat().st_size:
            raise RuntimeError("Grafted history unsupported")
    flags = raw_paths(repo, "-v", "-z")
    if any(p[0].islower() or p.startswith("S ") for p in flags):
        raise RuntimeError("skip-worktree/assume-unchanged flags prevent reliable coverage; use a complete audit copy without these flags. Do not alter the audited index.")
    index = git(repo, "ls-files", "--stage", "-z").stdout
    entries = {}
    for record in index.split(b"\0"):
        if not record:
            continue
        info, raw_path = record.split(b"\t", 1)
        mode, oid, stage = info.split()
        if stage != b"0":
            raise RuntimeError("Unmerged index: resolve scope outside this review before claiming coverage")
        entries[os.fsdecode(raw_path)] = {"mode": mode.decode(), "oid": oid.decode()}
    attrs = git(repo, "check-attr", "-z", "--stdin", "filter", "text", "eol", "ident", "working-tree-encoding",
                data=b"".join(os.fsencode(p) + b"\0" for p in sorted(entries))).stdout.split(b"\0")
    if attrs[-1:] == [b""]:
        attrs.pop()
    if len(attrs) % 3:
        raise ValueError("Malformed attributes response")
    for i in range(0, len(attrs), 3):
        if attrs[i + 2] not in (b"unspecified", b"unset"):
            raise RuntimeError("Content-transforming Git attributes unsupported: " + os.fsdecode(attrs[i]) +
                               ". Audit raw source in a separate controlled copy; do not change this tree.")
    return entries


def physical_files(repo, submodules):
    """Cross-check Git's enumeration; never follow symlinks or enter gitdirs."""
    found = set()
    pending = [repo]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                rel = str(path.relative_to(repo))
                if rel == ".git" or rel in submodules:
                    continue
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISDIR(mode):
                    pending.append(path)
                elif stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                    found.add(rel)
                else:
                    raise RuntimeError(f"Unsupported special file: {rel!r}; never read devices/FIFOs during inventory")
    return found


def snapshot(repo, seen=None):
    seen = set() if seen is None else seen
    real = repo.resolve(strict=True)
    if real in seen:
        raise RuntimeError("Recursive repository cycle")
    seen = seen | {real}
    entries = preflight(repo)
    result = {"repo": str(repo), "head": git(repo, "rev-parse", "--verify", "HEAD^{commit}").stdout.decode().strip(),
              "git_dir": str(git_dir(repo, "--absolute-git-dir")), "common_dir": str(git_dir(repo, "--git-common-dir")),
              "index_entries": entries, "tracked": {}, "untracked": {}, "ignored": {}, "submodules": {}}
    for rel, entry in sorted(entries.items()):
        path = safe_path(repo, rel)
        if entry["mode"] == "160000":
            if path.is_symlink():
                raise RuntimeError("Submodule root must not be a symlink")
            if not path.exists() or (path.is_dir() and not any(path.iterdir())):
                result["submodules"][rel] = {"initialized": False, "oid": entry["oid"]}
            else:
                top = git(path, "rev-parse", "--show-toplevel").stdout.removesuffix(b"\n")
                if Path(os.fsdecode(top)).resolve() != path.resolve():
                    raise RuntimeError("Nonempty submodule directory is not its own repository")
                result["submodules"][rel] = {"initialized": True, "oid": entry["oid"], "snapshot": snapshot(path, seen)}
        else:
            try:
                result["tracked"][rel] = file_metadata(path)
            except FileNotFoundError:
                result["tracked"][rel] = {"type": "missing"}
    for group, options in (("untracked", ["--others", "--exclude-standard", "-z"]),
                           ("ignored", ["--others", "--ignored", "--exclude-standard", "-z"])):
        for rel in sorted(raw_paths(repo, *options)):
            result[group][rel] = file_metadata(safe_path(repo, rel))
    expected = {p for p, m in result["tracked"].items() if m["type"] != "missing"}
    expected.update(result["untracked"])
    expected.update(result["ignored"])
    if physical_files(repo, result["submodules"]) != expected:
        raise RuntimeError("Physical filesystem and Git file inventory disagree; refusing incomplete scope")
    return result


def collect(repo, base):
    before = snapshot(repo)
    head = before["head"]
    base_sha = git(repo, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}").stdout.decode().strip()
    if git(repo, "merge-base", "--is-ancestor", base_sha, head, check=False).returncode:
        raise RuntimeError("--base must be a verified ancestor of HEAD; do not invent a baseline")
    stages = [("final-tree", [base_sha]), ("staged", ["--cached", head]), ("unstaged", [])]
    commits = git(repo, "rev-list", "--reverse", f"{base_sha}..{head}").stdout.decode().splitlines()
    for commit in commits:
        parents = git(repo, "rev-list", "--parents", "-n", "1", commit).stdout.decode().split()
        if len(parents) < 2:
            raise RuntimeError("Unexpected root commit in interval")
        stages.append((f"commit-{commit}", [parents[1], commit]))
    opts = ["--no-ext-diff", "--no-textconv", "--no-renames", "--unified=0", "--binary",
            "--submodule=short", "--ignore-submodules=none", "--src-prefix=a/", "--dst-prefix=b/",
            "--no-relative", "--no-color", "-O/dev/null"]
    patches, rows = {}, []
    for phase, revs in stages:
        patch = git(repo, "diff", *opts, *revs, "--").stdout
        phase_rows = parse_patch(phase, patch)
        counts = git(repo, "diff", *opts, "--no-patch", "--numstat", "-z", *revs, "--").stdout
        gitlinks = {p for p, e in before["index_entries"].items() if e["mode"] == "160000"}
        check_numstat(phase_rows, counts, gitlinks)
        if phase == "unstaged":
            represented = {r["path"] for r in phase_rows if r["kind"] == "file-delta"}
            for path, meta in before["tracked"].items():
                entry = before["index_entries"][path]
                blob_key = "blob_sha1" if len(entry["oid"]) == 40 else "blob_sha256"
                mode = "120000" if meta["type"] == "symlink" else (
                    "100755" if int(meta.get("mode", "0"), 8) & 0o100 else "100644")
                if (meta.get(blob_key) != entry["oid"] or mode != entry["mode"]) and path not in represented:
                    raise RuntimeError(f"Raw working file differs from index but Git omitted it: {path!r}; use a fresh isolated audit copy")
        patches[phase] = patch
        rows.extend(phase_rows)
    for group in ("untracked", "ignored"):
        for rel, meta in before[group].items():
            rows.append(mkrow(group, "file-delta", rel, change=group, payload=json.dumps(meta, sort_keys=True)))
            if meta["type"] == "file" and meta["size"] <= MAX_READ:
                data = safe_path(repo, rel).read_bytes()
                if sha(data) != meta["sha256"]:
                    raise RuntimeError("SCOPE DRIFT while reading additional source")
                if b"\0" not in data:
                    for i, line in enumerate(lf_lines(data), 1):
                        rows.append(mkrow(group, "line", rel, new_line=i, change="+", payload=line))
                else:
                    rows.append(mkrow(group, "binary", rel, change="requires-manual-binary-review", payload=meta["sha256"]))
            else:
                rows.append(mkrow(group, "unexpanded", rel, change="requires-manual-full-file-review", payload=json.dumps(meta, sort_keys=True)))
    # Keep the ignored aggregate and source-like marker for compatibility, but
    # now account for every ignored file, not only selected filename suffixes.
    rows.append(mkrow("ignored", "ignored-set", "<ignored paths>", change="triage-all", payload=json.dumps(sorted(before["ignored"]))))
    for rel in before["ignored"]:
        rows.append(mkrow("ignored", "ignored-source", rel, change="triage-source", payload=rel))
    rows.append(mkrow("submodules", "submodule-set", "<git submodules>", change="triage-all", payload=json.dumps(sorted(before["submodules"]))))
    for rel, sub in before["submodules"].items():
        rows.append(mkrow("submodules", "submodule", rel, change="requires-separate-scope",
                          payload=sha(canonical_json(sub))))
    after = snapshot(repo)
    if before != after:
        raise RuntimeError("SCOPE DRIFT during inventory; freeze the tree and retry")
    for i, row in enumerate(rows, 1):
        row["id"] = f"L{i:08d}"
    state = {"repo": str(repo), "base": base_sha, "head": head, "snapshot": before,
             "stage_hashes": {phase: sha(patch) for phase, patch in patches.items()},
             "stage_order": [phase for phase, _ in stages]}
    return state, rows, patches


def source_roots(snap):
    roots = {Path(snap[k]) for k in ("repo", "git_dir", "common_dir")}
    for sub in snap["submodules"].values():
        if sub["initialized"]:
            roots.update(source_roots(sub["snapshot"]))
    return roots


def outside(out, roots):
    if any(out == root or root in out.parents for root in roots):
        raise RuntimeError("Output MUST be outside source trees and Git metadata directories")


def ensure_repo_and_out(repo_arg, out_arg, init):
    repo = Path(repo_arg).resolve(strict=True)
    top = Path(os.fsdecode(git(repo, "rev-parse", "--show-toplevel").stdout.removesuffix(b"\n"))).resolve(strict=True)
    requested = Path(out_arg).absolute()
    if requested.is_symlink():
        raise RuntimeError("Audit output must not be a symlink")
    out = requested.resolve()
    outside(out, {top, git_dir(top, "--absolute-git-dir"), git_dir(top, "--git-common-dir")})
    if init and out.exists():
        raise RuntimeError("Output already exists; choose a new directory to avoid overwrites")
    return top, out


def init(args):
    repo, out = ensure_repo_and_out(args.repo, args.out, True)
    state, rows, patches = collect(repo, args.base)
    outside(out, source_roots(state["snapshot"]))
    # No artifacts are written until preflight, parsing and snapshot checks pass.
    out.mkdir(parents=True, exist_ok=False)
    patch_dir = out / "patches"
    patch_dir.mkdir()
    for phase, patch in patches.items():
        (patch_dir / f"{phase}.patch").write_bytes(patch)
    inventory = [{k: row[k] for k in IMMUTABLE} for row in rows]
    (out / "inventory.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    scope = {"format_version": FORMAT_VERSION, "state": state,
             "state_sha256": sha(canonical_json(state)), "items": len(rows),
             "inventory_sha256": sha(canonical_json(inventory))}
    (out / "scope.json").write_text(json.dumps(scope, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    with (out / "ledger.csv").open("w", newline="", encoding="utf-8", errors="surrogateescape") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, **{name: "" for name in REVIEW}})
    print(f"INVENTORY CREATED: {len(rows)} items across {len(patches)} phases at {out}")
    print("No repairs performed. Submodules require separate linked scopes; fingerprints alone are not reviews.")


def verify(args):
    repo, out = ensure_repo_and_out(args.repo, args.out, False)
    scope = json.loads((out / "scope.json").read_text(encoding="utf-8"))
    if scope.get("format_version") != FORMAT_VERSION:
        raise RuntimeError("Unsupported audit format; create a fresh v2 inventory, never relabel a v1 audit")
    original = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
    if sha(canonical_json(original)) != scope["inventory_sha256"] or len(original) != scope["items"]:
        raise RuntimeError("Inventory changed after scope creation")
    state, regenerated, patches = collect(repo, scope["state"]["base"])
    if sha(canonical_json(state)) != scope["state_sha256"] or state != scope["state"]:
        raise RuntimeError("SCOPE DRIFT: source content or Git scope changed; create a fresh review")
    if [{k: row[k] for k in IMMUTABLE} for row in regenerated] != original:
        raise RuntimeError("Regenerated inventory differs")
    for phase, patch in patches.items():
        if (out / "patches" / f"{phase}.patch").read_bytes() != patch:
            raise RuntimeError(f"Stored patch changed: {phase}")
    with (out / "ledger.csv").open(newline="", encoding="utf-8", errors="surrogateescape") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise RuntimeError("Ledger columns changed")
        actual = list(reader)
    expected = {r["id"]: r for r in original}
    seen, incomplete = set(), []
    for row in actual:
        if None in row or any(v is None for v in row.values()):
            raise RuntimeError("Malformed ledger row")
        key = row["id"]
        if key in seen or key not in expected:
            raise RuntimeError(f"Duplicate or unknown ledger ID: {key}")
        seen.add(key)
        if any(row[k] != expected[key][k] for k in IMMUTABLE):
            raise RuntimeError(f"Immutable audit item altered: {key}")
        verdict = row["verdict"].strip().upper()
        if verdict not in {"PASS", "FINDING", "UNKNOWN", "N/A"} or not row["rationale"].strip() or not row["evidence_a"].strip():
            incomplete.append(key)
        if verdict in {"UNKNOWN", "FINDING"} and not row["follow_up"].strip():
            incomplete.append(key)
        if row["evidence_b"].strip() and row["evidence_a"].strip() == row["evidence_b"].strip():
            incomplete.append(key)
    missing = set(expected) - seen
    if missing:
        raise RuntimeError(f"Missing ledger entries: {len(missing)}")
    if incomplete:
        raise RuntimeError(f"Incomplete evidence/dispositions: {len(set(incomplete))}")
    summary = {s: sum(r["verdict"].strip().upper() == s for r in actual) for s in ("PASS", "FINDING", "UNKNOWN", "N/A")}
    print(f"DISPOSITIONS COMPLETE: {len(actual)} inventory items; source snapshot matches.")
    print("Verdicts:", json.dumps(summary, sort_keys=True))
    print("Exit 0 validates bookkeeping only. It does not certify review depth, evidence truth, linked submodule audits, or hardware correctness.")
    if summary["FINDING"] or summary["UNKNOWN"]:
        print("NOT CLEARED: unresolved findings or unknowns remain.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)
    a = s.add_parser("inventory", help="Create scope snapshot and per-line ledger")
    a.add_argument("--repo", required=True)
    a.add_argument("--base", required=True, help="Explicit verified ancestor commit")
    a.add_argument("--out", required=True, help="New directory outside source and Git metadata")
    b = s.add_parser("verify", help="Check dispositions and snapshot drift; not semantic approval")
    b.add_argument("--repo", required=True)
    b.add_argument("--out", required=True)
    args = p.parse_args()
    try:
        if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
            raise RuntimeError("POSIX with O_NOFOLLOW required; use Linux for kernel audits")
        init(args) if args.command == "inventory" else verify(args)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, csv.Error, subprocess.TimeoutExpired) as exc:
        print(f"AUDIT ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
