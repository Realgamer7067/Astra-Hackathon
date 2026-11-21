# TASK-003: Hypothetical collision runner and physical fragments

- **Owner:** Realgamer7067
- **Dependencies:** TASK-001
- **PR:** none
- **Target demo behavior:** Satellite–satellite and satellite–debris forced events run end to end; assumptions and original/modified states retained; seeded conservation-tested debris and paginated replay; bounded/cancellable jobs.

## Scope and allowed files

- Planned allocation: Lane B — user + main agent, explicitly requested by the user. Formal merged claim remains pending. Reserved for the user; another teammate must coordinate before claiming.
- Primary files / modules: scenario models/routes/store/jobs, physics/collision and fragmentation, orbit/numerical, features/scenarios.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-003 section.

## Acceptance criteria

- [ ] Satellite–satellite and satellite–debris forced events run end to end.
- [ ] assumptions and original/modified states retained.
- [ ] seeded conservation-tested debris and paginated replay.
- [ ] bounded/cancellable jobs.
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
