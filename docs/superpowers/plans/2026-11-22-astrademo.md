# Sharper Earth imagery and numerical collision demo

**Goal.** Submit a hypothetical collision in ASTRA, replay the computed debris on a sharper globe, and export the same run's report offline.

## 1. Integrate the collision runner

- [x] Bring the existing TASK-003 engine and completion handoff onto current `main`. Keep catalog, results and replay routes registered beside the bounded scenario worker. Regenerate OpenAPI and TypeScript contracts from the combined FastAPI app.
- [x] Mount the existing `ScenarioLab` from `App.tsx`. The completion event carries the scenario ID, seed and epoch. Reuse the replay session's active ID for `ResultsPanel`.
- [x] Verify a satellite–satellite and a satellite–debris run, participant assumptions, audit states, cancellation, frame paging, and unknown-ID errors. The first slice uses the fixed offline catalog. Source-backed participants need a later input adapter that pins an epoch and catalog snapshot.

## 2. Add sharper offline Earth imagery

- [x] Prepare 512-pixel geographic tiles from NASA Earth Observatory's July 2004 Blue Marble composite. Use levels 0–3 with 8,192 × 4,096 effective coverage at the highest level. Keep the raw source outside Git.
- [x] Load local tiles with Cesium's geographic tiling scheme. Display source attribution and use the bundled Natural Earth imagery if Blue Marble fails to load.
- [x] Verify the higher levels load as the camera zooms, the globe and marker alignment survive the imagery change, and the browser requests imagery only from the local app.

## 3. Show the integrated build

- [x] Run repository checks, Python tests, frontend tests, and production build. In desktop and mobile Chrome, submit a scenario, play and scrub its computed frames, and export its report.
- [ ] Open a feature PR with test evidence and preserve separate review. Keep the merged demo checkout available while testing the feature branch.
