# TASK-004: Cinematic globe and deterministic timeline

- **Owner:** snehkhanpara1108
- **Dependencies:** TASK-001; real integration needs TASK-002 and TASK-003
- **PR:** none
- **Target demo behavior:** Token-free globe renders batched catalog markers; real saved frames replay/pause/scrub; VFX independent of physics; desktop/mobile/keyboard and reduced motion verified; actual FPS recorded.

## Scope and allowed files

- Suggested lane: Lane C; not an ownership assignment.
- Primary files / modules: globe, timeline, app-shell feature modules.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-004 section.

## Acceptance criteria

- [ ] Token-free globe renders batched catalog markers.
- [ ] real saved frames replay/pause/scrub.
- [ ] VFX independent of physics.
- [ ] desktop/mobile/keyboard and reduced motion verified.
- [ ] actual FPS recorded.
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
