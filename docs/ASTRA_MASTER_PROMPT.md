# ASTRA 2026 — OpenAI Codex Master Implementation Prompt

## ROLE AND MISSION

You are OpenAI Codex acting as an autonomous senior full-stack engineer, orbital-dynamics developer, scientific-computing engineer, visualization specialist, QA engineer, and technical lead. **Build and verify a running application. Do not stop at a plan, architecture diagram, mockup, scaffolding, or static UI.** Inspect the repository before writing code. If empty, create the project from scratch. Make reasonable engineering decisions without asking clarification questions, unless credentials or external actions absolutely require user participation. Prioritize a compelling, stable, demo-ready 24-hour hackathon MVP over speculative breadth; make the architecture extensible.

Project working title: **ASTRA Orbital Collision Lab** (make branding configurable).
Event: VIT Bhopal ASTRA 2026; domain: **Sustainable Space & Space Environment**.

### Real problem

Increasing numbers of operational satellites, retired spacecraft, rocket bodies, and debris occupy Earth orbit. Public orbital data exists, but understanding how an impact could create fragments and increase hazards to nearby spacecraft is hard for students, researchers, communicators, and the general public. Build an interactive platform connecting authentic public orbital observations to **clearly hypothetical** collisions, physical fragment evolution, orbital exposure analysis, and educational ground-facing consequences. It is **not** an operational collision-warning or civil-protection system.

### Success experience

A visitor opens a beautiful, realistic, manipulable 3D Earth with actual cataloged spacecraft orbiting at the present time. They can search/select two catalog objects or a real known asteroid, inspect an orbit, choose a scenario, trigger a visually spectacular collision, then pause, rewind, accelerate time, inspect propagating debris and secondary encounters, and see exactly which orbital shells and spacecraft have increased modeled exposure. Earth overlays clarify ground tracks and **conditional** re-entry information without implying a hazard where none has been calculated. The experience should be understandable by a non-expert and credible to a technical judge.

## 1. NON-NEGOTIABLE USER DECISIONS

- Scientific accuracy: **hybrid**: sound real-world data and dynamics, explicitly qualified approximations for breakup and long-term behavior.
- Collision permutations: satellite–satellite; satellite–cataloged debris; debris–debris; satellite–rocket body/inactive spacecraft; debris–rocket body; **real identified asteroid/meteoroid-like natural object impacting a satellite or other object in a fictional redirected scenario**; secondary collisions where the physical model and timeframe support them. Include pair-order symmetry; never imply all pairings are physically likely.
- Live data: obtain **as many publicly accessible, usable cataloged Earth-orbiting objects as possible**; honest coverage counts. Not GPS-style live telemetry; timestamps and stale-data warnings required.
- Both orbital and Earth-facing effects, but ground risk must be scientifically qualified.
- Full simulation clock with current/past/future epochs where data supports them, pause, play, speed, scrub, reset, replay.
- Browser-based 3D app; hybrid client + Python simulation backend.
- Hackathon MVP now; expandable architecture later.
- Collision initiation: both computed close approaches and user-forced hypothetical contacts.
- Asteroids: start from **real named JPL objects and actual metadata/ephemerides**; user permits modified trajectory ONLY when **clearly labeled hypothetical**. Do not substitute a fabricated asteroid and call it real.
- Fragmentation: physics-based, transparent simplified NASA Standard Breakup Model-inspired approach (NOT a claim of certified NASA model fidelity).
- Secondary cascades: **short horizon (hours to days)**, strict computational caps; do not claim to predict full long-term Kessler syndrome.
- Geographic analysis: orbital ground tracks; potential service exposure only where independently supported; conditional re-entry corridor/uncertainty only where calculation supports it. An orbital ground track **is not** an Earth danger zone.
- Main demo emphasis: **spectacular cinematic collision visualization** without sacrificing source integrity.
- Defer asteroid impacts onto Earth's surface and crater/blast/tsunami modeling until after MVP.
- Implementation workflow: OpenAI Codex.

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

## 4. EXTERNAL DATA AND HONEST COVERAGE

### 4.1 CelesTrak

Reference docs:
- https://celestrak.org/NORAD/documentation/gp-data-formats.php
- https://celestrak.org/satcat/satcat-format.php
- https://celestrak.org/usage-policy.php
- https://celestrak.org/NORAD/elements/

Use supported canonical query forms such as `https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=CSV` and `...gp.php?CATNR=25544&FORMAT=CSV`. Do not assume unverified group names like `GROUP=ALL` produce the entire catalog. Ingest a documented set of object groups and deduplicate by NORAD_CAT_ID, retaining source/epoch conflicts. To obtain additional tracked debris/inactive objects, discover officially documented feeds or authorized bulk sources; preserve coverage limitations rather than claiming a comprehensive full-catalog feed if one is unavailable. SATCAT metadata is not a replacement for missing current orbital elements.

- Current CelesTrak usage policy: GP records typically update every 2 hours; **do not re-download GP more frequently than every 2 hours**, use compressed CSV (preferred over 3× larger JSON) and no hammering/retrying after non-200 responses. Distinguish metadata refresh schedules from propagation frequency.
- Use CSV OMM-compatible fields; support 6-digit+ and potentially 9-digit catalog IDs; do not depend on 5-character TLE identifiers. Define CelesTrak object's `EPOCH`, `NORAD_CAT_ID`, `MEAN_MOTION`, `ECCENTRICITY`, `INCLINATION`, `RA_OF_ASC_NODE`, `ARG_OF_PERICENTER`, `MEAN_ANOMALY`, `BSTAR`, etc. Validate actual record field names and types against upstream.
- Join SATCAT by catalog ID for `OBJECT_TYPE` (`PAY`, `R/B`, `DEB`, `UNK`), operational status if present, launch date, decay date and optional RCS. **RCS is not a measured physical radius or mass.** Never call missing mass 'known'.
- Cache last good snapshots persistently and survive network outage. Show `source`, `last_success`, `element_epoch`, `object_count`, `staleness`, `coverage`, `fallback_mode` in UI. The catalog's latest update does not mean each element record is equally fresh.
- Catalog can contain objects no longer in orbit; filter decayed items appropriately and show uncertainty.

### 4.2 JPL asteroids

Reference docs:
- https://ssd-api.jpl.nasa.gov/doc/horizons.html
- https://ssd-api.jpl.nasa.gov/doc/
- https://ssd.jpl.nasa.gov/horizons/manual.html

Backend obtains **real identified asteroid metadata** and actual ephemerides for user-selected epochs. Prefer Earth-center vectors in a documented common frame (e.g., Horizons `EPHEM_TYPE=VECTORS`, Earth center `500@399`, `REF_PLANE=FRAME`, `REF_SYSTEM=ICRF`, explicit units and time scale) with versioned parsing. Verify individual request syntax; note time-scale differences such as TDB vs UTC and convert deliberately. JPL's API cannot be called directly from a browser due to service/CORS restrictions. Cache sensible prepared asteroid choices if the service is unavailable.

**Required fictional impact mode:** show the real asteroid name, source, original ephemeris, estimated/unknown size and the user's edited event time. For a hypothetical impact on a satellite, create an explicitly modified event state (e.g., replace position so it intersects selected target while preserving or editing a velocity vector); save `original_state`, `modified_state`, reason and coordinate frame. Display `HYPOTHETIC REDIRECTED TRAJECTORY — NOT A PREDICTION` prominently in scenario form, 3D view, screenshots/reports and exported results. If an arbitrary position change makes the hypothetical path nonphysical, call it **state injection/fictional interception**, not a feasible asteroid deflection, and do not report a meaningful maneuver Δv/cost. Do not pretend a real asteroid naturally strikes an Earth satellite. If no real JPL asteroid data is available and no truthful cached metadata is present, disable this mode with a friendly explanation rather than inventing a named source.

### 4.3 Fixtures and source integrity

Ship a small deterministic **synthetic** fixture catalog (e.g., 12–100 physically plausible objects), a reproducible satellite-satellite collision case, debris-vs-satellite case, and a known-object asteroid demo that activates only if cached **authentic** JPL identity/ephemeris metadata exists. Label these `DEMO / SYNTHETIC DATA`; never show them as current real-world objects. Support offline demo startup; show how to switch to live mode. Fixtures must not be misleadingly presented as observations. Document exact sourcing and attribution.

## 5. COORDINATES, TIME, AND ORBITAL PHYSICS

- Time: UTC ISO 8601 over API; timezone-aware timestamps. Store Unix/Julian time safely; all calculations use real seconds, not animation frames. JPL vector epochs may be TDB/TT; explicit conversion required.
- SGP4 output: **TEME (km and km/s)**, not directly Earth-fixed latitude/longitude and not automatically J2000/ICRF. Convert via Astropy with appropriate Earth rotation handling to **ITRS** for Cesium Earth-fixed visualization and lat/lon. For collision arithmetic, transform states into a **single consistent inertial frame** (document whichever is chosen) before differencing or combining with JPL asteroid vectors; include test cases to catch wrong-frame mistakes.
- Never mistake mean orbital elements for Cartesian state vectors. Do not put km directly into Cesium APIs expecting meters.
- Earth gravitational parameter `mu = 398600.4418 km^3/s^2`, equatorial radius `R = 6378.137 km`, J2 `= 1.08262668e-3` as initial documented constants; choose a consistent terrestrial reference model.
- Debris acceleration: `a = -mu*r/|r|^3 + a_J2`, where with `z` component the usual Earth J2 Cartesian acceleration is implemented and unit-tested; optional drag (`Cd`, area/mass, density model) is disabled until tested, then clearly qualified. No arbitrary downward motion to force debris to hit Earth.
- Use vectorized RK4 or adaptive DOP853 with numerical tolerances/step-size that scale to hundreds–thousands of fragments for hours–days. Require deterministic results for same seed and model settings, independent of render frame rate. If individual trajectories cross an approximate atmosphere boundary (default 120 km), mark `ENTRY_THRESHOLD_CROSSED` and stop propagation as appropriate; do NOT assert ground strike or surviving fragments.
- If playback scrubs backwards, read/interpolate precomputed trajectory samples; do not integrate backwards from a dissipative/terminal state blindly. Use adequate interpolation or short segments for visual accuracy; report simulation sample spacing.
- SGP4 input element epoch validity: warn when propagation is far from the elements' epoch; do not label long-range extrapolation operationally accurate.

## 6. COLLISION SETUP AND PRECISE BEHAVIOR

### Natural close-approach mode

Allow selection of a relevant pair or choose documented close-approach candidates. Estimate time of closest approach (TCA) over a user-selected horizon by sampling first and refining candidate minima numerically. Output encounter epoch, closest separation in meters or km, relative velocity in km/s, catalog snapshot timestamp and stated assumptions. Distinguish **close approach** from **physical contact**. Do not invent a collision probability from distance alone; reliable collision probabilities need orbit covariance/uncertainty that the public GP catalog generally does not provide. Use configurable assumed hard-body radius only if explicitly labeled as an assumption. Do not declare an inevitable actual-world collision.

### Forced hypothetical collision mode

Select any two distinct orbiting objects. If their natural state vectors do not intersect, explicitly construct a **counterfactual collision** by editing one participant's event position to a chosen impact point while preserving or user-editing velocity; optionally adjust impact angle and target point. Log and display the original separation and the modification, including `scenario_type=FORCED_HYPOTHETICAL`. Never describe the forced impact as an actual conjunction or realistic maneuvre. For a natural-contact case supported by the assumed radii, `scenario_type=NATURAL_GEOMETRIC_CONTACT` can be used with careful caveats.

### Physical impact calculations

- Parent input state: mass (known/assumed), approximate effective size/shape (known/assumed), inertial position and velocity, impact epoch, collision geometry. Most satellites do not have publicly confirmed mass/radius; present clearly labeled presets with editable values and confidence.
- Compute `v_rel = |v1-v2|`, reduced mass `mu_red = m1*m2/(m1+m2)`, center-of-mass velocity, kinetic energy in COM frame `E_rel = 0.5*mu_red*v_rel^2` (use SI for Joules), and a specific-energy indicator such as `0.5*m_impactor*v_rel^2 / m_target` with correct units and direction. Consider NASA's approximate 40 J/g catastrophic criterion only as one model assumption, never a universal proof of an event's outcome.
- Separate a physically modeled impact energy/data panel from a cinematic flash/glow/sparks. No atmospheric fireball in a vacuum. No arbitrary energy-to-ground-damage interpretation.

## 7. FRAGMENTATION ENGINE

Build a **transparent, approximate NASA-breakup-model-inspired** generator, not a complete certified implementation. Cite NASA material and explain the approximation in `docs/PHYSICS.md`. Design a pluggable `FragmentationModel` interface for future standard-model fidelity.

- Inputs: collision state and parent masses, sizes (or labeled assumptions), relative velocity, impact geometry, pseudo-random seed, length cutoff, `max_simulated_fragments` default 300–800, cap configurable safely to e.g. 1,500 or 2,000 depending on runtime; include material/area-to-mass priors as configurable approximations.
- Sample representative characteristic lengths from a documented heavy-tailed distribution, infer approximate masses/areas from adjustable physical assumptions, and sample breakup-frame velocity impulses from a physically motivated size/area-to-mass-correlated distribution with bounded tails.
- Model only a **resolved representative subset** if full physical count would be huge. Track `resolved_fragment_count`, `estimated_unresolved_count` (only if a justified distribution produces an estimate), and `unresolved_mass_kg`. Do **not** equate 600 rendered fragments with 600 real physical debris objects.
- Mass accounting: resolved mass sum must never exceed available total parent mass, residual mass explicitly stored. Total center-of-mass momentum must be conserved across resolved components plus residual aggregate/bucket to declared numerical tolerance; relative fragment kinetic energy cannot exceed an explicitly defined available energy budget. Correct sampled velocity field or scale appropriately; clearly explain approximations where residual aggregate is not individually integrated.
- For fragments, store inertial epoch state vectors and optional sample weight. For visual effect create separate transient VFX particles not included in physics inventory; user can toggle visual exaggeration.
- Reproducibility: same scenario input + snapshot hash + seed + model version yields same numerical results within documented numerical tolerance.

## 8. SHORT-TERM SECONDARY ENCOUNTERS AND CASCADES

Horizon selectable from e.g. 1 hour / 6 hours / 24 hours / 72 hours (hours-days). Limit a hackathon MVP to 24 hours if 72-hour propagation is too costly, but retain API support/clear limits. Require at least screening against selected nearby cataloged objects; comprehensive all-pairs collision search across every catalog object plus every fragment is not required in MVP.

- Broad phase: time-bucketed spatial bins, KD-tree, or similar. Avoid O(N_catalog × N_fragments × N_timesteps) pairwise loops. Screen near relevant orbits/altitude shells and refine minima for candidates with continuous relative-motion approximation or bounded local minimization. Include satellite–fragment screening, optionally fragment–fragment screening with strict caps.
- Output `screened_close_approach` for minimum separations within configurable thresholds (e.g., 10 km, 100 km), including temporal sampling precision, and only label `geometric_contact_in_model` if trajectories intersect within explicit assumed hard-body radii and time step is refined. **No real-world collision prediction**.
- Optional actual secondary fragmentation of a computed model-contact event, at most two generations and hard caps on fragment count, event count, runtime, and numerical instability. State when further events are truncated. Never have a scripted animation masquerade as a calculated cascade.
- For risk reporting, compute changes in simulated debris count/density by altitude/inclination bins and changes in close-approach frequency **within the chosen screened sample**. Never extrapolate local results to verified Kessler syndrome or general collision probability.

## 9. EARTH-FACING CONSEQUENCES / MAP LAYERS

Implement **separate overlays** with distinct legends:

A. `ORBITAL_HAZARD`: altitude/latitude/longitude visualization of debris orbital tracks and statistically aggregated shell occupancy, e.g. 100-km altitude bins and inclination bins. A globe ground projection may show where orbital objects pass overhead, but mark it **projection only / not an impact warning**.

B. `SATELLITE_EXPOSURE`: cataloged satellites screened for fragment close approaches, with event list, minimum separation, timestamp, model assumptions, and mission type if metadata supports it. When describing services (communications, navigation, weather), say **potential service exposure** only; no predicted outage or affected population without validated service-footprint and failure models.

C. `CONDITIONAL_ENTRY`: only for fragments actually simulated crossing an entry threshold (e.g. 120 km). Show approximate crossing geolocation and event time. With a defensible sensitivity ensemble, draw a **clearly illustrative uncertainty corridor** and source the assumptions; otherwise show a crossing point with a warning that no reliable ground-impact corridor can be determined. Never draw danger polygons based solely on orbital ground tracks. No casualty figures, no city threat claims, no guarantee of surviving objects reaching ground. For MVP do not attempt detailed asteroid atmospheric entry or surface-impact/crater modeling.

D. `DATA_LIMITATIONS`: visible dynamic panel explaining uncertainty, excluded effects, catalog coverage, data age, perturbations excluded and forced-scenario modifications.

## 10. CINEMATIC 3D UX / PRODUCT DESIGN

Design language: premium scientific mission control; dark navy/charcoal (not pure-black everywhere), deep blue/teal cool highlights, amber for hypothetical situations, red only for actual modeled collision markers, legible text, realistic Earth atmosphere/day-night cues, restrained glow, elegant typography and polished transitions. Keep it useful for the public, not a hard-to-read Hollywood HUD.

**Desktop layout:**
- Main full-bleed globe, smooth orbit/fly camera, Earth-centered view, camera controls, subtle stars, visible terminator/day-night illumination where supported, optional satellite orbit arcs, dynamic selection halos, debris trails. Attribution always visible.
- Top strip: project branding, UTC time, `LIVE CATALOG / CACHED / OFFLINE DEMO`, catalog count, object coverage, source timestamp/age, settings and help.
- Left drawer: search by name/NORAD ID, filters (active/inactive/debris/rocket body/unknown, altitude, inclination, mission type), selectable objects, collision lab form.
- Right inspector: object identity, type, known/assumed size/mass, altitude, speed, inclination, ephemeris/epoch, distance, selected trajectory and direct explanation of what is real versus hypothetical.
- Bottom timeline: play/pause, step forward/back, arbitrary scrub, speed presets (1×, 10×, 100×, 1000×, 10000× if stable), exact UTC time, event pins, jump to impact, replay from checkpoint, timeline end state. Maintain consistent world state while scrubbing.
- Collapsible results drawer: collision summary, fragment distribution charts, affected orbital shells, close-approach table, data provenance, export.
- 3 distinct modes: `Live Orbit`, `Collision Laboratory`, `Impact Intelligence`, with seamless transitions.

**Signature 20–30 second demonstration flow:**
1. Realistic globe, many genuine cataloged orbital markers visible, live/cached timestamps, user selects two spacecraft.
2. UI warns forced impact is fictional and shows chosen epoch; user clicks `Simulate Hypothetical Collision`.
3. Camera smoothly approaches the event at a comprehensible visual scale; near-impact countdown, velocity vector trails, cinematic slow-motion and brief shock-like light bloom **explicitly decorative**.
4. Fragments shoot outward and curve along integrated orbital trajectories, not straight-line forever; size/altitude coloring and optional exaggerated visual scale.
5. Scrub time forward; Earth overlays illuminate affected orbital bands, close approaches, and only legitimate entry-threshold markers.
6. Click a fragment or threatened spacecraft to see numeric source-backed results, limitations and provenance. Export concise scenario report.

**Visual integrity:** spacecraft are microscopic at planetary scale. Use exaggerated icon/model scaling and annotate it `visual sizes exaggerated`; orbital positions and physical distances must still use truthful numerical coordinates. Separate lens-friendly VFX particle positions from scientific debris position arrays. No flash effect necessary on lower-power GPUs; progressive enhancement. Optimize camera to avoid clipping/strobing. Provide `Reduce motion` and `Low graphics` toggles.

**Responsive/mobile:** smaller catalog and visual effects defaults; search, scenario preset, globe, timeline and result summaries remain usable without hover. Keyboard accessibility, screen reader labels, color-vision safe legends, errors/empty states. Use real, meaningful text—not placeholder charts and counters.

## 11. API AND CONTRACTS

Use versioned routes `/api/v1/`. Responses must validate through Pydantic and typed frontend bindings. Include `schema_version`, `generated_at_utc`, clear metric units, relevant coordinate frames, and provenance for all scientific outputs. Recommended endpoint contract:

- `GET /health` → service version, cache readiness, simulation readiness.
- `GET /api/v1/catalog/status` → `{mode, sources, fetched_at, element_epoch_min/max, records, displayable_count, catalog_snapshot_id, warning_codes}`.
- `GET /api/v1/objects?query=&kind=&limit=&cursor=` → paginated catalog search.
- `GET /api/v1/objects/{id}` → identity, catalog metadata, source, ephemeris freshness, optional assumed physical attributes.
- `GET /api/v1/states?at=UTC&scope=visible|selected|preset&format=json|binary` → batched positions + velocities (specify frame, km or meters, and sampling time); use dense binary only if worthwhile.
- `GET /api/v1/asteroids/search?q=` and `GET /api/v1/asteroids/{id}/ephemeris?start=&stop=` → verified backend JPL-derived output; no frontend-to-JPL calls.
- `POST /api/v1/scenarios` → validate/save a scenario and return scenario ID + acknowledged assumptions.
- `POST /api/v1/scenarios/{id}/run` → job ID, deterministic seed, state `queued|running|completed|failed|cancelled`.
- `GET /api/v1/jobs/{id}` → progress phase, percentage where meaningful, errors.
- `GET /api/v1/scenarios/{id}/results` → collisions, fragment stats, orbital risk bins, secondary encounter events, re-entry crossings, warning/limitations.
- `GET /api/v1/scenarios/{id}/frames?from=&to=&step=&cursor=` → paginated render-friendly time samples, no huge single JSON responses.
- `GET /api/v1/scenarios/{id}/report?format=json|markdown` → reproducibility metadata and a factual scenario summary; PDF optional stretch only.

Sample normalized object (illustrative schema; source parser adapts field names):

```json
{
  "id": "NORAD:25544",
  "name": "ISS (ZARYA)",
  "kind": "PAYLOAD",
  "operational_status": "UNKNOWN",
  "state_source": "CELESTRAK_GP",
  "element_epoch_utc": "2026-11-21T00:00:00Z",
  "catalog_snapshot_id": "sha256:...",
  "mass_kg": null,
  "effective_radius_m": null,
  "physical_properties_basis": "UNAVAILABLE",
  "orbit": { "format": "OMM_CSV", "theory": "SGP4", "frame": "TEME" }
}
```

Sample scenario request:

```json
{
  "schema_version": "1.0",
  "type": "FORCED_HYPOTHETICAL",
  "epoch_utc": "2026-11-21T12:00:00Z",
  "participants": [
    {"object_id": "NORAD:25544", "assumed_mass_kg": 420000, "assumed_radius_m": 50},
    {"object_id": "NORAD:12345", "assumed_mass_kg": 1500, "assumed_radius_m": 3}
  ],
  "forced_contact": {"move_participant_index": 1, "impact_geometry": "CENTERED"},
  "simulation": {"seed": 42, "duration_hours": 24, "output_step_seconds": 60, "max_resolved_fragments": 600, "max_cascade_generations": 1},
  "requested_products": ["TRAJECTORIES", "ORBITAL_HAZARD", "SECONDARY_ENCOUNTERS", "ENTRY_CROSSINGS"]
}
```

**Important:** example IDs, timestamps and physical sizes above are schema illustrations, NOT asserted actual mass/radius/epoch for those catalog objects. API must refuse requests referencing missing IDs; tests use fixtures. For asteroid-driven scenarios add `asteroid_id`, `original_ephemeris_ref`, original/modified state and `fictional_redirect=true`. Add strict server-side validation and error envelopes.

**Required provenance type**, included on every alert/analysis product:

```ts
type EvidenceKind =
  | 'CATALOG_OBSERVATION'
  | 'PROPAGATED_ESTIMATE'
  | 'HYPOTHETICAL_SIMULATION'
  | 'SYNTHETIC_DEMO';

type Provenance = {
  kind: EvidenceKind;
  source: string;
  sourceUrl?: string;
  sourceFetchedAtUtc?: string;
  sourceEpochUtc?: string;
  catalogSnapshotId?: string;
  modelVersion?: string;
  coordinateFrame?: string;
  assumptions: string[];
  limitations: string[];
  isStale?: boolean;
};
```

Respect client/server CORS origins, strict provider host allowlists (prevent SSRF), validated asteroid IDs/time ranges, max body/request sizes, max simulation horizon and fragment count, cancellation/timeouts and reasonable in-memory job limits. Do not expose upstream requests as arbitrary URLs in a public proxy. Keep provider credentials optional and server-side. Add attribution/licensing notes. No auth required for local hackathon MVP, but do not expose unlimited compute jobs publicly without quotas.

## 12. PERFORMANCE AND RELIABILITY

Performance targets on a reasonably modern laptop (record actual measured hardware/browser in report; these are targets, not invented completed benchmarks):
- Globe reaches a usable initial scene in ~5 seconds under reasonable local conditions using a cached sample; progressive catalog loading thereafter.
- Show at least 5,000 simultaneous catalog markers at ~30 FPS or higher on a midrange laptop, without a per-object React rerender; scale up toward 20,000+ or more with LOD, occlusion, batching and quality controls. Publish actual achieved counts/FPS; no fake coverage.
- A standard deterministic collision demo with ~300–600 resolved fragments and ~24 hours of propagation should complete within ~60 seconds on a developer laptop if feasible; measure actual runtime and document the achieved limit. Show phase/progress. Streaming partial results optional.
- Memory bounded by downsampling, frame pagination, typed arrays, and backend caches; avoid huge request bodies or >100K React nodes. Debounce user time scrubs; cache samples and avoid rerunning physics for cosmetic camera changes.
- Handle absent network, HTTP 403/429/5xx, provider schema drift, stale element epochs, numerical instabilities, no matching catalog records and browser WebGL issues with readable fallback statuses. Do not endlessly retry and violate CelesTrak usage policy.
- Support data source mode `LIVE`, `CACHED`, or `DEMO`; UI always reflects mode. Do not silently swap providers or mode.

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

## 14. 24-HOUR HACKATHON EXECUTION PLAN

Implement in this order, keeping the main branch runnable at each gate:

**Milestone 0 — Foundation (1 hour)**
- Inspect repository and environment; initialize monorepo, commands, env example, formatting, CI-ish test scripts, README. Render a working Cesium globe with source attribution and token-free fallback. First screenshot.

**Milestone 1 — Real orbital layer (3 hours)**
- CelesTrak connector, CSV OMM parsing, snapshot caching, sample fixture fallback, SGP4 and correct TEME→ITRS, object search, type colors, a few thousand batched markers and selected orbit trails. Display mode, count, last successful source update. Tests for OMM parsing and basic propagation.

**Milestone 2 — Essential UI and timeline (4 hours)**
- Premium desktop layout, sidebar search/inspector, globe controls, timeline play/pause/speed/scrub, object focus, responsive states, filters, altitudes and chart labels. Sample data works offline; source mode obvious.

**Milestone 3 — Collision core (5 hours)**
- Forced hypothetical satellite-satellite and satellite-debris setup; consistent inertial frame; relative velocity/energy calculations; deterministic breakup generation with mass/momentum checks; numerical integration of ~300–600 fragments; results timeline. Unit tests plus visible working animation.

**Milestone 4 — Cinema and impact intelligence (4 hours)**
- Camera approach, impact visual effects, trails, time acceleration/replay, orbital hazard histograms, selected-neighbor short-term encounter screening and result explanations; ground track overlays and entry-threshold markers only when supported. Maintain scientific/visual separation.

**Milestone 5 — Known asteroid scenario (3 hours)**
- Backend real JPL lookup/ephemeris retrieval and cache; clearly fictional state-injected impact on a selected satellite; provenance labels, failure state if NASA unavailable; tests. If network is down, do not fabricate astronomy data.

**Milestone 6 — Finish, verify and demonstrate (4 hours)**
- Reliability and performance audit, fix blockers, browser screenshots and visual polish, automated checks, documentation, known limitations, deterministic preset demos, one-command startup, a 60–90 second live demo script, actual benchmark results.

If behind schedule, preserve: **working Earth + real/cached objects + selectable forced collision + physically propagated fragments + replay + visible qualifications**. Defer advanced asteroid integration, cascades, fancy chart exports and polished re-entry overlays rather than substituting fake data or breaking the core. Keep a visible `MVP vs stretch` checklist in project docs.

## 15. TESTING AND SCIENTIFIC VALIDATION

### Automated scientific tests

1. **SGP4:** verify OMM parsing, correct epoch handling, numeric error codes and trusted SGP4 reference states within a specified tolerance; test six-digit identifiers. Validate TEME→ITRS and TEME→common-inertial roundtrips at known epochs, Earth rotation and proper km↔m conversion.
2. **Kepler propagation:** for J2 disabled and drag disabled, numerical integration approximates a two-body circular/elliptic orbit against analytic solutions; relative energy/angular momentum drift bounded and tested across chosen time step/tolerance. With J2, validate expected nodal precession direction and convergence against smaller time step.
3. **Collision geometry:** deterministic known intersecting and nonintersecting trajectories; correct minima and time-of-closest-approach; ensure forced events retain the `HYPOTHETICAL` flag all the way to exported report.
4. **Energy and conservation:** relative kinetic energy correct in SI; cumulative represented mass + residual mass equals parent mass within tolerance; modeled momentum conservation; velocity impulse budget and seed reproducibility. Verify no NaNs, negative mass or hyperbolically giant velocities without explicit bounds.
5. **Secondary encounters:** cross-check accelerated screening against brute-force small synthetic fixtures; prevent a near miss being labeled a contact merely because it passes a coarse time-bin radius.
6. **Entry threshold:** only mark threshold crossing when a propagated fragment crosses it; confirm an orbital ground track alone produces no re-entry alert.
7. **JPL integration:** parse authentic documented response fixtures; handle ambiguous IDs, missing sizes, API errors, and UTC/TDB conversion. Assert that `fictional_redirect` is always displayed/exported.
8. **Offline cache:** network timeout or provider HTTP errors causes explicit `CACHED` or `DEMO` mode, not fabricated `LIVE` data.

### UX/browser verification

- Manual/automated smoke: app boots, 3D Earth visible, search works, selected object focuses, collision can run, explosion VFX + modeled fragment trajectories visible, clock replays/scrubs, results update, warnings/legend readable, report exports, mobile has usable essential flow.
- No browser console errors, failed loads or silently ignored API errors; no content overflow/overlapping panels at 1366×768 and mobile 390×844. Respect reduced motion.
- Validate catalog attribution and data age. Provide a visible disclaimers section and per-scenario evidence badges.
- Record real measured FPS, objects rendered, run duration, backend RAM, data snapshot ages, and tests executed. **Never report imagined benchmark numbers**.

### Historical science reference (optional comparison, not a required recreation)

The Iridium 33–Cosmos 2251 collision (2009) may be used to explain orbital fragmentation at a qualitative level, or for regression against documented high-level parameters when an authentic historical record has been sourced. Do not claim to recreate its exact debris population or positions from current OMM snapshots.

## 16. ACCEPTANCE CRITERIA — DEFINITION OF DONE

**Hard gate: runnable application**
- [ ] Working dev startup commands for frontend and backend, tested on clean env or described precisely.
- [ ] Realistic 3D Earth functional without a paid credential; clearly labeled token-free fallback.
- [ ] Real public orbital elements ingested when network available; valid SGP4 propagated positions and honest source timestamps; offline demo works.
- [ ] Search/filter/select live or cached cataloged objects and examine path/details.
- [ ] At least satellite–satellite and satellite–debris **hypothetical forced** collisions run end to end, producing physical state-based debris and independent cinematic VFX.
- [ ] Numerical debris trajectories progress across time and are replayable/scrubbable deterministically.
- [ ] Orbital exposure results are derived from simulated positions; secondary close approach analysis at least on bounded relevant set.
- [ ] Earth overlay shows ground tracks and explicitly differentiates projections from re-entry events; no invented country/city hazard zones.
- [ ] All what-if collisions clearly marked fictional; no unsupported real-world collision probability.
- [ ] Scenario reproducibility includes random seed, model version, scenario parameters and input catalog snapshot identifier.
- [ ] Major computation has passing tests; frontend build and typecheck pass; no critical UI overlap.
- [ ] README includes setup, actual tested commands, architecture, model limitations, screenshots or capture procedure, demo script and honest implemented/pending checklist.

**Second-tier acceptance (complete if resources permit)**
- [ ] Backend JPL known-asteroid discovery and ephemeris integration; fictional asteroid-to-satellite collision with prominent `redirected trajectory` label.
- [ ] Bounded cascading fragment contact generation and warning events.
- [ ] Conditional entry-threshold map with computed geolocation and explicit uncertainty/limitations.
- [ ] Mobile-friendly reduced-feature flow and low-power graphics mode.
- [ ] Exported human-readable scenario report; self-contained prerecorded deterministic fixture demonstration.

**Explicit exclusions from MVP**: asteroid–Earth surface impacts, crater/blast/tsunami zones, precise debris-on-ground casualties, authoritative collision probabilities without covariance, fully predictive Kessler-syndrome evolution over years, fully exhaustive catalog coverage when no suitable source exists, precise satellite service outage/population models, mission-critical alerts.

## 17. USER-FACING HONESTY, LEGALITY, AND SAFETY

Keep a concise always-accessible notice: **“Educational research simulation. Catalog positions are estimates; collision scenarios and impact trajectories are hypothetical unless explicitly stated otherwise. Not for spacecraft operations or emergency decisions.”**

- Display `Observed catalog metadata`, `Propagated estimate`, `Hypothetical event`, `Synthetic demo` as distinct states in visualizations and reports.
- Do not call an OMM feed “live telemetry.” Do not call CelesTrak SATCAT operational status fully accurate for every object.
- Do not report an Earth “affected country” just because a satellite passes above it; separate geographical footprint, orbital exposure, and modeled entry crossing.
- Do not invent asteroid threats, real event forecasts, geographic danger zones, probability percentages, emergency alerts, deaths, economic damage or active collision warnings.
- Respect data licenses, CelesTrak usage policy and NASA/JPL fair-use/API rules. Source attribution must be visible.
- Expose numerical approximations, sampling, missing sizes/masses, drag limitations and data-epoch staleness in `LIMITATIONS.md` and the UI.

## 18. OPERATING INSTRUCTIONS FOR CODEX

1. **First** examine existing files, package manager, environment and repository state; identify reusable code before replacing anything. Check upstream docs of packages and data sources as needed. Do not silently delete user work.
2. Write a concise prioritized task list and then **execute it**, not just describe it. Work independently through milestones. If a change fails, debug and rerun tests.
3. Start with one complete vertical slice (cached catalog → propagation → globe → forced collision → fragment trajectories → results) before expanding features. Keep the app always runnable.
4. Use checked-in deterministic fixtures, real integration tests where network is available, and explicit source state. Never fake a successful live API response or represent a CSS-only effect as physics.
5. Use type-checked, testable modules, robust error handling and strict science contracts. Visual effects must be independent from the numerical model.
6. After major milestones execute relevant test/build commands and, if browser tooling is available, **actually open the app and inspect/repair screenshots** at desktop and mobile dimensions. If browser access is unavailable, state that and still run code-level checks.
7. If you must cut scope to fit time, preserve the core, list deferred items truthfully, and leave working extension interfaces. No half-implemented screens with fake buttons.
8. Provide a complete `README.md`, `.env.example`, dependency lockfile, `.gitignore`, source/license references, `docs/PHYSICS.md`, `docs/DATA_SOURCES.md`, `docs/LIMITATIONS.md`, and a short demo script.
9. On completion, report: built features, live versus fallback data behavior, commands to run, exact tests and outcomes, real benchmark measurements if captured, known limitations, and remaining backlog. Do **not** claim passes or measured performance without running them.
10. **Begin implementing now.** Do not respond with only a proposal, plan, or questions.

## 19. REFERENCE STARTING POINTS

- CelesTrak current GP formats and supported queries: https://celestrak.org/NORAD/documentation/gp-data-formats.php
- CelesTrak usage policy (obey current version): https://celestrak.org/usage-policy.php
- SATCAT metadata specification: https://celestrak.org/satcat/satcat-format.php
- JPL Horizons API documentation: https://ssd-api.jpl.nasa.gov/doc/horizons.html
- JPL API terms/fair use: https://ssd-api.jpl.nasa.gov/doc/
- Astropy SGP4 TEME frame transformations: https://docs.astropy.org/en/stable/coordinates/satellites.html
- Python SGP4 implementation: https://pypi.org/project/sgp4/
- CesiumJS docs: https://cesium.com/learn/cesiumjs/ref-doc/
- NASA orbital debris technical reference (NASA OTPS 2024, includes Standard Breakup Model discussion): https://www.nasa.gov/wp-content/uploads/2024/05/2024-otps-cba-of-orbital-debris-phase-2-plus-svgs-v3-tjc-tagged.pdf

Treat the above as starting points and verify their current APIs before coding. Implement the application.
