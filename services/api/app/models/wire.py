"""Versioned wire models shared by the catalog, scenario, replay and exposure lanes."""

from datetime import datetime, timedelta
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, model_validator


def require_utc(value: datetime) -> datetime:
    if value.utcoffset() != timedelta(0):
        raise ValueError("epoch must be UTC")
    return value


Epoch = Annotated[AwareDatetime, AfterValidator(require_utc)]
Vector3 = tuple[float, float, float]
SourceMode = Literal["LIVE", "CACHED", "DEMO"]
ObjectKind = Literal["PAYLOAD", "ROCKET_BODY", "DEBRIS", "UNKNOWN"]
Product = Literal["TRAJECTORIES", "ORBITAL_HAZARD", "SECONDARY_ENCOUNTERS", "ENTRY_CROSSINGS"]
SnapshotId = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Health(WireModel):
    status: Literal["ok", "degraded"]
    version: str
    cache_ready: bool
    simulation_ready: bool


class ErrorDetail(WireModel):
    code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)


class ErrorEnvelope(WireModel):
    error: ErrorDetail
    request_id: str


class Provenance(WireModel):
    kind: Literal[
        "CATALOG_OBSERVATION", "PROPAGATED_ESTIMATE", "HYPOTHETICAL_SIMULATION", "SYNTHETIC_DEMO"
    ]
    mode: SourceMode
    source: str
    source_url: str | None = Field(None, alias="sourceUrl")
    source_fetched_at_utc: Epoch | None = Field(None, alias="sourceFetchedAtUtc")
    source_epoch_utc: Epoch | None = Field(None, alias="sourceEpochUtc")
    catalog_snapshot_id: SnapshotId | None = Field(None, alias="catalogSnapshotId")
    model_version: str | None = Field(None, alias="modelVersion")
    coordinate_frame: Literal["GCRS", "ITRS", "TEME"] | None = Field(None, alias="coordinateFrame")
    assumptions: list[str]
    limitations: list[str]
    is_stale: bool | None = Field(None, alias="isStale")


class CatalogStatus(WireModel):
    mode: SourceMode
    sources: list[str]
    fetched_at: Epoch | None
    element_epoch_min: Epoch | None
    element_epoch_max: Epoch | None
    records: Annotated[int, Field(ge=0)]
    displayable_count: Annotated[int, Field(ge=0)]
    catalog_snapshot_id: SnapshotId
    warning_codes: list[str]


class OrbitDescriptor(WireModel):
    format: Literal["OMM_CSV"]
    theory: Literal["SGP4"]
    frame: Literal["TEME"]


class CatalogObject(WireModel):
    id: Annotated[str, Field(min_length=1)]
    name: str
    kind: ObjectKind
    operational_status: Literal["ACTIVE", "INACTIVE", "UNKNOWN"]
    state_source: Literal["CELESTRAK_GP", "SYNTHETIC_DEMO"]
    element_epoch_utc: Epoch | None
    catalog_snapshot_id: SnapshotId
    mass_kg: Annotated[float, Field(gt=0)] | None
    effective_radius_m: Annotated[float, Field(gt=0)] | None
    physical_properties_basis: Literal["OBSERVED", "ASSUMED", "UNAVAILABLE"]
    orbit: OrbitDescriptor | None


class CartesianState(WireModel):
    object_id: str
    position: Vector3
    velocity: Vector3


class InertialState(WireModel):
    at_utc: Epoch
    frame: Literal["GCRS"]
    position_unit: Literal["km"]
    velocity_unit: Literal["km/s"]
    state: CartesianState


class RenderStates(WireModel):
    at_utc: Epoch
    frame: Literal["ITRS"]
    position_unit: Literal["m"]
    velocity_unit: Literal["m/s"]
    states: list[CartesianState]
    provenance: Provenance


class Participant(WireModel):
    object_id: str
    assumed_mass_kg: Annotated[float, Field(gt=0)] | None = None
    assumed_radius_m: Annotated[float, Field(gt=0)] | None = None


class ForcedContact(WireModel):
    move_participant_index: Literal[0, 1]
    impact_geometry: Literal["CENTERED"]


class SimulationSettings(WireModel):
    seed: Annotated[int, Field(ge=0, le=4_294_967_295)] = 42
    duration_hours: Annotated[float, Field(gt=0, le=24)] = 24
    output_step_seconds: Annotated[int, Field(ge=1, le=3600)] = 60
    max_resolved_fragments: Annotated[int, Field(ge=1, le=1500)] = 600
    max_cascade_generations: Literal[0] = 0


class ScenarioRequest(WireModel):
    schema_version: Literal["1.0"]
    type: Literal["FORCED_HYPOTHETICAL"]
    epoch_utc: Epoch
    participants: tuple[Participant, Participant]
    forced_contact: ForcedContact
    simulation: SimulationSettings
    requested_products: Annotated[list[Product], Field(min_length=1, max_length=4)]

    @model_validator(mode="after")
    def distinct_participants(self) -> Self:
        first, second = self.participants
        if first.object_id == second.object_id:
            raise ValueError("participants must be distinct")
        return self


class JobFailure(WireModel):
    code: str
    message: str


class Job(WireModel):
    job_id: str
    scenario_id: str
    seed: int
    state: Literal["queued", "running", "completed", "failed", "cancelled"]
    progress: Annotated[float, Field(ge=0, le=1)] | None
    error: JobFailure | None


class FramePosition(WireModel):
    object_id: str
    position: Vector3


class FrameSample(WireModel):
    at_utc: Epoch
    positions: list[FramePosition]


class FramePage(WireModel):
    schema_version: Literal["1.0"]
    generated_at_utc: Epoch
    scenario_id: str
    frame: Literal["ITRS"]
    position_unit: Literal["m"]
    sample_step_seconds: Annotated[int, Field(gt=0)]
    samples: Annotated[list[FrameSample], Field(max_length=120)]
    next_cursor: str | None
    provenance: Provenance

    @model_validator(mode="after")
    def cap_positions(self) -> Self:
        if sum(len(sample.positions) for sample in self.samples) > 50_000:
            raise ValueError("frame page exceeds 50,000 positions")
        return self


class ForcedModification(WireModel):
    original_state: InertialState
    modified_state: InertialState
    original_separation_km: Annotated[float, Field(ge=0)]


class OccupancyBin(WireModel):
    altitude_min_km: float
    altitude_max_km: float
    resolved_count: Annotated[int, Field(ge=0)]


class CloseApproach(WireModel):
    catalog_object_id: str
    fragment_id: str
    at_utc: Epoch
    separation_km: Annotated[float, Field(ge=0)]


class EntryCrossing(WireModel):
    fragment_id: str
    at_utc: Epoch
    threshold_altitude_km: float
    latitude_deg: Annotated[float, Field(ge=-90, le=90)]
    longitude_deg: Annotated[float, Field(ge=-180, le=180)]


class ScenarioResult(WireModel):
    schema_version: Literal["1.0"]
    generated_at_utc: Epoch
    scenario_id: str
    resolved_fragment_count: Annotated[int, Field(ge=0, le=1500)]
    unresolved_mass_kg: Annotated[float, Field(ge=0)] | None
    contact_approach_itrs_m: tuple[FramePosition, FramePosition] | None = None
    modification: ForcedModification | None
    occupancy: list[OccupancyBin]
    encounters: list[CloseApproach]
    entry_crossings: list[EntryCrossing]
    provenance: Provenance


class DemoBundle(WireModel):
    schema_version: Literal["1.0"]
    catalog: CatalogStatus
    objects: list[CatalogObject]
    states: RenderStates
    scenario: ScenarioRequest
    job: Job
    frames: FramePage
    result: ScenarioResult

    @model_validator(mode="after")
    def validate_demo_references(self) -> Self:
        object_ids = {obj.id for obj in self.objects}
        states = self.states.states
        if (
            self.catalog.mode != "DEMO"
            or len(object_ids) != len(self.objects)
            or len(self.objects) != self.catalog.records
            or len(states) != self.catalog.displayable_count
            or len({state.object_id for state in states}) != len(states)
        ):
            raise ValueError("demo catalog counts or identifiers are inconsistent")
        if any(state.object_id not in object_ids for state in states) or any(
            p.object_id not in object_ids for p in self.scenario.participants
        ):
            raise ValueError("demo references an unknown object")
        snapshot = self.catalog.catalog_snapshot_id
        evidence = (self.states.provenance, self.frames.provenance, self.result.provenance)
        if any(obj.catalog_snapshot_id != snapshot for obj in self.objects) or any(
            item.kind != "SYNTHETIC_DEMO"
            or item.mode != "DEMO"
            or item.catalog_snapshot_id != snapshot
            for item in evidence
        ):
            raise ValueError("demo evidence must identify the same synthetic snapshot")
        if (
            self.job.scenario_id != self.frames.scenario_id
            or self.job.scenario_id != self.result.scenario_id
        ):
            raise ValueError("demo scenario identifiers do not match")
        return self


class SatcatMetadata(WireModel):
    norad_cat_id: str
    object_type_raw: str | None = None
    operational_status_code: str | None = None
    launch_date: str | None = None
    decay_date: str | None = None
    rcs_m2: float | None = None
    owner: str | None = None
    note: str = "RCS is radar cross-section, not a measured physical radius or mass."


class ObjectSearchPage(WireModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at_utc: Epoch
    items: list[CatalogObject]
    next_cursor: str | None
    total: Annotated[int, Field(ge=0)]
    catalog_snapshot_id: SnapshotId
    provenance: Provenance


class ObjectDetail(WireModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at_utc: Epoch
    object: CatalogObject
    satcat: SatcatMetadata | None = None
    staleness_hours: Annotated[float, Field(ge=0)] | None = None
    is_stale: bool
    provenance: Provenance


class CatalogRefreshResult(WireModel):
    status: CatalogStatus
    refreshed: bool
    message: str
