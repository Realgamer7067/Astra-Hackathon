# Execution boundary and inventory contract

## Contents

1. Codex and OpenCode operation
2. What the helper inventories
3. Unsupported states and manual review
4. Coverage, evidence and exit codes
5. Commands and resumption

## Codex and OpenCode operation

A skill is guidance, not an operating-system permission boundary. The OpenCode adapter in `integrations/opencode/kernel-auditor.md` applies only to OpenCode. Its `edit: deny`/`bash: ask` settings do not configure Codex. Preserve the adapter for OpenCode users; never assume its restrictions transferred to another host.

For Codex, establish source and Git metadata as read-only, with a separate writable audit-output location. Use the host's current permission controls or a read-only source mount in an isolated environment. Start with read-only Codex permissions if uncertain, but recognize that an entirely read-only environment cannot create the ledger: arrange an explicitly writable external output directory rather than broadly enabling source edits. Never launch an unrestricted session just to make the helper run. External builds are optional, separately authorized, and must not expand source write access.

If the user explicitly requests local OpenCode installation, preserve the optional adapter alongside the skill. The original installation layout is:

```bash
mkdir -p ~/.config/opencode/skills ~/.config/opencode/agents
cp -a mainline-kernel-auditor ~/.config/opencode/skills/
cp mainline-kernel-auditor/integrations/opencode/kernel-auditor.md ~/.config/opencode/agents/
```

Only run installation outside an audit and after checking the destination for an existing skill. OpenCode's Bash approval is a command-review boundary, not an OS sandbox. Read the proposed command before approving it; the adapter denies direct edits and subagent launches.

Local Codex discovers user skills under `~/.agents/skills/<name>/SKILL.md`; invoke with `$mainline-kernel-auditor`. ChatGPT-managed skills use the host's Skills interface. Keep the complete skill folder and its references/scripts together. This guide is not an instruction to install automatically. `agents/openai.yaml` supplies UI metadata; it is not a sandbox.

Use a trusted Python/Git installation and PATH. The helper disables system/global Git configuration, inherited GIT_* overrides, fsmonitor, hooks, external diff/textconv, automatic maintenance and network protocols. It rejects repository filters and partial clones before diff operations. Repository-local config/attributes still need inspection, and a patched trusted Git version remains necessary. Read-only mounting is the stronger boundary. The helper does not defend against a compromised interpreter, hostile concurrent filesystem replacement, or kernel vulnerabilities.

## What the helper inventories

- Pinned ancestor baseline and HEAD; final tracked worktree delta; staged and unstaged deltas.
- Every reachable commit in `base..HEAD`, each compared to its first parent, including reverted/history-only work. Merge histories may include many shared upstream commits: make the baseline/scope explicit instead of silently dropping them.
- Text additions/deletions using LF line boundaries, checked against Git numstat; file modes, symlinks, binary changes, deleted files, and no-final-newline markers. Renames are deliberately represented as deletion/addition.
- Every untracked and ignored file, including nonstandard suffixes. Text up to 4 MiB gets line rows; larger files, symlinks and binaries receive explicit manual-review rows and content fingerprints. Never call those rows a completed line review without a separately linked expansion/provenance audit.
- Raw content, type and permission fingerprints of all tracked, untracked and ignored files. Compare raw Git blob hashes to the index to detect changes that Git's stat cache could otherwise hide. Hashes cover unchanged tracked dependencies for drift detection, but do not mean those dependencies were semantically reviewed.
- Recursive content snapshots of initialized submodules, including their dirty, untracked and ignored contents. **Their internal line inventories require separate child audits with verified baselines.** Parent verification checks content drift, not completion of child reviews. Uninitialized modules are explicit unknowns, never automatically fetched.

A pre/post content scan checks for changes during collection. It is not an atomic snapshot and cannot detect every transient edit-and-revert race. Quiesce the implementation agent and use a fixed read-only snapshot. Hashing a full kernel and ignored build outputs may take time and disk space; report the cost and scope rather than silently sample or truncate.

## Unsupported states and manual review

Preflight fails clearly for split-index artifacts (including stale shared-index files, to avoid timestamp writes), skip-worktree/assume-unchanged flags, unmerged index stages, shallow/grafted history, partial clones, configured clean/process filters, and active text/eol/ident/encoding normalization attributes. These cases can hide or transform physical source bytes or trigger execution. Do not clear flags, alter attributes, fetch, reset or repair the audited tree. If already authorized, prepare a separate complete controlled audit copy, account for every original file and difference, and pin its provenance; otherwise document the blocker and continue independent manual analysis. Never claim the helper covered unsupported input.

Untracked nested repositories, unreadable files, special files and symlinked parent directories also stop inventory instead of disappearing from scope. Scope nested repositories separately. Symlink entries are hashed as link targets without dereferencing; if the build consumes external content, inventory that content as a separate dependency scope. The helper does not fingerprint files outside its declared roots, boot partitions, initramfs, external firmware directories or actions taken by an earlier agent outside the tree.

Git replace refs are ignored intentionally. All quoted object IDs and baseline reasoning must refer to the actual object graph. Missing objects fail; do not turn lazy network fetching back on.

## Coverage, evidence and exit codes

`inventory` exit 0 means the declared inventory artifacts were created. It is not a review result. Every line/metadata row starts unreviewed.

`verify` exit 0 means source/artifacts match and all inventory rows contain structurally valid dispositions. It prints `DISPOSITIONS COMPLETE` and separate PASS/FINDING/UNKNOWN/N/A counts. UNKNOWN/FINDING are allowed and explicitly NOT CLEARED; both require follow-up. PASS/N/A require an applicable rationale and locatable evidence or group argument. A second reference is optional unless the substantive claim needs independent corroboration; duplicated strings do not count as corroboration.

Exit 2 means an audit error (unsupported source, drift, corrupted artifacts, missing rows/evidence, or tool failure). Read the error; unfinished dispositions and source drift are different problems. Old format-v1 scopes are rejected: retain them as history and generate fresh v2 scopes. Do not edit their version field to bypass this check.

The verifier cannot establish citation truth, review depth, child-scope completeness, hardware correctness or tamper-proof provenance. A person able to rewrite all audit artifacts can replace their hashes. Do not call the files cryptographically immutable or represent exit 0 as kernel approval.

## Commands and resumption

Resolve `<skill-dir>` from the loaded skill location and use an absolute source path, verified baseline and new output directory:

```bash
python3 <skill-dir>/scripts/review_scope.py inventory --repo <source-tree> --base <verified-ancestor-SHA> --out <new-external-audit-directory>
python3 <skill-dir>/scripts/review_scope.py verify --repo <source-tree> --out <audit-directory>
```

The output must be outside the source, linked-worktree Git directories, common Git directory, and initialized submodule metadata. Existing output directories are refused during inventory to prevent overwrite. Do not put reports in the kernel checkout.

Record scope hashes and preserve full patches; ledger excerpts are previews, not the full source. After every batch, save the evidence register and checkpoint. On resumption, check snapshot consistency before reusing conclusions. When source drifts, create a new scope and revalidate any carried-forward work; retain historical findings without presenting reverted bugs as current defects.
