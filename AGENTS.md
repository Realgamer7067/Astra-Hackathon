# Canonical Project Instructions

This file is the **single source of truth** for all coding agents in this repository. Agent-specific files only point here and to the appropriate role prompt.

## Mission

Build an original, complete, reliable, visually polished hackathon project within 24 hours. The application stack is **undecided until kickoff**; do not assume one.

## Read before changing anything

1. `README.md`, `docs/WORKFLOW.md`, `docs/PROJECT_BRIEF.md`.
2. `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md`, `docs/DECISIONS.md`.
3. `docs/QUALITY.md`, the relevant `tasks/<state>/TASK-*.md` card.
4. Your explicit role prompt: `prompts/MAIN_AGENT.md`, `prompts/TEAMMATE_AGENT.md`, or `prompts/REVIEW_AGENT.md`.

If a document is still a template, say so. **Never hallucinate decisions as finalized.**

## Ownership and task lifecycle

- Four humans; **the coordinator and main implementation agent are the same agent**.
- A separate, user-invoked **review agent** reviews all open PRs and handles integration.
- Feature-based ownership: each developer claims an independent vertical slice.
- Track work using **Markdown cards in `tasks/`**, not GitHub Issues. An unclaimed ready task can be claimed with `python scripts/tasks.py claim TASK-001 --owner <name>` on a dedicated branch and merged before implementation.
- Treat `tasks/` as shared state. Pull the latest `main` before claiming; do not silently steal a task. If two people claim the same task, the first merged claim wins.
- Do not edit another task owner's files, contracts, database schema, or shared infrastructure without coordination.

## Coding contract

- Make the **smallest end-to-end change** satisfying acceptance criteria.
- Preserve existing interfaces; propose contract changes in `docs/CONTRACTS.md` for review first.
- Keep functions clear, names descriptive, dependencies justified, and code maintainable.
- Include suitable tests, error handling, loading/empty states, accessibility, mobile responsiveness, and security considerations.
- Never commit secrets, tokens, `.env`, credentials, local agent data, or large build artifacts.
- Never claim tests or reviews passed unless actually run and inspected.
- If a task is blocked or uncertainty affects the architecture, stop and report it rather than inventing behavior.

## Git & review

- Branch from latest `main`; use `feat/TASK-123-short-name`, `fix/TASK-123-short-name`, or `chore/short-name`.
- Work in separate Git branches/worktrees; never let concurrent agents edit the same checkout.
- Open a PR using `.github/pull_request_template.md`; describe tests and visual proof where relevant.
- Never push directly to protected `main`, force-push shared branches, bypass checks, or approve your own PR.
- On-demand reviewer inspects **all open PRs** when requested, can fix issues in safe branches, and may merge only after checks, required approvals, and GitHub rules permit it.
- Review comments are not a substitute for enforced branch protection.

## Verification

1. Run `python scripts/repo_health.py`.
2. When a stack is selected, run `python scripts/run_project_checks.py` (configured lint, typecheck, tests, security, build, etc.).
3. Run app manually; check critical happy-path, failure-path, desktop/mobile UI, and demo flow.
4. Report **exact commands run**, results, changed files, unresolved risks, and PR URL.

## Priority order under time pressure

Working demo > broken extra features. Protect stability and integration time. Freeze features as described in `docs/DEMO.md`.

