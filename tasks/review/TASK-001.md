# TASK-001: Token-free runnable foundation

- **Owner:** Realgamer7067
- **Dependencies:** none
- **PR:** none
- **Target demo behavior:** Local API and token-free globe start offline; shared fixtures validate against executable contracts; all seven configured check categories run; baseline screenshot and exact startup commands recorded.

## Scope and allowed files

- Lane: Coordinator.
- Primary files / modules: Root manifests/locks/checks, apps/web baseline, services/api baseline, packages/contracts, data/fixtures.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-001 section.

## Acceptance criteria

- [x] Local API and token-free globe start with locally served data and imagery.
- [x] Shared fixtures validate against executable contracts.
- [x] All seven configured check categories run.
- [x] Baseline screenshot and exact startup commands recorded.
- [x] API failure and retry verified in Chrome. Frame page limits are enforced by the shared schema.
- [ ] Tests actually run and evidence included in feature PR; separate review required.

## Validation and visual proof

- Automated: python scripts/repo_health.py; python scripts/run_project_checks.py after TASK-001 configures real stack checks.
- Add/run the task-specific tests identified in docs/PLAN.md before claiming acceptance.
- Manual: execute owning task's documented demo behavior and failure path; capture desktop/mobile screenshots for UI.
- Evidence: [startup commands](../../README.md#run-the-foundation-locally) and [desktop screenshot](../../docs/evidence/foundation-desktop.png).

## Blockers / integration notes

- The claim merged in PR #2. The foundation PR promotes TASK-002–005 on merge. Move TASK-001 to done only after verified merge.
