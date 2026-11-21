# Git and patch archaeology

The goal is to reconstruct lineage, intent, prerequisites and current disposition—not to collect cherry-pick hashes.

## Establish repository identity

For every tree record remote URL, object hash, branch/ref, merge base with upstream, shallow/partial state, dirty state and whether history is authentic or imported from a source drop. Do not compare branch names alone.

Use [scripts/index-kernel-evidence.py](../scripts/index-kernel-evidence.py) for a reproducible first-pass index, then inspect results manually. Literal source searches default to the committed `HEAD` tree; commit-message, author and pickaxe searches explicitly use all refs.

~~~bash
scripts/index-kernel-evidence.py \
  --tree <kernel-tree> --revision HEAD \
  --term <non-empty-literal> --output <new-report.md>
~~~

Use `--working-tree` only when uncommitted work is intentionally evidence. It requires an output file and writes a new sidecar directory containing `status -uall`, the tracked binary diff, submodule state, hashes and copies of source-like untracked files. Put that evidence directory outside the inspected worktree so the helper cannot index its own output. Existing reports are refused unless `--force`; evidence directories are never silently replaced. Working-tree source search covers all tracked files plus the copied source-like untracked set, rather than making unpreserved untracked text look reproducible.

## Search vocabulary

Build aliases from:

- retail/codename/model/board/product/platform;
- SoC marketing and internal IDs;
- PMIC and component parts;
- compatibles, Kconfig symbols, driver filenames and function names;
- error strings from logs;
- DTS labels, GPIO/pinctrl group names, clock/reset IDs;
- subsystem and maintainer names;
- author names and all known email identities.

Search paths, commit messages and patch bodies. Name-only author searches miss co-authored, forwarded, reviewed, renamed-email and squashed work.

## Core commands

~~~bash
git log --all --date=iso-strict --decorate --oneline -- <path>
git log --all --author='<name-or-email>' --format=fuller
git log --all -S'<literal>' --pickaxe-all -- <subtree>
git log --all -G'<regex>' --pickaxe-all -- <subtree>
git blame -w -M -C <file>
git show --find-renames --find-copies --stat <commit>
git show <commit>^! -- <paths>
git log --graph --boundary --left-right <upstream>...<branch>
git range-diff <old-base>..<old-tip> <new-base>..<new-tip>
git merge-base <upstream> <branch>
git patch-id --stable
~~~

Also inspect raw mailing-list messages and series metadata. A GitHub/GitLab commit may be a rebased copy of a lore patch with different hash.

## Reconstruct the series

1. Identify the patch’s actual parent and base, not the repository default branch.
2. Find cover letter, all revisions, prerequisite series and follow-ups.
3. Read review threads for requested redesign, testing gaps and NAK/rejection reasons.
4. Determine whether pieces merged through different subsystem trees.
5. Compare current upstream semantics, compatible strings, headers and driver APIs.
6. Search for equivalent behavior under renamed files/symbols.
7. Use stable patch-id/diff inspection for rebased or squashed equivalents.
8. Check reverts and later fixes.

## Dependency extraction

For each changed node/symbol, trace:

- binding addition and dt-binding headers;
- driver match data and Kconfig;
- clock/reset/regulator/pinctrl/interconnect/IOMMU/power-domain providers;
- firmware/reserved-memory/remoteproc dependencies;
- board DTS and defconfig;
- userspace expectations;
- commits referenced by Fixes, Depends-on, Link or lore thread.

A clean cherry-pick can still be semantically inapplicable. A conflicting cherry-pick can already be present in redesigned form.

## Classification

| Class | Meaning |
|---|---|
| Already upstream | Equivalent change is in target ancestry; cite resulting commit/path |
| Represented differently | Required behavior exists under changed API/topology |
| Applicable but incomplete | Core idea fits but named prerequisites or validation are missing |
| Depends on unported vendor infrastructure | Relies on Android/vendor frameworks not present upstream |
| Downstream hack unsuitable upstream | Hardcoded/bypass behavior violates current subsystem design |
| Documentation-only lead | Reveals hardware/sequence/name but code should not be carried |
| Superseded/rejected | Later series or maintainer decision replaces it; explain why |
| Wrong variant/baseline | Evidence is for materially different hardware or source |
| Unknown | Base, dependency, lineage or target evidence is insufficient |

## Applicability report

| Commit/series | Author/message ID | Base and date | Intent | Prerequisites | Current upstream equivalent | Variant evidence | Review disposition | Classification | Minimal validation |
|---|---|---|---|---|---|---|---|---|---|

Never call a patch newest from its timestamp alone. Compare series version, ancestry, review state and resulting upstream code. Never apply a mailbox or commit from an untrusted source without inspecting its complete diff and metadata.
