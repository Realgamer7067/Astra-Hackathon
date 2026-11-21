# ASTRA interface baseline

## Coordination status

TASK-001 implements `GET /health` and `GET /api/v1/demo`. Other endpoint descriptions below are contracts for the owning lanes to implement. The [Pydantic models](../services/api/app/models/wire.py) define the foundation wire fields. [OpenAPI](../packages/contracts/openapi.json) and [TypeScript](../packages/contracts/api.d.ts) are generated from those models. Lane owners coordinate changes before modifying these shared shapes.

The collision runner adds `POST /api/v1/scenarios`, `POST /api/v1/scenarios/{id}/run`, `GET /api/v1/jobs/{id}`, `POST /api/v1/jobs/{id}/cancel`, and `GET /api/v1/scenarios/{id}/frames`. `GET /api/v1/scenarios/{id}/simulation` supplies the raw physics summary and forced-contact audit. The exposure lane can consume those outputs when implementing `/results` and `/report`. Creation uses `application/json` and accepts the fixed synthetic epoch. Trajectories and conditional entry crossings are available products. Errors use the shared envelope.

The local worker retains up to 10 scenarios per process, including up to two active jobs. The sample budget is one million fragment positions per scenario. A frame cursor is valid for the same time window and sample step. Pages contain up to 120 epochs and 50,000 positions. The final sample can be closer to the preceding sample when the duration falls between regular output samples. After a modeled entry crossing, that fragment has no later positions.

The demo route returns a versioned bundle with catalog status, object records, a fixed ITRS marker snapshot, and schema examples for a forced scenario, job, frame page and result. The frame example is empty because no collision was computed. All fixture evidence is `SYNTHETIC_DEMO`. Separate lane endpoints must carry their own provenance and validation. In the MVP request example below, `max_cascade_generations` must be `0`.

Regenerate from the repository root whenever the API schema changes:

```bash
uv run --locked python -m scripts.export_openapi
npm run contracts:generate
```

## Shared wire decisions

- UTC ISO 8601 timezone-aware epochs; inertial state frame GCRS in km and km/s; render state frame ITRS in meters and meters/second. Every batch declares frame, units, epoch and provenance.
- Object IDs are strings, including NORAD numeric identifiers of six or more digits; physical attributes are nullable and assumptions explicit.
- Error envelope: {error: {code: string, message: string, details: object}, request_id: string}. No provider internals or secrets in messages.
- Object search defaults to limit 50, maximum 200; opaque cursor or null. Empty success is items:[], next_cursor:null. Reject invalid requests with 422, missing IDs with 404, capacity exhaustion with 429, upstream unavailability with 503.
- Scenario defaults: seed 42, duration 24 hours, output spacing 60 seconds, resolved cap 600. Server hard limits: horizon 24 hours, 1,500 fragments, 2 active jobs, 10 retained jobs, 120-second job timeout, 1 MiB request body. Secondary generation is zero in MVP. Surface truncation and missing products explicitly.
- Frame page maximum 120 sample epochs and 50,000 position records; reduce page size when fragment count requires it. Response includes next_cursor, sample_step_seconds, scenario_id and provenance. Never return an entire large run unpaged.
- Add POST /api/v1/jobs/{id}/cancel, idempotent for terminal jobs. Jobs use queued/running/completed/failed/cancelled states.
- A source-mode change is explicit in status and every analysis product. Snapshots are immutable hash-identified inputs.
- Unknown mass/radius blocks collision execution until the user acknowledges an assumption. Reject duplicate/missing participants, non-finite numbers, nonpositive masses and out-of-limit simulations.

## Feature contracts

| ID | Producer | Consumers | Owning task |
|---|---|---|---|
| CATALOG-v1 | catalog/orbit | explorer, globe, scenarios, screening | TASK-002 |
| SCENARIO-v1 | scenario/job/physics | scenario form, replay, results | TASK-003 |
| FRAMES-v1 | orbit/propagation | globe and timeline | TASK-001 schema; TASK-002/003 producers |
| EXPOSURE-v1 | screening/exposure | results and report | TASK-005 |
| PROVENANCE-v1 | all server producers | every client feature/export | TASK-001 |

Mock fixtures must validate against the same schemas and carry SYNTHETIC_DEMO. Never display a mocked job as a completed real run. Provider source schemas are separately validated at ingestion.


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
  "simulation": {"seed": 42, "duration_hours": 24, "output_step_seconds": 60, "max_resolved_fragments": 600, "max_cascade_generations": 0},
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
