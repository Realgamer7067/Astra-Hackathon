# Group review / merge policy

Your **main and implementation agent are the same**. Your second, separate cloud agent is the on-demand **Group Review Agent**.

## What the reviewer is allowed to do

- Review all PRs when explicitly asked; comment, request changes, and give rejection reasons.
- Reproduce and fix bugs, perform testing, repair integration conflicts, create fix branches and PRs.
- Merge PRs that are **actually ready under configured GitHub rules** (not just verbally "approved").
- Report the state of each PR and any new architectural risks.

## Safeguards

- Use a different working tree; inspect untrusted branch code in a sandbox, without production secrets.
- Preserve author ownership. If the PR branch cannot be edited safely, open an integration/fix PR rather than rewriting history.
- Prioritize blockers, majors, then minor polish; do not spend hours rewriting stylistic details.
- Required checks and a non-author approval must pass. If the reviewer has the same GitHub identity as a PR author, it **cannot** count as an independent approval.
- Never run `gh pr merge --admin`, force-push `main`, dismiss a required review, or disable branch protection.
- Use final-head-SHA matched merges (`scripts/merge_checked.py`). If it rejects, report the reason instead of bypassing.
- A rejected PR normally stays open with actionable "changes requested" feedback; closing someone else's PR is a deliberate human decision.

## Output format for group reviews

| PR | Owner | Severity | Actual checks | Action | Next step |
|---|---|---|---|---|---|
| #123 | name | Major | test failed | Changes requested | Owner fixes API |

Also report: integrated demo health, changed contracts, potential regressions, remaining time and risks. The agent is **not** on an automatic PR-open trigger.

