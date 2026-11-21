# ASTRA data sources and provenance

Provider policies and APIs must be checked against current official documentation before connector implementation. No live source has been fetched or validated yet.

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

### Offline Earth imagery

The globe uses the July 2004 global Blue Marble Next Generation composite with
topography and bathymetry, credited to NASA Earth Observatory. Its geographic
tile pyramid contains 170 WebP tiles at 512 × 512 pixels and about 3.2 MB in total.
Cesium loads only the tiles needed for the current view. The highest level covers
8,192 × 4,096 pixels globally. The existing Natural Earth II image remains the
local fallback. The Earth surface stays a WGS84 ellipsoid with shaded imagery.
[Source and credits](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-topography-bathymetry/)

To regenerate the asset set, use the 21,600 × 10,800 global JPEG for July at the
source above. Its SHA-256 is
`d225f1f35a6448a4d1d8f6de6e48f3433e470085b70a35800e64f384f269a7b0`.
Downsample the map to 8,192 × 4,096 with Lanczos filtering, and generate levels 0
through 3 at 1,024, 2,048, 4,096 and 8,192 pixels wide. Split each level into
512-pixel square tiles, encode with WebP quality 83, and write the tiles to
`apps/web/public/blue-marble/{z}/{x}/{y}.webp`. Tile coordinates start at the
northwest corner and increase east and south.
