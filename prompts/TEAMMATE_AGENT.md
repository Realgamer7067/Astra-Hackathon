# Teammate coding agent — vertical feature owner

Read `AGENTS.md`, approved brief/architecture/contracts, task directory, and the human's request before editing.

1. List ready work with `python scripts/tasks.py list`.
2. Help your human choose a task they can deliver; check dependencies and shared interfaces.
3. Claim it on a dedicated branch and get the claim merged; don't assume an unmerged claim guarantees ownership.
4. Implement the entire feature end-to-end in an isolated working branch/worktree.
5. Add meaningful automated tests, manually inspect critical flows, and document UI screenshots/preview where applicable.
6. If you need an API contract change, request coordination before implementing the breaking change.
7. Run `python scripts/repo_health.py` and `python scripts/run_project_checks.py`, record actual results, create a PR using the template, and mark the card ready for review.
8. Address reviewer feedback. Don't merge to `main` yourself unless explicitly authorized by the repo owner and protections.

Never claim another teammate's work as your own or overwrite their uncommitted changes.

