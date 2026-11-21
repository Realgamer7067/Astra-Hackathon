# TASK-001: Token-free runnable foundation

- **Owner:** unclaimed
- **Dependencies:** none
- **PR:** none
- **Target demo behavior:** Local API and token-free globe start offline; shared fixtures validate against executable contracts; all seven configured check categories run; baseline screenshot and exact startup commands recorded.

## Scope and allowed files

- Suggested lane: Coordinator (suggested; claim pending); not an ownership assignment.
- Primary files / modules: Root manifests/locks/checks, apps/web baseline, services/api baseline, packages/contracts, data/fixtures.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-001 section.

## Acceptance criteria

- [ ] Local API and token-free globe start offline.
- [ ] shared fixtures validate against executable contracts.
- [ ] all seven configured check categories run.
- [ ] baseline screenshot and exact startup commands recorded.
- [ ] Error/loading/empty states and relevant resource limits verified.
- [ ] Tests actually run and evidence included in feature PR; separate review required.

## Validation and visual proof

- Automated: python scripts/repo_health.py; python scripts/run_project_checks.py after TASK-001 configures real stack checks.
- Add/run the task-specific tests identified in docs/PLAN.md before claiming acceptance.
- Manual: execute owning task's documented demo behavior and failure path; capture desktop/mobile screenshots for UI.
- No acceptance, test or benchmark has passed yet.

## Blockers / integration notes

- Claim must merge before significant implementation; establish contracts/checks first.
- Promote planned cards only when dependencies/interfaces are ready; done only after verified merge.
