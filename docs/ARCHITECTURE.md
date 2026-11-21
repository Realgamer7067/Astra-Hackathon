# ASTRA architecture baseline

## Planning decision

Use the supplied default: React/TypeScript/Vite/Cesium web client; Python 3.11+ FastAPI/Pydantic/NumPy/SciPy/sgp4/Astropy server; SQLite and local cache. No accounts, paid globe token or AI service in the MVP. Versions and install commands become verified facts only in TASK-001.

Alternative: client-only propagation reduces deployment complexity but contradicts the requested authoritative Python physics boundary. Distributed workers/cloud database add coordination cost without helping the local demo. Keep one bounded local worker and persistent cache.

## Ownership boundaries

- Coordinator: manifests, locks, API registration, global routing/design tokens, configuration, generated contracts and CI.
- Lane A (proposed Teammate 2): catalog connector/repository/orbit service, catalog routes, catalog search and inspector.
- Lane B (user + main agent): scenario routes/storage/jobs, collision/fragmentation/numerical propagation, scenario form.
- Lane C: globe primitives/camera/effects, app shell and timeline.
- Lane D: screening/exposure, results/report routes and results UI.
- Each lane owns tests beside its feature. Request coordinator integration for shared files; never edit another lane silently.

## Scientific boundary

Catalog propagation starts in TEME. Adopt GCRS for common geocentric inertial collision states, with explicit epoch and full position/velocity transformations. Astropy transforms to ITRS for rendering; Cesium receives meters only at the boundary. JPL ICRF vectors require deliberate frame/time conversion, never a relabel. J2 treatment relative to Earth's axis and time-varying frame must be documented and tested before enabling.

## Failure behavior

Startup loads local data without waiting for ingestion. LIVE/CACHED/DEMO is explicit. Provider failures retain last good cache; absent cache uses visibly synthetic data. Jobs have finite resources, cancellation and readable error states. Scrubbing reads saved samples and never reruns physics.

## Commands

The foundation uses Python 3.12 and Node.js 24 in CI with `uv.lock` and `package-lock.json`. Follow the root README for startup and checks. Vite serves bundled Natural Earth imagery and proxies the local FastAPI service. TASK-001 registers the demo/health endpoints, with live catalog, simulation jobs and analysis services reserved for their owning lanes.


## 2. BUILD STACK

Recommended default unless repo constraints dictate otherwise:
- Monorepo: `apps/web` (React + TypeScript + Vite + CesiumJS), `services/api` (Python 3.11+ + FastAPI + Pydantic v2 + NumPy + SciPy + sgp4 + Astropy), `packages/contracts` (generated OpenAPI types or checked-in TypeScript interfaces), `data/fixtures`, `docs`, `tests`.
- Styling: Tailwind CSS or carefully structured CSS variables; lightweight UI component set; Lucide icons. No generic admin dashboard look.
- Orbital catalogs: backend CelesTrak OMM-compatible **CSV**, parsed with full numeric NORAD catalog IDs and joined to SATCAT metadata; SGP4 from `sgp4` Python package; Astropy for validated TEME→ITRS and other Earth frame transformations.
- Real small bodies: NASA/JPL Horizons backend adapter (optional `astroquery.jplhorizons` where it simplifies robust vector handling), plus SBDB for metadata. Cache ephemerides and raw request provenance.
- Numerical debris integrator: NumPy/SciPy vectorized simulation with two-body gravity + J2; optional clearly labeled approximate drag after physics verification. Use km, km/s, kg, seconds internally; convert to Cesium meters and fixed frame at the boundary.
- Data: SQLite + local file cache for MVP. No account system required. Background ingestion should not block startup.
- Progress updates: SSE or WebSocket if genuinely useful; HTTP polling acceptable for MVP.
- Quality: pytest + Vitest; Playwright browser smoke tests if feasible; lint + typecheck + build. Use a lockfile and pinned compatible versions; check APIs against currently installed versions.
- Cesium: avoid adding one Entity per catalog object at full scale. Use point/buffer primitives, LOD, visibility filters, instance collections, and track selection details separately. An option to use Cesium's experimental BufferPointCollection is acceptable if stable in the installed Cesium version; otherwise use supported point collections. Use Cesium's rendering loop and avoid competing WebGL contexts.

Do not add a cloud paid dependency just to show a globe. Prefer a public/legal imagery source with attribution and proper rate limiting, locally hosted legally permitted imagery, or a high-quality Cesium ellipsoid fallback. Default must work **without a Cesium ion token**; optional richer imagery/terrain can be enabled by documented env configuration. Do not scrape restricted map tiles or imply use rights you have not verified. No API keys embedded in the frontend.


## 3. ARCHITECTURE AND BOUNDARIES

Data flow:
1. `CelesTrakConnector` and `JPLConnector` fetch with conditional requests where supported, compression, backoff, caching, and provenance.
2. `CatalogRepository` stores original records, normalized OMM, SATCAT type/status, element epoch, quality/staleness, and snapshot hash. Never misclassify unknown payload status as operational.
3. `OrbitService` propagates cataloged objects using SGP4 and outputs positions and velocities in explicitly named frames.
4. `ScenarioService` validates a scenario, converts participants' states to a common inertial frame, and records all manual state changes.
5. `CollisionEngine` calculates relative state, impact geometry/energy and breakup outcomes.
6. `FragmentEngine` samples physically motivated fragment masses/sizes/velocity impulses under conservation/budget constraints, with an explicit unresolved mass bucket and visible-versus-physical counts separated.
7. `PropagationEngine` numerically propagates fragments and detects atmospheric entry-threshold crossings.
8. `ScreeningEngine` screens short-horizon fragment–catalog-object approaches, refines candidate TCAs and computes **distances**, not unwarranted probabilities.
9. `ExposureService` summarizes shell/altitude/inclination occupancy increases, affected cataloged objects, ground tracks, and conditional entry crossings.
10. `API` provides catalog snapshots, objects, simulation controls, frames, event timeline, and report. `Web` provides globe, timeline, scenario lab, warnings, evidence, and polished visual storytelling.

Architecture must be modular; backend scientific computation is authoritative. Decorative particles and collision flashes may use client-side animation but **must not alter scientific states**. The frontend should never silently synthesize 'live data'.


## 13. REPOSITORY ORGANIZATION

Suggested modules; adapt to actual repo:

```text
apps/web/src/
  app/                 # routes, providers, global state
  components/          # HUD, search, inspector, scenario panel, charts
  globe/               # Cesium integration, primitives, cameras, effects, layers
  timeline/            # clock controls, event markers, frame interpolation
  features/scenarios/  # scenario builder, saved runs, report
  services/            # typed API client, caching
  styles/              # design tokens, responsive rules
services/api/app/
  main.py
  routes/{catalog,objects,asteroids,scenarios,results}.py
  models/{objects,scenarios,results,provenance}.py
  connectors/{celestrak,jpl}.py
  orbit/{sgp4_service,frames,numerical}.py
  physics/{collision,fragmentation,screening,exposure}.py
  storage/{catalog_cache,scenario_store}.py
  jobs/{scheduler,worker}.py
services/api/tests/
apps/web/src/**/*.test.ts
apps/web/e2e/
data/fixtures/
docs/{ARCHITECTURE,PHYSICS,DATA_SOURCES,DEMO_SCRIPT,LIMITATIONS}.md
.env.example
README.md
```

No giant single-file React view and no single 1,000-line Python physics endpoint. Keep simulation deterministic, typed and unit-tested. Add `.gitignore` for secrets, runtime caches, node_modules, Python caches, generated data and large ephemeris files; commit small legally distributable fixtures only.
