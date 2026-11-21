# ASTRA scope and limitations

Current implementation status: planning only. No simulation, catalog coverage, test results for science, or performance measurements exist yet.

MVP excludes surface impacts, casualties, authoritative probabilities, long-term Kessler predictions, precise service outages and fabricated full-catalog coverage. Asteroid integration and secondary fragmentation are optional.

## 17. USER-FACING HONESTY, LEGALITY, AND SAFETY

Keep a concise always-accessible notice: **“Educational research simulation. Catalog positions are estimates; collision scenarios and impact trajectories are hypothetical unless explicitly stated otherwise. Not for spacecraft operations or emergency decisions.”**

- Display `Observed catalog metadata`, `Propagated estimate`, `Hypothetical event`, `Synthetic demo` as distinct states in visualizations and reports.
- Do not call an OMM feed “live telemetry.” Do not call CelesTrak SATCAT operational status fully accurate for every object.
- Do not report an Earth “affected country” just because a satellite passes above it; separate geographical footprint, orbital exposure, and modeled entry crossing.
- Do not invent asteroid threats, real event forecasts, geographic danger zones, probability percentages, emergency alerts, deaths, economic damage or active collision warnings.
- Respect data licenses, CelesTrak usage policy and NASA/JPL fair-use/API rules. Source attribution must be visible.
- Expose numerical approximations, sampling, missing sizes/masses, drag limitations and data-epoch staleness in `LIMITATIONS.md` and the UI.
