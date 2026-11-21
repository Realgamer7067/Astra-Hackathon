"""Construct a forced contact from explicitly inertial, simultaneous states."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from ..models.wire import ForcedModification, InertialState, Vector3

FloatArray = NDArray[np.float64]


def vector_tuple(vector: FloatArray) -> Vector3:
    return float(vector[0]), float(vector[1]), float(vector[2])


@dataclass(frozen=True)
class Impact:
    modification: ForcedModification
    contact_km: FloatArray
    com_velocity_km_s: FloatArray
    total_mass_kg: float
    relative_speed_km_s: float
    energy_j: float


def compute_impact(
    states: tuple[InertialState, InertialState],
    masses_kg: tuple[float, float],
    move_index: Literal[0, 1],
) -> Impact:
    first, second = states
    if first.at_utc != second.at_utc or first.state.object_id == second.state.object_id:
        raise ValueError("Impact requires two distinct objects at the same epoch.")
    masses = np.asarray(masses_kg, dtype=np.float64)
    if not np.isfinite(masses).all() or np.any(masses <= 0):
        raise ValueError("Participant masses must be positive and finite.")
    a = np.asarray(first.state.position, dtype=np.float64)
    b = np.asarray(second.state.position, dtype=np.float64)
    v1 = np.asarray(first.state.velocity, dtype=np.float64)
    v2 = np.asarray(second.state.velocity, dtype=np.float64)
    total = float(masses.sum())
    first_fraction = float(masses[0]) / total
    com = v1 * first_fraction + v2 * (1 - first_fraction)
    speed = float(np.linalg.norm(v1 - v2))
    reduced_mass = first_fraction * float(masses[1])
    original = states[move_index]
    contact = states[1 - move_index].state.position
    modified = original.model_copy(
        update={"state": original.state.model_copy(update={"position": contact})}
    )
    return Impact(
        modification=ForcedModification(
            original_state=original,
            modified_state=modified,
            original_separation_km=float(np.linalg.norm(a - b)),
        ),
        contact_km=np.asarray(contact, dtype=np.float64),
        com_velocity_km_s=com,
        total_mass_kg=total,
        relative_speed_km_s=speed,
        energy_j=0.5 * reduced_mass * (speed * 1000) ** 2,
    )
