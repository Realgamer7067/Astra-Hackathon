# ASTRA physics specification

Implementation requirements, not claims of completed validation. The backend owns scientific states; all numerical tolerances must be recorded with tests.

## Local collision model

The synthetic snapshot supplies ITRS positions and velocities. Astropy converts both to GCRS at the same UTC epoch. At forced contact, the moved object's position becomes the target's position and its inertial velocity stays unchanged. The result stores both versions and the original separation. Replay samples are converted to ITRS meters at their own epochs with bundled Earth orientation data.

The representative breakup uses a truncated power law for lengths and divides 60% of parent mass according to the cube of those lengths. It subtracts the mass-weighted mean velocity impulse so the resolved pieces and the unresolved mass share the center-of-mass momentum budget. The unresolved mass is represented as an aggregate moving with the center of mass. The impulse cap is 0.5 km/s and the fragment relative-energy budget is 15% of the impact energy. Those fractions are model assumptions. The resolved count describes the sample, and the model does not estimate the full number of pieces.

RK4 advances at steps of up to 15 seconds with two-body gravity and J2. The Earth's pole is transformed to GCRS at impact and held fixed for the run. A crossing of a sphere with radius equal to the equatorial Earth radius plus 120 km terminates that sampled trajectory. Position and time at the crossing are interpolated within the integration step. Geodetic coordinates identify the modeled crossing only. Drag, further breakup, surface impacts and survival are outside the model.

The unit tests compare a two-body circular orbit with its analytic position to within 0.02 km after 5,400 seconds, check the direction of J2 nodal precession and verify that fragments which cross the threshold disappear from later samples. Separate tests cover seeded output and mass, momentum and energy budgets.

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
