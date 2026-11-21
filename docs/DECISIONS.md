# Decision log

## TEMPLATE-001: Collaboration defaults (approved for starter)

- One main agent performs **both** coordination and implementation.
- One **separate cloud review agent**, invoked on demand, reviews all PRs and may integrate/merge when protected branch rules permit.
- Four humans own vertical features, not fixed frontend/backend roles.
- Tasks are Markdown cards stored under `tasks/` rather than GitHub Issues.
- All developers may use different coding agents with canonical `AGENTS.md`.
- The template has no application framework, no bundled skill packs, and no committed credentials.
- The project prioritizes code quality, visual polish, testing, and demo reliability.

## Decisions to make at kickoff

Record each material choice in this format:

### ADR-NNN: Title

- **Status:** Proposed / Approved / Superseded
- **Context:** What problem or constraint required a choice?
- **Options considered:**
- **Decision and owner:**
- **Consequences / tradeoffs:**
- **Date:**

Do not rewrite prior decisions without noting why they changed.


## ASTRA-001: Supplied concept and planning authorization

- Status: Accepted for planning on 2026-11-21.
- Context: User supplied ASTRA specification and requested work division, plan and start.
- Decision: Preserve concept, scientific honesty and core demo; use supplied recommended stack as baseline. Do not claim official rubric or package validation.
- Tradeoff: Freeze narrow core before optional asteroids/cascades.

## ASTRA-002: Four feature lanes and shared integration gate

- Status: Planned execution baseline, individual claims pending.
- Decision: Catalog explorer; collision runner; globe/replay; exposure/report. Coordinator owns foundation/shared files. Separate user-invoked review remains mandatory.
- Consequence: TASK-001 must establish schemas, fixtures and runnable checks before parallel application work. Names are not assigned without coordination.

## ASTRA-003: Numerical and operational limits

- Status: Baseline requiring executable verification in TASK-001/003.
- Decision: GCRS inertial and ITRS render states; 24-hour maximum; default 600 resolved fragments; no secondary fragmentation in core. See CONTRACTS.md for bounded jobs/pages.
- Consequence: J2 frame assumptions and scientific tolerances need evidence. Any resource increase requires measured justification.

## ASTRA-004: User takes collision engine

- Status: User-requested allocation, 2026-11-21; formal claim merge pending.
- Decision: User + main agent take lane B / TASK-003: scenario setup, collision physics, fragmentation, numerical propagation and jobs, retaining TASK-001 foundation and coordination. Catalog lane A / TASK-002 is proposed for Teammate 2. Lanes C and D remain unchanged.
- Consequence: Supersedes the initial person-to-lane mapping; interfaces and dependencies remain unchanged. Reserve the collision card for the user.
