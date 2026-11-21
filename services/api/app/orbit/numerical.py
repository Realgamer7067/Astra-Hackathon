"""Vectorized Earth gravity integration and terminal atmosphere-threshold detection."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from ..physics.collision import FloatArray

EARTH_MU = 398600.4418  # km³/s²
EARTH_RADIUS = 6378.137  # km
EARTH_J2 = 1.08262668e-3
ENTRY_ALTITUDE_KM = 120.0
ENTRY_RADIUS = EARTH_RADIUS + ENTRY_ALTITUDE_KM
MAX_STEP_S = 15.0


@dataclass(frozen=True)
class Crossing:
    fragment_index: int
    elapsed_s: float
    position_km: FloatArray


@dataclass(frozen=True)
class Trajectory:
    seconds: FloatArray
    positions_km: FloatArray
    final_velocities_km_s: FloatArray
    crossings: tuple[Crossing, ...]


def acceleration(positions: FloatArray, axis: FloatArray, j2: float) -> FloatArray:
    radius_sq = np.sum(positions**2, axis=1, keepdims=True)
    base = -EARTH_MU * positions / radius_sq**1.5
    if j2 == 0:
        return base
    axial = (positions @ axis)[:, None]
    factor = 1.5 * j2 * EARTH_MU * EARTH_RADIUS**2 / radius_sq**2.5
    return base + factor * (positions * (5 * axial**2 / radius_sq - 1) - 2 * axial * axis)


def rk4(
    position: FloatArray, velocity: FloatArray, step: float, axis: FloatArray, j2: float
) -> tuple[FloatArray, FloatArray]:
    p1, v1 = velocity, acceleration(position, axis, j2)
    p2 = velocity + step / 2 * v1
    v2 = acceleration(position + step / 2 * p1, axis, j2)
    p3 = velocity + step / 2 * v2
    v3 = acceleration(position + step / 2 * p2, axis, j2)
    p4 = velocity + step * v3
    v4 = acceleration(position + step * p3, axis, j2)
    return (
        position + step / 6 * (p1 + 2 * p2 + 2 * p3 + p4),
        velocity + step / 6 * (v1 + 2 * v2 + 2 * v3 + v4),
    )


def entry_fraction(start: FloatArray, end: FloatArray) -> float:
    # The RK4 step brackets the crossing. Interpolate only within that short chord.
    lo, hi = 0.0, 1.0
    delta = end - start
    for _ in range(32):
        mid = (lo + hi) / 2
        if np.linalg.norm(start + mid * delta) > ENTRY_RADIUS:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def propagate(
    initial_positions: FloatArray,
    initial_velocities: FloatArray,
    *,
    duration_s: float,
    sample_step_s: int,
    axis: FloatArray,
    j2: float = EARTH_J2,
    checkpoint: Callable[[float], None] | None = None,
) -> Trajectory:
    if np.any(np.linalg.norm(initial_positions, axis=1) <= ENTRY_RADIUS):
        raise ValueError("The encounter must begin above the entry threshold.")
    times = np.append(np.arange(0.0, duration_s, sample_step_s), duration_s)
    samples = np.full((len(times), len(initial_positions), 3), np.nan)
    position, velocity = initial_positions.copy(), initial_velocities.copy()
    active = np.ones(len(position), dtype=bool)
    crossings: list[Crossing] = []
    now = 0.0
    samples[0] = position
    for i, target in enumerate(times[1:], start=1):
        while now < target and np.any(active):
            if checkpoint is not None:
                checkpoint(now / duration_s)
            step = min(MAX_STEP_S, float(target) - now)
            indices = np.flatnonzero(active)
            before = position[indices]
            after, next_velocity = rk4(before, velocity[indices], step, axis, j2)
            if not np.isfinite(after).all() or not np.isfinite(next_velocity).all():
                raise ArithmeticError("Numerical propagation did not produce finite states.")
            entered = np.flatnonzero(np.linalg.norm(after, axis=1) <= ENTRY_RADIUS)
            for local_index in entered:
                original_index = int(indices[local_index])
                fraction = entry_fraction(before[local_index], after[local_index])
                crossings.append(
                    Crossing(
                        original_index,
                        now + step * fraction,
                        before[local_index] + fraction * (after[local_index] - before[local_index]),
                    )
                )
                active[original_index] = False
            position[indices], velocity[indices] = after, next_velocity
            now += step
        samples[i, active] = position[active]
        if not np.any(active):
            break
    if checkpoint is not None:
        checkpoint(1)
    return Trajectory(times, samples, velocity, tuple(crossings))
