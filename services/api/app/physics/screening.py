"""Broad-phase and refined encounter screening.

Implements bounded fragment–catalog-object screening that avoids
O(N_catalog × N_fragments × N_timesteps) brute-force sweeps in the
hot path while producing results cross-checkable against a full
brute-force reference.

All distances are in km (GCRS inertial frame).  Near misses are
never promoted to contacts based solely on coarse spatial bins.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StateVector:
    """Inertial Cartesian state at a single epoch (km, km/s)."""

    object_id: str
    epoch_s: float  # seconds since scenario epoch
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float

    @property
    def r_mag(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)


@dataclass(frozen=True, slots=True)
class ScreenedEncounter:
    """A refined close-approach record between a fragment and a catalog object."""

    catalog_object_id: str
    fragment_id: str
    epoch_s: float
    separation_km: float


@dataclass(frozen=True, slots=True)
class ScreeningLimits:
    """Configurable caps for the screening engine."""

    broad_phase_bin_km: float = 200.0  # spatial bin edge length
    refine_threshold_km: float = 100.0  # max distance to refine
    max_encounters: int = 500  # hard cap on output rows
    max_candidate_pairs: int = 50_000  # pairs entering refinement


@dataclass
class ScreeningResult:
    """Container returned by the screening functions."""

    encounters: list[ScreenedEncounter] = field(default_factory=list)
    screened_pair_count: int = 0
    refined_pair_count: int = 0
    truncated: bool = False
    limits: ScreeningLimits = field(default_factory=ScreeningLimits)


# ---------------------------------------------------------------------------
# Distance helpers
# ---------------------------------------------------------------------------


def _separation_km(a: StateVector, b: StateVector) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    dz = a.z - b.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


# ---------------------------------------------------------------------------
# Broad-phase: altitude-shell bucketing
# ---------------------------------------------------------------------------


def _altitude_km(sv: StateVector, r_earth_km: float = 6378.137) -> float:
    return sv.r_mag - r_earth_km


def _build_shell_index(
    states: Sequence[StateVector],
    bin_km: float,
) -> dict[int, list[StateVector]]:
    """Bucket states by altitude shell for fast broad-phase rejection."""
    index: dict[int, list[StateVector]] = {}
    for sv in states:
        alt = _altitude_km(sv)
        bucket = int(alt // bin_km)
        index.setdefault(bucket, []).append(sv)
    return index


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def screen_encounters(
    fragment_samples: Sequence[StateVector],
    candidate_states: Sequence[StateVector],
    limits: ScreeningLimits | None = None,
) -> ScreeningResult:
    """Bounded broad-phase + refinement screening.

    1. Bucket fragments and candidates into altitude shells.
    2. Pair only objects sharing the same or adjacent shells (broad phase).
    3. Refine candidates within ``limits.refine_threshold_km`` with exact
       Euclidean separation.
    4. Return up to ``limits.max_encounters`` closest encounters, sorted
       ascending by separation.

    Near misses are reported with their actual refined separation and are
    **never** promoted to geometric contacts unless the caller applies an
    explicit hard-body radius check.
    """
    if limits is None:
        limits = ScreeningLimits()

    result = ScreeningResult(limits=limits)

    # Group by epoch for temporal co-location
    frag_by_epoch: dict[float, list[StateVector]] = {}
    for sv in fragment_samples:
        frag_by_epoch.setdefault(sv.epoch_s, []).append(sv)

    cand_by_epoch: dict[float, list[StateVector]] = {}
    for sv in candidate_states:
        cand_by_epoch.setdefault(sv.epoch_s, []).append(sv)

    common_epochs = sorted(set(frag_by_epoch) & set(cand_by_epoch))

    all_encounters: list[ScreenedEncounter] = []

    for epoch in common_epochs:
        frags = frag_by_epoch[epoch]
        cands = cand_by_epoch[epoch]

        # Broad phase: altitude shell index
        frag_index = _build_shell_index(frags, limits.broad_phase_bin_km)
        cand_index = _build_shell_index(cands, limits.broad_phase_bin_km)

        for shell_key, shell_frags in frag_index.items():
            # Check same shell and adjacent shells
            for offset in (-1, 0, 1):
                neighbor_cands = cand_index.get(shell_key + offset, [])
                for frag in shell_frags:
                    for cand in neighbor_cands:
                        result.screened_pair_count += 1
                        if result.screened_pair_count > limits.max_candidate_pairs:
                            result.truncated = True
                            break

                        # Refinement: exact separation
                        sep = _separation_km(frag, cand)
                        if sep <= limits.refine_threshold_km:
                            result.refined_pair_count += 1
                            all_encounters.append(
                                ScreenedEncounter(
                                    catalog_object_id=cand.object_id,
                                    fragment_id=frag.object_id,
                                    epoch_s=epoch,
                                    separation_km=sep,
                                )
                            )
                    if result.truncated:
                        break
                if result.truncated:
                    break
            if result.truncated:
                break
        if result.truncated:
            break

    # Sort and cap
    all_encounters.sort(key=lambda e: e.separation_km)
    if len(all_encounters) > limits.max_encounters:
        result.truncated = True
        all_encounters = all_encounters[: limits.max_encounters]

    result.encounters = all_encounters
    return result


def brute_force_screen(
    fragment_samples: Sequence[StateVector],
    candidate_states: Sequence[StateVector],
    threshold_km: float = 100.0,
) -> list[ScreenedEncounter]:
    """Reference brute-force O(F×C) screening for cross-checking.

    Returns **all** encounters within ``threshold_km`` without any
    spatial-index acceleration.  Used in tests to validate the bounded
    broad-phase implementation.
    """
    frag_by_epoch: dict[float, list[StateVector]] = {}
    for sv in fragment_samples:
        frag_by_epoch.setdefault(sv.epoch_s, []).append(sv)

    cand_by_epoch: dict[float, list[StateVector]] = {}
    for sv in candidate_states:
        cand_by_epoch.setdefault(sv.epoch_s, []).append(sv)

    common_epochs = sorted(set(frag_by_epoch) & set(cand_by_epoch))

    encounters: list[ScreenedEncounter] = []
    for epoch in common_epochs:
        for frag in frag_by_epoch[epoch]:
            for cand in cand_by_epoch[epoch]:
                sep = _separation_km(frag, cand)
                if sep <= threshold_km:
                    encounters.append(
                        ScreenedEncounter(
                            catalog_object_id=cand.object_id,
                            fragment_id=frag.object_id,
                            epoch_s=epoch,
                            separation_km=sep,
                        )
                    )

    encounters.sort(key=lambda e: e.separation_km)
    return encounters
