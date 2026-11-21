"""Validate a fixture-backed scenario and produce inertial fragment trajectories."""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np

from ..models.scenarios import SimulationSummary
from ..models.wire import (
    CartesianState,
    DemoBundle,
    EntryCrossing,
    FramePage,
    FramePosition,
    FrameSample,
    Provenance,
    ScenarioRequest,
)
from ..orbit.numerical import ENTRY_ALTITUDE_KM, Trajectory, propagate
from ..orbit.simulation_frames import earth_axis, entry_coordinates, to_inertial, to_render
from .collision import compute_impact, vector_tuple
from .fragmentation import fragment

MODEL_VERSION = "astra-demo-breakup-rk4-j2-v1"
MAX_STORED_POSITIONS = 1_000_000
MAX_PAGE_POSITIONS = 50_000
MAX_PAGE_EPOCHS = 120


class ScenarioError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PreparedScenario:
    request: ScenarioRequest
    states: tuple[CartesianState, CartesianState]
    masses_kg: tuple[float, float]
    radius_m: tuple[float, float]
    snapshot: str
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class CompletedRun:
    summary: SimulationSummary
    trajectory: Trajectory
    epoch: datetime
    output_step_s: int
    request: ScenarioRequest

    def frame_page(self, indices: Sequence[int], offset: int, step_s: int) -> FramePage:
        count = self.summary.resolved_fragment_count
        capacity = min(MAX_PAGE_EPOCHS, MAX_PAGE_POSITIONS // count)
        page = indices[offset : offset + capacity]
        samples = self.trajectory.positions_km[list(page)]
        sample_epochs = [
            self.epoch + timedelta(seconds=float(self.trajectory.seconds[i])) for i in page
        ]
        frame_rows, fragment_rows = np.where(np.isfinite(samples[:, :, 0]))
        xyz = to_render(samples[frame_rows, fragment_rows], [sample_epochs[i] for i in frame_rows])
        positions: list[list[FramePosition]] = [[] for _ in page]
        for frame_index, fragment_index, vector in zip(frame_rows, fragment_rows, xyz, strict=True):
            positions[frame_index].append(
                FramePosition(
                    object_id=fragment_id(int(fragment_index)), position=vector_tuple(vector)
                )
            )
        return FramePage(
            schema_version="1.0",
            generated_at_utc=self.summary.generated_at_utc,
            scenario_id=self.summary.scenario_id,
            frame="ITRS",
            position_unit="m",
            sample_step_seconds=step_s,
            samples=[
                FrameSample(at_utc=at, positions=row)
                for at, row in zip(sample_epochs, positions, strict=True)
            ],
            next_cursor=str(offset + len(page)) if offset + len(page) < len(indices) else None,
            provenance=self.summary.provenance.model_copy(update={"coordinate_frame": "ITRS"}),
        )

    def frame_indices(self, start: datetime | None, end: datetime | None, step_s: int) -> list[int]:
        if step_s % self.output_step_s:
            raise ScenarioError(
                422, "INVALID_FRAME_STEP", "Frame step must be a multiple of the run's sample step."
            )
        for bound in (start, end):
            if bound is not None and bound.utcoffset() != timedelta(0):
                raise ScenarioError(422, "INVALID_FRAME_EPOCH", "Frame bounds must use UTC.")
        if start is not None and end is not None and end < start:
            raise ScenarioError(422, "INVALID_FRAME_RANGE", "Frame range ends before it starts.")
        return [
            index
            for index in range(0, len(self.trajectory.seconds), step_s // self.output_step_s)
            if (start is None or self.sample_epoch(index) >= start)
            and (end is None or self.sample_epoch(index) <= end)
        ]

    def sample_epoch(self, index: int) -> datetime:
        return self.epoch + timedelta(seconds=float(self.trajectory.seconds[index]))


def fragment_id(index: int) -> str:
    return f"fragment-{index + 1:04d}"


def prepare_scenario(scenario: ScenarioRequest, demo: DemoBundle) -> PreparedScenario:
    if scenario.epoch_utc != demo.states.at_utc:
        raise ScenarioError(
            422, "UNSUPPORTED_EPOCH", "Use the fixed epoch from the synthetic snapshot."
        )
    if any(
        product not in ("TRAJECTORIES", "ENTRY_CROSSINGS")
        for product in scenario.requested_products
    ):
        raise ScenarioError(
            422, "UNAVAILABLE_PRODUCT", "This runner supports trajectories and entry crossings."
        )
    config = scenario.simulation
    sample_count = 1 + math.ceil(config.duration_hours * 3600 / config.output_step_seconds)
    if sample_count * config.max_resolved_fragments > MAX_STORED_POSITIONS:
        raise ScenarioError(
            422,
            "SAMPLE_BUDGET",
            "Reduce the run duration or fragment count, or increase sample spacing.",
        )
    by_id = {state.object_id: state for state in demo.states.states}
    selected: list[CartesianState] = []
    masses: list[float] = []
    radii: list[float] = []
    assumptions = ["Forced hypothetical contact. One position is replaced at the snapshot epoch."]
    for item in scenario.participants:
        state = by_id.get(item.object_id)
        if state is None:
            raise ScenarioError(
                404, "OBJECT_NOT_FOUND", "A participant has no state in the synthetic snapshot."
            )
        mass, radius = item.assumed_mass_kg, item.assumed_radius_m
        if mass is None or radius is None:
            raise ScenarioError(
                422, "ASSUMPTIONS_REQUIRED", "Supply an assumed mass and radius for both objects."
            )
        if not (0.01 <= mass <= 1e7 and 0.01 <= radius <= 500):
            raise ScenarioError(
                422,
                "ASSUMPTIONS_OUT_OF_RANGE",
                "Use mass between 0.01 and 10 million kg and radius between 0.01 and 500 m.",
            )
        selected.append(state)
        masses.append(mass)
        radii.append(radius)
        assumptions.append(f"{item.object_id}: assumed mass {mass:g} kg and radius {radius:g} m.")
    return PreparedScenario(
        scenario,
        (selected[0], selected[1]),
        (masses[0], masses[1]),
        (radii[0], radii[1]),
        demo.catalog.catalog_snapshot_id,
        tuple(assumptions),
    )


def simulate(
    prepared: PreparedScenario, scenario_id: str, checkpoint: Callable[[float], None]
) -> CompletedRun:
    scenario = prepared.request
    config = scenario.simulation
    epoch = scenario.epoch_utc
    checkpoint(0)
    initial = to_inertial(prepared.states, epoch)
    event = compute_impact(
        initial, prepared.masses_kg, scenario.forced_contact.move_participant_index
    )
    cloud = fragment(event, config.seed, config.max_resolved_fragments, 2 * max(prepared.radius_m))
    initial_positions = np.broadcast_to(event.contact_km, cloud.velocities_km_s.shape)
    trajectory = propagate(
        initial_positions,
        cloud.velocities_km_s,
        duration_s=config.duration_hours * 3600,
        sample_step_s=config.output_step_seconds,
        axis=earth_axis(epoch),
        checkpoint=checkpoint,
    )
    crossings: list[EntryCrossing] = []
    if "ENTRY_CROSSINGS" in scenario.requested_products and trajectory.crossings:
        crossing_times = [epoch + timedelta(seconds=x.elapsed_s) for x in trajectory.crossings]
        fixed = to_render(np.stack([x.position_km for x in trajectory.crossings]), crossing_times)
        for crossing, at, (lat, lon) in zip(
            trajectory.crossings, crossing_times, entry_coordinates(fixed), strict=True
        ):
            crossings.append(
                EntryCrossing(
                    fragment_id=fragment_id(crossing.fragment_index),
                    at_utc=at,
                    threshold_altitude_km=ENTRY_ALTITUDE_KM,
                    latitude_deg=lat,
                    longitude_deg=lon,
                )
            )
    evidence = Provenance(
        kind="SYNTHETIC_DEMO",
        mode="DEMO",
        source="ASTRA synthetic fixtures",
        sourceUrl=None,
        sourceFetchedAtUtc=None,
        sourceEpochUtc=epoch,
        catalogSnapshotId=prepared.snapshot,
        modelVersion=MODEL_VERSION,
        coordinateFrame="GCRS",
        isStale=None,
        assumptions=list(prepared.assumptions),
        limitations=[
            "Illustrative fragment population and fixed-epoch J2 axis. Atmospheric drag and cascades are excluded.",
            "Entry events mark an approximate altitude crossing. Ground impact and survival were not modeled.",
            "Exposure and secondary encounters are separate analysis products and are not computed by this runner.",
        ],
    )
    summary = SimulationSummary(
        schema_version="1.0",
        generated_at_utc=datetime.now(UTC),
        scenario_id=scenario_id,
        scenario_type=scenario.type,
        seed=config.seed,
        relative_speed_km_s=event.relative_speed_km_s,
        impact_energy_j=event.energy_j,
        resolved_mass_kg=float(cloud.masses_kg.sum()),
        fragment_energy_budget_j=cloud.energy_budget_j,
        resolved_fragment_count=len(cloud.masses_kg),
        unresolved_mass_kg=cloud.unresolved_mass_kg,
        modification=event.modification,
        occupancy=[],
        encounters=[],
        entry_crossings=crossings,
        provenance=evidence,
    )
    return CompletedRun(summary, trajectory, epoch, config.output_step_seconds, scenario)
