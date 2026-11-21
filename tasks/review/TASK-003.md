# TASK-003: Hypothetical collision runner and physical fragments

- **Owner:** Realgamer7067
- **Dependencies:** TASK-001
- **PR:** `feat/TASK-003-demo-integration`
- **Target demo behavior:** Satellite–satellite and satellite–debris forced events run end to end; assumptions and original/modified states retained; seeded conservation-tested debris and paginated replay; bounded/cancellable jobs.

## Scope and allowed files

- Lane B is owned by Realgamer7067. The claim merged in PR #4.
- Primary files / modules: scenario models/routes/store/jobs, physics/collision and fragmentation, orbit/numerical, features/scenarios.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-003 section.

## Acceptance criteria

- [x] Satellite–satellite and satellite–debris forced events run end to end.
- [x] assumptions and original/modified states retained.
- [x] seeded conservation-tested debris and paginated replay.
- [x] bounded/cancellable jobs.
- [x] Error/loading/empty states and relevant resource limits verified.
- [ ] Tests actually run and evidence included in feature PR; separate review required.

## Validation and visual proof

- Automated checks passed. `python scripts/repo_health.py`, `python scripts/run_project_checks.py`, `python -m pytest -q services/api/tests` (65 passed), and `python -m unittest discover -s tests` (12 passed). The configured frontend suite passed 43 tests.
- Desktop Chrome verified a satellite–debris run with 96 representatives and 121 replay samples across two pages. The matching report retained seed 73.
- Mobile Chrome at 390 pixels verified a satellite–satellite run, playback, scrubbing and a report retaining seed 74. Blocking the Blue Marble tiles loaded the Natural Earth fallback.

## Blockers / integration notes

- Dependencies must merge before final integration; synthetic schema-valid fixtures may support isolated development after TASK-001.
- Promote planned cards only when dependencies/interfaces are ready; done only after verified merge.
