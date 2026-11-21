# Script Contracts

Read when running or integrating the helpers. They are local, read-only decision aids, not remote verifiers. Require Python 3.10+; JSON needs only the standard library. YAML for idea input needs optional PyYAML. IANA timezone lookup may need system timezone data or `tzdata`; explicit UTC offsets avoid that dependency.

Use absolute script paths or run from the installed skill directory. Pass the project path/file explicitly: the current directory is not automatically the hackathon repository. Run `--help` first. Exit `0` means the requested local operation completed; `1` means a reported negative condition; `2` means invalid input. No helper deploys, submits, edits project files, or guarantees judging readiness.

## Idea ranking

```bash
python scripts/score-ideas.py /path/to/ideas.json --json
```

Default active keys: `rubric_fit`, `demo_impact`, `feasibility`, `originality`, `visual_potential`, `story_strength`, `technical_depth`, `sponsor_fit`, `usefulness`, `time_to_mvp`, `differentiation`, `failure_risk`, `complexity_cost`, `dependency_risk`. Scores are 0-10; high benefits are good, high risk/cost is bad, high `time_to_mvp` means fast. Weights are listed in [idea-tournament.md](idea-tournament.md).

Active scores are required by default (`--strict` is a compatibility alias). Explicit `--allow-missing` gives missing benefits 0 and missing costs/risks 10, with provisional warnings. Unassessed risk must never improve ranking. Use real JSON booleans for `fatal_pass`; absent gates are assumed and warned, not verified. Exit 1 means no candidate passed supplied gates. Totals are heuristics, not win probabilities; normalized scores can be negative.

Embedded `weights` and `--weights file.json` override named defaults. Use `--replace-weights` for an exact event rubric without accidentally retaining unrelated defaults. Example complete custom input:

```json
{
  "weights": {"innovation": 40, "implementation": 30, "impact": 20, "presentation": 10},
  "ideas": [
    {"name": "Candidate A", "fatal_pass": true,
     "scores": {"innovation": 8, "implementation": 7, "impact": 7, "presentation": 6}},
    {"name": "Candidate B", "fatal_pass": true,
     "scores": {"innovation": 5, "implementation": 9, "impact": 7, "presentation": 9}}
  ]
}
```

```bash
python scripts/score-ideas.py /path/to/ideas.json --replace-weights --json
```

Verify feasibility/eligibility separately; do not infer implementation quality from technical complexity.

## Rubric audit

```bash
python scripts/rubric-audit.py /path/to/RUBRIC.md --fail-below 80 --json
```

Use the seven template columns, unique criterion names, weights in percentage points (`40%` or `40`, not `0.4` for 40%), and strength `0`-`5` or `4/5`. Escape a literal pipe as `\|`; multiline cells and arbitrary Markdown tables are not supported. Unknown weights stay unknown. The aggregate is null unless every weight is known and the total is 100 within 0.1 percentage point. A threshold with unknown/incomplete weights exits 1. Do not silently renormalize a partial rubric. Missing proof caps reported strength, but supplied proof text is not independently verified.

## Deadline audit

```bash
python scripts/deadline-audit.py 2026-09-12T18:00:00+05:30
python scripts/deadline-audit.py --from-file /path/to/HACKATHON.md --json
```

Input must contain a time. Naive timestamps require `--timezone`; ambiguous/nonexistent DST wall times are rejected—resolve an explicit offset from the official cutoff. `--now` makes tests deterministic. At or after the cutoff, exit 1. A file must have one unambiguous `Deadline: ...` value. For multiple deliverable deadlines, select the earliest currently binding one explicitly; the script does not infer event rules or grace periods.

## Submission audit

```bash
python scripts/submission-audit.py /path/to/project --require README.md --require demo.mp4 --json
```

The tracker defaults to `SUBMISSION.md`; `--submission CUSTOM.md` replaces that filename. Only the tracker plus `--require` files are hard local requirements; other internal documents are advisory (`--minimal` hides advisories). Required assets must be nonempty regular files inside the project root. List actual screenshot files, not a directory. Presence does not validate video/image contents.

Use `Status: submitted` or `Current status: submitted` only after actual confirmation. `draft`, `saved`, conflicting statuses, blank status, unchecked tasks, placeholders, and incomplete table statuses remain blockers. Template rows require a ready/complete status and a `YES` judge-view check. For genuinely inapplicable rows use status `N/A — official reason`; verify the exemption manually. Unknown late-edit permission is a warning, never permission to edit. Blocker count deduplicates line findings. `--no-fail` suppresses blocker exit 1, not input errors; never use it as proof of completeness.

## Repository snapshot

```bash
python scripts/project-status.py /path/to/project --json
```

Finds nested manifests, state-document presence, deployment configs, and TODO locations. Ignores common vendor/build/credential directories, symlinks, and non-regular files. TODO content scanning uses a text/source allowlist and skips `.env` files; output contains markers/locations, not source lines. This is not a secret scanner. Git output omits commit subjects and disables optional locks; a parent repository is identified but not scanned as the project. Paths and branch names may themselves contain sensitive information: inspect before sharing. Large repositories still require targeted inspection; this snapshot is not an exhaustive application audit.
