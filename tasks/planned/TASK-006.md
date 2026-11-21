# TASK-006: Integrated reliability performance and demo freeze

- **Owner:** unclaimed
- **Dependencies:** TASK-002, TASK-003, TASK-004, TASK-005
- **PR:** none
- **Target demo behavior:** All required checks run on final commit; offline/happy/failure and mobile/desktop demo verified; actual measurements and limitations documented; backup rehearsed and no core blockers.

## Scope and allowed files

- Suggested lane: Coordinator with all lanes; separate reviewer invoked by user; not an ownership assignment.
- Primary files / modules: Integration fixes coordinated with feature owners; README, docs/DEMO, evidence artifacts.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-006 section.

## Acceptance criteria

- [ ] All required checks run on final commit.
- [ ] offline/happy/failure and mobile/desktop demo verified.
- [ ] actual measurements and limitations documented.
- [ ] backup rehearsed and no core blockers.
- [ ] Error/loading/empty states and relevant resource limits verified.
- [ ] Tests actually run and evidence included in feature PR; separate review required.

## Validation and visual proof

- Automated: python scripts/repo_health.py; python scripts/run_project_checks.py after TASK-001 configures real stack checks.
- Add/run the task-specific tests identified in docs/PLAN.md before claiming acceptance.
- Manual: execute owning task's documented demo behavior and failure path; capture desktop/mobile screenshots for UI.
- No acceptance, test or benchmark has passed yet.

## Blockers / integration notes

- Dependencies must merge before final integration; synthetic schema-valid fixtures may support isolated development after TASK-001.
- Promote planned cards only when dependencies/interfaces are ready; done only after verified merge.
