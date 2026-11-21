# ASTRA four-person implementation plan

> Execution baseline dated 2026-11-21. The coordinator owns TASK-001 under the merged claim. Feature ownership is recorded when each claim merges.

## Success and approach

Deliver a token-free Earth with source-labeled catalog markers, object selection, a forced hypothetical satellite–satellite/debris collision, deterministic fragment replay and inspectable exposure. Preserve data provenance and offline operation before optional breadth. Use the recommended React/Cesium + FastAPI scientific monorepo; see ARCHITECTURE.md and CONTRACTS.md for decisions and limits.

Approaches considered: purely sequential delivery minimizes interfaces but underuses four developers; four disconnected demos integrate badly. Recommended: one shared foundation, then four feature lanes built against validated fixtures, integrated in small PRs. First complete slice uses synthetic inputs and real numerical physics; live ingestion is then swapped in through the same catalog interface.

## Four-person work division

| Person | Feature lane | Primary cards | Owns | Handoff |
|---|---|---|---|---|
| You + main agent | B: collision runner and coordination | 001, 003 | shared foundation; scenario form, jobs/store, collision/fragmentation/numerical | validated scenario/job and paginated trajectories |
| Teammate 2 | A: catalog explorer | 002 | connectors, catalog/orbit, search/inspector | source-labeled states and selectable object IDs |
| Teammate 3 | C: globe and replay | 004 | globe, app shell, timeline, camera/effects | token-free scene and deterministic replay of server samples |
| Teammate 4 | D: exposure and reporting | 005 | screening/exposure, results/report routes and UI | bounded encounters, shell charts, projections and report |

The separate reviewer is invoked by the user and is not a fifth parallel implementer. It reviews all PRs, including coordinator PRs. The main agent implements lane B, explicitly requested by the user, while retaining foundation and coordination. Catalog lane A is proposed for Teammate 2. Names and merged claims remain pending; the collision card is reserved for the user in this plan.

## Shared-file ownership and integration

Coordinator owns root manifests, dependency locks, project-checks.json, CI, env examples, API route registration, app routing, global styles and packages/contracts. Feature owners supply modules exported through agreed entry points and request registration in coordinator integration PRs. No simultaneous edits of shared files. Each developer uses a separate branch/worktree from updated main. Claims merge before implementation; first merged claim wins.

## Dependency graph and time budget

| Time since kickoff | Work | Exit gate |
|---|---|---|
| 0–1h | TASK-001 foundation and claim/schema review | token-free globe baseline, /health, real checks, typed fixtures, local startup |
| 1–4h | TASK-002/003/004/005 begin against fixtures | catalog selection, first collision math, scene timeline, synthetic result panel |
| 4–8h | integrate narrow cached/demo vertical slice | select → run real physics → replay → results works end to end |
| 8–13h | live catalog ingestion; propagation/conservation; screening refinement | validated science and explicit source failure modes |
| 13–17h | cinema, responsiveness, genuine exposure/report integration | polished full core flow with bounded resource use |
| 17–20h | TASK-006 reliability/performance; optional TASK-007 only if core green | captured actual measurements and no core blockers |
| 20–24h | freeze, review/repair, rehearsal and submission | documented tests, offline backup, second-machine demo |

These are parallel wall-clock windows. The source prompt's serial milestone hours must not be multiplied across four people. Every 60–90 minutes report current commit, contract changes, blockers and demo health.

TASK-001 unlocks schema-based work in 002–005. TASK-005 can build/test algorithms using fixtures before 003 is merged, but final acceptance needs real 002/003 outputs. TASK-004 can build playback using a truthful synthetic frame fixture before real simulation results arrive. TASK-006 depends on 002–005; TASK-007 is stretch and never blocks 006.

## Task implementation sequence and interfaces

### TASK-001 — runnable shared foundation

Create apps/web (Vite React TS Cesium), services/api/app/main.py (FastAPI factory and /health), services/api/app/models (Pydantic wire types), packages/contracts (matching generated OpenAPI types), data/fixtures and root scripts/config/lockfiles. Start with 12–100 explicitly synthetic objects and one deterministic scenario/frame fixture; fixtures validate through server schemas and client contract checks. Provide startup without provider network access or ion token.

1. Define /health, provenance, object/state/frame/scenario/job/result schemas from CONTRACTS.md and fixture validation tests.
2. Install/pin compatible versions after checking current official APIs. Configure all seven real project checks before adding app source.
3. Add minimal API and token-free globe shell; limit shared app entry point edits to coordinator. Export feature mounting points for catalog, scenario, timeline and results.
4. Run checks, startup both processes and inspect initial browser scene. Document exact commands; capture first screenshot.
5. Merge separately reviewed foundation before promoting 002–005.

### TASK-002 — source-backed catalog explorer

Create connectors/celestrak.py, storage/catalog_cache.py, orbit/sgp4_service.py, orbit/frames.py, routes/catalog.py and objects.py, web features/catalog and tests. Define fetch_snapshot() returning immutable normalized snapshot/provenance; propagate_objects(ids, epoch_utc) returning declared GCRS/ITRS batches per contracts.

1. Failing tests for six-digit IDs, malformed/empty CSV, unknown operational status, staleness and cached/demo fallback; use mocked provider transport.
2. Add persistent last-good cache, supported documented feeds, deduplication and policy-compliant refresh without retry hammering.
3. Validate propagation against trusted reference states, frame conversion and km↔m boundary; record explicit tolerances.
4. Add search/filter/selection and source/freshness inspector. Connect object IDs to scenario picker and states to globe.
5. Run relevant tests and real provider integration only when network available; never make CI depend on provider availability.

### TASK-003 — deterministic collision runner

Create models/scenarios.py, routes/scenarios.py, storage/scenario_store.py, jobs/scheduler.py and worker.py, physics/collision.py and fragmentation.py, orbit/numerical.py, web features/scenarios. Expose run_scenario(validated_input, snapshot) returning persisted result/frame references, and deterministic FragmentationModel.generate(event, seed, limits).

1. Failing validation tests: missing/duplicate IDs, unknown attributes without acknowledgment, invalid units/numbers, forced-position audit and excessive jobs/horizon/fragments.
2. Implement common-frame impact state, SI energy, mass/residual/momentum/energy budgets, seeded bounded fragments.
3. Test two-body analytical orbit agreement/drift, verified J2 direction/convergence, terminal entry crossing and deterministic samples. Define tolerances and model version in PHYSICS.md.
4. Persist queued/running/terminal jobs with progress/cancel/timeouts and paginated precomputed frames; scrubbing never reintegrates.
5. Add editable assumptions, explicit hypothetical confirmation, run/progress/cancel/error UI; demo satellite–satellite and debris–satellite.

### TASK-004 — cinematic globe and replay

Create globe/{viewer,markers,layers,camera,effects}, timeline/{clock,interpolation,controls} and app layout feature modules. Playback consumes FRAMES-v1 only; Cesium primitives own marker rendering, React owns controls. Clock state: UTC epoch, paused state, speed, bounded run interval and selected event.

1. Add semantic controls and dark navy/teal/amber layout per UX.md; coordinate global tokens through owner.
2. Render source-labeled marker batches, selection and orbit trails without per-object React updates. Handle no WebGL and slow-loading data.
3. Test play/pause/speed/scrub/reset/end behavior, frame boundary interpolation and terminal fragment visibility.
4. Connect actual job frames, impact camera and independent decorative particles. Include exaggerated-size labels, reduced motion and low graphics.
5. Browser-check keyboard, 1366×768 and 390×844. Measure actual marker/FPS performance, retain hardware/browser evidence.

### TASK-005 — exposure and factual report

Create physics/screening.py and exposure.py, routes/results.py, services/report.py, web features/results. screen_encounters(fragment_samples, candidate_states, limits) returns refined modeled distances and metadata; summarize_exposure(samples) returns occupancy bins and computed crossings with provenance.

1. Failing tests comparing bounded broad-phase screening against brute-force fixtures; near misses never become contacts based solely on coarse bins.
2. Add bounded selected-neighbor screening/refinement and 100-km altitude occupancy, with screened-set limits visible.
3. Compute ground projections independently from entry crossing flags; no ground-track input alone yields an entry warning.
4. Build result charts/table/empty/loading/error states and report including seed/model/snapshot/original-modified states/limitations.
5. Connect real simulation output and frame UI; verify hypothetical labels survive export and no unsupported probability/service-outage language appears.

### TASK-006 — verify and freeze

Run repo health and all configured checks on final reviewed commit; inspect browser console and primary/failure/offline flows. Measure runtime/memory/FPS and source ages without inventing targets as results. Fix blockers in owning branches, complete README/startup/attribution, rehearse demo and backup. No new optional features after hour 20.

### TASK-007 — optional real asteroid mode

Only after the core is green and enough buffer remains. Backend official SBDB/Horizons adapter, authentic cached metadata/response tests, UTC/TDB/frame conversions and explicit state injection audit. Display HYPOTHETIC REDIRECTED TRAJECTORY — NOT A PREDICTION in form/globe/report. Disable on unavailable authentic data. No feasible deflection/cost claim. Secondary cascades remain deferred unless separately scoped and reviewed.

## Review focus

- Wrong frames/time scales or km/m conversions: TASK-002 reference conversions and TASK-003 cross-frame rejection tests.
- Fake live data on outage: TASK-002 explicit LIVE/CACHED/DEMO transition tests.
- Broken conservation or unbounded compute: TASK-003 mass/momentum/energy and resource-limit/cancel tests.
- Near miss mislabeled contact or ground projection mislabeled risk: TASK-005 brute-force/refined-distance and no-entry tests.
- Replay changes numerical output or erases fictional labels: TASK-004 clock tests and TASK-005 export/provenance assertions.

## Start and handoff commands

The foundation PR promotes TASK-002–005 on merge. Afterward, pull `main`, pick your allocated lane, and use `python scripts/tasks.py claim TASK-002 --owner YOUR_NAME` with your task number on a dedicated claim branch. Once the claim merges, branch again from current `main` to implement. TASK-004 and TASK-005 can start with fixtures while TASK-002 and TASK-003 build their producers.

## Evidence status

TASK-001's browser evidence is in [evidence/foundation-desktop.png](evidence/foundation-desktop.png). It shows the local demo snapshot. Live ingestion, numerical validation and scale benchmarks remain feature work.
