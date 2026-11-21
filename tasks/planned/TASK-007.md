# TASK-007: Optional authentic JPL asteroid fictional interception

- **Owner:** unclaimed
- **Dependencies:** TASK-006 core gates green; sufficient pre-freeze buffer
- **PR:** none
- **Target demo behavior:** Real identified JPL object/ephemeris with source and time/frame conversion tests; prominent fictional state injection labels everywhere; unavailable authentic data disables mode; no fabricated asteroid data.

## Scope and allowed files

- Suggested lane: Available owner by explicit claim; not an ownership assignment.
- Primary files / modules: connectors/jpl, asteroid routes/models, asteroid feature modules and authentic fixtures.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-007 section.

## Acceptance criteria

- [ ] Real identified JPL object/ephemeris with source and time/frame conversion tests.
- [ ] prominent fictional state injection labels everywhere.
- [ ] unavailable authentic data disables mode.
- [ ] no fabricated asteroid data.
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
