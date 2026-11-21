"""Seeded, approximate representative breakup with explicit physical budgets."""

from dataclasses import dataclass

import numpy as np

from .collision import FloatArray, Impact

RESOLVED_MASS_FRACTION = 0.6
ENERGY_FRACTION = 0.15
MAX_IMPULSE_KM_S = 0.5
MIN_LENGTH_M = 0.01
LENGTH_EXPONENT = 1.6


@dataclass(frozen=True)
class FragmentCloud:
    lengths_m: FloatArray
    masses_kg: FloatArray
    velocities_km_s: FloatArray
    unresolved_mass_kg: float
    energy_budget_j: float


def fragment(event: Impact, seed: int, count: int, maximum_length_m: float) -> FragmentCloud:
    if count < 1 or count > 1500:
        raise ValueError("Resolve between 1 and 1500 fragments.")
    rng = np.random.default_rng(seed)
    maximum_length_m = max(MIN_LENGTH_M, maximum_length_m)
    upper_tail = (MIN_LENGTH_M / maximum_length_m) ** LENGTH_EXPONENT
    lengths = MIN_LENGTH_M * (1 - rng.random(count) * (1 - upper_tail)) ** (-1 / LENGTH_EXPONENT)
    weights = lengths**3
    masses = event.total_mass_kg * RESOLVED_MASS_FRACTION * weights / weights.sum()
    offsets = np.zeros((count, 3))
    budget = event.energy_j * ENERGY_FRACTION
    if count > 1 and budget > 0:
        # Smaller pieces can receive larger impulses. Remove bulk drift before applying caps.
        offsets = rng.normal(size=(count, 3)) / np.sqrt(lengths[:, None] / MIN_LENGTH_M)
        offsets -= np.average(offsets, weights=masses, axis=0)
        peak = float(np.linalg.norm(offsets, axis=1).max())
        energy = 0.5e6 * float(np.sum(masses[:, None] * offsets**2))
        if peak > 0 and energy > 0:
            offsets *= min(MAX_IMPULSE_KM_S / peak, np.sqrt(budget / energy))
    return FragmentCloud(
        lengths_m=lengths,
        masses_kg=masses,
        velocities_km_s=event.com_velocity_km_s + offsets,
        unresolved_mass_kg=event.total_mass_kg - float(masses.sum()),
        energy_budget_j=budget,
    )
