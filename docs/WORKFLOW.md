# Four-person workflow (feature ownership)

## Roles

| Participant | Responsibility |
|---|---|
| You + **main agent** | **One agent does both coordination and implementation.** Proposes the plan, obtains your approval, writes project specifications and task cards, builds its own features, creates PRs. |
| Teammates 2–4 + chosen agents | Pick ready feature cards, claim ownership, build vertical slices, test and open PRs. No prescribed technology or fixed frontend/backend roles. |
| Your **separate review agent** | Runs **only when requested**. Reviews every open PR, tests integration, requests changes, fixes issues/conflicts safely, may merge passing PRs where GitHub rules allow it. |

The reviewer is not a magically persistent service. To review, launch its cloud agent with repo access and `prompts/REVIEW_ALL_PRS.md`.

## Kickoff: approve before execution

1. Share the official problem statement and judging criteria with the main agent.
2. Main agent proposes: problem understanding, viable MVP, judge-facing differentiator, stack, architecture, data/privacy plan, API contracts, demo workflow, 24-hour schedule, risk list.
3. **Human approves or modifies the proposal.** Do not generate tasks or application code before this decision.
4. Main agent fills `docs/PROJECT_BRIEF.md`, `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md`, `docs/DECISIONS.md` and sets up `project-checks.json` for the chosen stack.
5. Main agent creates multiple **independent feature cards** from `tasks/_TEMPLATE.md`, putting approved/unblocked cards in `tasks/ready/` and dependencies in `tasks/planned/`.
6. Communicate the ready board to the team. Once ownership is established, all four build in parallel.

## Markdown task board

Each Markdown file is a task card. The **directory is the status**:

- `tasks/planned/` – dependency or decision outstanding
- `tasks/ready/` – anyone may claim
- `tasks/active/` – a named owner is working
- `tasks/review/` – PR open and ready for reviewer
- `tasks/blocked/` – blocked, with an explanation
- `tasks/done/` – merged and verified

Run `python scripts/tasks.py list` to view the board. To claim: `python scripts/tasks.py claim TASK-001 --owner your-name`; this moves the relevant card from `ready` to `active`. Commit the change in a **small claim PR** (or let the coordinator batch ownership changes in one PR) before significant coding. Pull the latest `main` and check the task remains available. **First merged claim wins.** If a claim conflicts, coordinate instead of overwriting.

Other status changes: `python scripts/tasks.py move TASK-001 --to review` or `--to blocked --reason 'waiting for endpoint'`, and finally `--to done` **only after merge**. Keep status changes small and based on known facts.

## Coding a feature

1. Read `AGENTS.md`, task scope, architecture and contracts.
2. Create branch `feat/TASK-001-short-name` from current `main` (or a dedicated worktree if you run multiple agents).
3. Implement the complete vertical slice; expose stable mocks/interfaces early if another task depends on it.
4. Run all configured checks, manually test key flows, attach screenshots or video for UI changes.
5. Open a PR, complete the PR checklist, and move your task card to `review` in that PR or a small coordinated status PR.
6. Respond to review feedback. A task is not done merely because an agent says it is.

**Shared files:** Only one owner coordinates changes to schemas, lockfiles, global design tokens, env examples, routing, and contracts. Propose cross-cutting changes before writing them.

## Review / integration on demand

When you ask the review agent, it performs the full sweep in `prompts/REVIEW_ALL_PRS.md`:

- Inventory all open PRs and identify dependency/order, changed interfaces, tests, and potential overlapping files.
- Analyze security, correctness, readability, performance, UX/accessibility, tests, and rubric fit.
- Request changes when quality is insufficient; do **not** treat partial tests as success.
- Fix safe issues and conflicts on isolated branches. Never overwrite an author's branch without permission; where necessary, propose a separate integration PR.
- Re-run CI checks on the **final commit**. Merge only when repo rules and required reviews permit it.
- Report merged PRs, rejected/blocked PRs, outstanding risks, and task board status.

## Daily communication during a 24h event

- Start-of-task: owner, scope, contract, target PR time.
- Every ~60–90 minutes: quick status, blockers, interface changes, demo health.
- At freeze: **no new features**; fix critical bugs and polish the demo.
- Maintain a working deployment and a local backup walkthrough.

## What the agents must not assume

- A ZIP can create online GitHub settings or grant cloud access: **it cannot**.
- Two agents using the **same GitHub account** are distinct coding sessions, **not distinct GitHub reviewers**. GitHub does not allow authors to approve their own PRs.
- A PR comment marked "approved" in prose is not equivalent to a formal required approval or a required status check.
- GitHub's rule enforcement, not a prompt, is the ultimate merge gate.

