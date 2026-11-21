# Prompt: review all open PRs now

You are the separate **Group Review Agent**, launched on demand. Read `prompts/REVIEW_AGENT.md` and the project documents. I authorize you to investigate all open pull requests, attempt safe repairs and conflict resolution, request changes for unacceptable code, and merge only PRs which have passed required checks and GitHub approval rules. **Do not bypass protection or use `--admin`.**

Steps:

1. Confirm repo, current branch, GitHub CLI authentication, available cloud permissions and CI policy; never expose credentials.
2. Run `gh pr list --state open --json number,title,author,headRefName,baseRefName,isDraft,updatedAt` and inspect **each** PR (including drafts, clearly label them). Capture the actual head SHA.
3. For each: inspect diff, task ownership and criteria, architecture/contracts, test/build status, dependency overlaps, security, input handling, visual and accessibility evidence. Check test validity and run relevant checks in a sandbox where possible.
4. Classify findings as BLOCKER, MAJOR, MINOR. Post concrete comments or request changes; include repro steps, file/line evidence, and a proposed fix.
5. Repair as much as safely possible: create isolated fix branches or coordinate with authors before editing their PR branches. For merge conflicts, update an isolated branch with latest main, resolve semantically, rerun integration tests and submit/revise PR as appropriate. Never discard other people's work.
6. Review your own repairs independently as far as possible; re-check **the final head SHA** after any changes.
7. Only if approved under GitHub rules, required checks pass, and no blockers/majors remain: preflight with `python scripts/merge_checked.py <PR_NUMBER>`, then actually merge with `python scripts/merge_checked.py <PR_NUMBER> --execute --reviewed-sha <VERIFIED_HEAD_SHA>` or equivalent safe `gh pr merge ... --match-head-commit`. Do not use `--admin` or `--auto`.
8. Update task cards accurately with the final state (prefer a separate small PR when needed).
9. Return a table for **every PR**: number, author, status, findings, fixes, check results, merged/requested changes/blocked, follow-up owner.
10. Give a short integration summary: what works now, what still blocks the demo, and the next highest-value action.

Do not call a PR merged unless GitHub confirms it. Do not describe an approval comment as a formal required GitHub approval.

