# TASK-004: Cinematic globe and deterministic timeline

- **Owner:** snehkhanpara1108
- **Dependencies:** TASK-001; real integration needs TASK-002 and TASK-003
- **PR:** #8
- **Target demo behavior:** Token-free globe renders batched catalog markers; real saved frames replay/pause/scrub; VFX independent of physics; desktop/mobile/keyboard and reduced motion verified; actual FPS recorded.

## Scope and allowed files

- Suggested lane: Lane C; not an ownership assignment.
- Primary files / modules: globe, timeline, app-shell feature modules.
- Shared interfaces: docs/CONTRACTS.md; request coordinator changes to schemas/registration/locks/global tokens.
- Exclusions: unrelated feature lanes, paid provisioning, unsupported science claims; optional cascades and surface-impact models.
- Implementation steps and interfaces: docs/PLAN.md, TASK-004 section.

## Acceptance criteria

- [x] Token-free globe renders batched catalog markers.
- [x] real saved frames replay/pause/scrub.
- [x] VFX independent of physics.
- [x] desktop/mobile/keyboard and reduced motion verified.
- [x] actual FPS recorded.
- [x] Error/loading/empty states and relevant resource limits verified.
- [ ] Tests actually run and evidence included in feature PR; separate review required.

## Validation and visual proof

- Automated: `python scripts/repo_health.py` (PASSED); `npm run typecheck` (0 errors); `npm run lint` (0 warnings, 0 errors across 18 files); `npm test` (29/29 Vitest tests passed across 4 test files, including completed-run multi-page `/frames` replay integration test and first-frame impact test); `npm run build` (clean production build).
- Manual: Verified in live browser at 1366x768 desktop and 390x844 mobile viewports, including high-DPI resolution scaling (~1.56x backing canvas), live FPS counter (`FPS idle` when stationary, 15-18 FPS in active replay), keyboard navigation (`Tab`, `Space`, `Enter`), completed-run paginated `/frames` playback (play, scrub, reset, first-frame impact auto-focus), and separate `SYNTHETIC_DEMO` preview mode.

## Blockers / integration notes

- Dependencies must merge before final integration; synthetic schema-valid fixtures may support isolated development after TASK-001.
- Promote planned cards only when dependencies/interfaces are ready; done only after verified merge.
