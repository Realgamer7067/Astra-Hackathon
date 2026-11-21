# TASK-002: Catalog explorer and correct orbital states

- **Owner:** mayukh-oss
- **Dependencies:** TASK-001
- **PR:** none
- **Target demo behavior:** Search/select real or explicitly demo objects; six-digit IDs preserved; validated SGP4 and frame conversion; source age/coverage and provider failure modes visible.

## Scope and allowed files

- Suggested lane: Lane A; not an ownership assignment.
- Primary files / modules: connectors/celestrak, storage/catalog_cache, orbit/sgp4_service and frames, catalog/object routes, features/catalog.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-002 section.

## Acceptance criteria

- [ ] Search/select real or explicitly demo objects.
- [ ] six-digit IDs preserved.
- [ ] validated SGP4 and frame conversion.
- [ ] source age/coverage and provider failure modes visible.
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
