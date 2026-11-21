"""Wire extensions for the collision lane's run creation and physics handoff."""

from typing import Annotated, Literal

from pydantic import Field

from .wire import ScenarioResult, SnapshotId, WireModel


class ScenarioCreated(WireModel):
    scenario_id: str
    scenario_type: Literal["FORCED_HYPOTHETICAL"]
    catalog_snapshot_id: SnapshotId
    assumptions: list[str]


class SimulationSummary(ScenarioResult):
    scenario_type: Literal["FORCED_HYPOTHETICAL"]
    seed: int
    relative_speed_km_s: Annotated[float, Field(ge=0)]
    impact_energy_j: Annotated[float, Field(ge=0)]
    resolved_mass_kg: Annotated[float, Field(gt=0)]
    fragment_energy_budget_j: Annotated[float, Field(ge=0)]
