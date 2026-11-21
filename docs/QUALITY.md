# Quality and judging gates

**The product must be complete and reliable, not merely impressive-looking.** Apply every relevant check; tools cannot automatically judge all visual and usability qualities.

## Machine-enforced after stack choice

Before adding application source, the main agent must create `project-checks.json` with runnable argv arrays for:

1. `format`: consistent formatting
2. `lint`: code style and static defects
3. `typecheck`: type/syntax checks or equivalent
4. `unit`: tests of individual units
5. `integration`: cross-component/contract tests
6. `security`: known vulnerabilities, static checks and/or secrets scan
7. `build`: production build

If a category does not apply to the chosen stack, document a **real equivalent check** in its place, not `echo passed`. Add `accessibility` and `e2e` commands where supported. CI must fail if application directories exist without a real check configuration.

## Human and reviewer checks (mandatory where relevant)

- **Functionality:** Real end-to-end happy path, failure path, no demo-only hardcoded success.
- **UI quality:** Clear hierarchy, clean spacing, typography and colors, readable contrast, consistent components, excellent mobile layout.
- **Accessibility:** Keyboard navigation, focus states, labels, semantic controls, meaningful status/error messages, contrast.
- **Originality:** Solves the hackathon's actual problem, distinct value, measurable user benefit.
- **Engineering:** Understandable code, tight scope, healthy architecture, clear contracts, no duplicated magic constants.
- **Performance:** Responsiveness, loading indicators, degraded service behavior, avoid wasteful API calls.
- **Security/privacy:** Secrets excluded, least privilege, validated user input, safe error messages, no unsafe dependencies.
- **Demo:** Deployable, predictable, polished story, graceful backup if Wi-Fi/API fails.

## PR severity

- **Blocker:** Exposed secrets, broken build, major security defect, false test claims, breaking contract, invalid/missing core functionality, serious data loss risk.
- **Major:** Important bug, unreliable integration, inaccessible primary flow, substantial regression or missing agreed tests.
- **Minor:** Non-blocking polish, isolated refactor, optional optimization (prefer follow-up when time is short).

Reviewers must cite concrete files/lines and reproduction steps for blockers/majors. Treat visual quality as a separate manual review, not a pass/fail that lint alone can supply.


# ASTRA-specific acceptance and validation

Targets below are unmeasured. Run the scientific reference tests and actual desktop/mobile walkthrough before claiming completion.

## 12. PERFORMANCE AND RELIABILITY

Performance targets on a reasonably modern laptop (record actual measured hardware/browser in report; these are targets, not invented completed benchmarks):
- Globe reaches a usable initial scene in ~5 seconds under reasonable local conditions using a cached sample; progressive catalog loading thereafter.
- Show at least 5,000 simultaneous catalog markers at ~30 FPS or higher on a midrange laptop, without a per-object React rerender; scale up toward 20,000+ or more with LOD, occlusion, batching and quality controls. Publish actual achieved counts/FPS; no fake coverage.
- A standard deterministic collision demo with ~300–600 resolved fragments and ~24 hours of propagation should complete within ~60 seconds on a developer laptop if feasible; measure actual runtime and document the achieved limit. Show phase/progress. Streaming partial results optional.
- Memory bounded by downsampling, frame pagination, typed arrays, and backend caches; avoid huge request bodies or >100K React nodes. Debounce user time scrubs; cache samples and avoid rerunning physics for cosmetic camera changes.
- Handle absent network, HTTP 403/429/5xx, provider schema drift, stale element epochs, numerical instabilities, no matching catalog records and browser WebGL issues with readable fallback statuses. Do not endlessly retry and violate CelesTrak usage policy.
- Support data source mode `LIVE`, `CACHED`, or `DEMO`; UI always reflects mode. Do not silently swap providers or mode.


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

