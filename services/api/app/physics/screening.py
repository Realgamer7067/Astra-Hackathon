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


def _minimum_distance_interval(
    a_start: StateVector,
    a_end: StateVector,
    b_start: StateVector,
    b_end: StateVector,
) -> tuple[float, float]:
    """Compute the minimum Euclidean separation between two objects over [t_start, t_end].

    Uses linear relative motion approximation between the interval endpoints:
      r_rel(u) = r0 + u * dr
    where u in [0, 1].

    Returns (min_separation_km, min_epoch_s).
    """
    dt = a_end.epoch_s - a_start.epoch_s
    if dt <= 0:
        sep = _separation_km(a_start, b_start)
        return sep, a_start.epoch_s

    rx0 = a_start.x - b_start.x
    ry0 = a_start.y - b_start.y
    rz0 = a_start.z - b_start.z

    rx1 = a_end.x - b_end.x
    ry1 = a_end.y - b_end.y
    rz1 = a_end.z - b_end.z

    drx = rx1 - rx0
    dry = ry1 - ry0
    drz = rz1 - rz0

    dr_sq = drx * drx + dry * dry + drz * drz

    if dr_sq < 1e-12:
        sep = math.sqrt(rx0 * rx0 + ry0 * ry0 + rz0 * rz0)
        return sep, a_start.epoch_s

    u_star = -(rx0 * drx + ry0 * dry + rz0 * drz) / dr_sq
    u_clamped = max(0.0, min(1.0, u_star))

    rx_min = rx0 + u_clamped * drx
    ry_min = ry0 + u_clamped * dry
    rz_min = rz0 + u_clamped * drz

    min_sep = math.sqrt(rx_min * rx_min + ry_min * ry_min + rz_min * rz_min)
    min_epoch = a_start.epoch_s + u_clamped * dt
    return min_sep, min_epoch


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
    """Bounded broad-phase + relative-motion refinement screening.

    1. Group objects by ID into time series and identify common sample epochs.
    2. Over discrete sample epochs, bucket objects into altitude shells to prune
       distant pairs.
    3. Across matching intervals [t_k, t_{k+1}], perform linear relative-motion
       refinement to locate the interior minimum distance.
    4. Screen candidates within ``limits.refine_threshold_km``.
    5. Return up to ``limits.max_encounters`` closest encounters sorted ascending
       by minimum separation.

    Near misses are reported with their actual refined separation and are
    **never** promoted to geometric contacts unless the caller applies an
    explicit hard-body radius check.
    """
    if limits is None:
        limits = ScreeningLimits()

    result = ScreeningResult(limits=limits)

    # Index by object_id -> epoch_s -> StateVector
    frags_by_id_epoch: dict[str, dict[float, StateVector]] = {}
    for sv in fragment_samples:
        frags_by_id_epoch.setdefault(sv.object_id, {})[sv.epoch_s] = sv

    cands_by_id_epoch: dict[str, dict[float, StateVector]] = {}
    for sv in candidate_states:
        cands_by_id_epoch.setdefault(sv.object_id, {})[sv.epoch_s] = sv

    # Group by epoch for broad-phase altitude filtering
    frag_by_epoch: dict[float, list[StateVector]] = {}
    for sv in fragment_samples:
        frag_by_epoch.setdefault(sv.epoch_s, []).append(sv)

    cand_by_epoch: dict[float, list[StateVector]] = {}
    for sv in candidate_states:
        cand_by_epoch.setdefault(sv.epoch_s, []).append(sv)

    sorted_epochs = sorted(set(frag_by_epoch) & set(cand_by_epoch))
    if not sorted_epochs:
        return result

    # Identify candidate pairs that are close enough at any sample epoch
    # or whose interval bounding could bring them close
    candidate_pairs: set[tuple[str, str]] = set()

    for epoch in sorted_epochs:
        frags = frag_by_epoch[epoch]
        cands = cand_by_epoch[epoch]

        frag_index = _build_shell_index(frags, limits.broad_phase_bin_km)
        cand_index = _build_shell_index(cands, limits.broad_phase_bin_km)

        for shell_key, shell_frags in frag_index.items():
            for offset in (-1, 0, 1):
                neighbor_cands = cand_index.get(shell_key + offset, [])
                for frag in shell_frags:
                    for cand in neighbor_cands:
                        candidate_pairs.add((frag.object_id, cand.object_id))

    all_encounters: list[ScreenedEncounter] = []

    # For each candidate pair, refine across all common intervals and single points
    for frag_id, cand_id in candidate_pairs:
        f_epochs = frags_by_id_epoch[frag_id]
        c_epochs = cands_by_id_epoch[cand_id]
        pair_common_epochs = sorted(set(f_epochs) & set(c_epochs))

        if len(pair_common_epochs) == 1:
            ep = pair_common_epochs[0]
            result.screened_pair_count += 1
            if result.screened_pair_count > limits.max_candidate_pairs:
                result.truncated = True
                break
            sep = _separation_km(f_epochs[ep], c_epochs[ep])
            if sep <= limits.refine_threshold_km:
                result.refined_pair_count += 1
                all_encounters.append(
                    ScreenedEncounter(
                        catalog_object_id=cand_id,
                        fragment_id=frag_id,
                        epoch_s=ep,
                        separation_km=sep,
                    )
                )
            continue

        # Intervals between consecutive matching epochs
        best_pair_sep = float("inf")
        best_pair_epoch = pair_common_epochs[0]

        for i in range(len(pair_common_epochs) - 1):
            t0 = pair_common_epochs[i]
            t1 = pair_common_epochs[i + 1]

            result.screened_pair_count += 1
            if result.screened_pair_count > limits.max_candidate_pairs:
                result.truncated = True
                break

            min_sep, min_ep = _minimum_distance_interval(
                f_epochs[t0], f_epochs[t1], c_epochs[t0], c_epochs[t1]
            )
            if min_sep < best_pair_sep:
                best_pair_sep = min_sep
                best_pair_epoch = min_ep

        if best_pair_sep <= limits.refine_threshold_km:
            result.refined_pair_count += 1
            all_encounters.append(
                ScreenedEncounter(
                    catalog_object_id=cand_id,
                    fragment_id=frag_id,
                    epoch_s=best_pair_epoch,
                    separation_km=best_pair_sep,
                )
            )

        if result.truncated:
            break

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

    Includes interval refinement across all matching consecutive epochs.
    Returns encounters within ``threshold_km``.
    """
    frags_by_id_epoch: dict[str, dict[float, StateVector]] = {}
    for sv in fragment_samples:
        frags_by_id_epoch.setdefault(sv.object_id, {})[sv.epoch_s] = sv

    cands_by_id_epoch: dict[str, dict[float, StateVector]] = {}
    for sv in candidate_states:
        cands_by_id_epoch.setdefault(sv.object_id, {})[sv.epoch_s] = sv

    encounters: list[ScreenedEncounter] = []

    for frag_id, f_epochs in frags_by_id_epoch.items():
        for cand_id, c_epochs in cands_by_id_epoch.items():
            common_epochs = sorted(set(f_epochs) & set(c_epochs))
            if not common_epochs:
                continue

            if len(common_epochs) == 1:
                ep = common_epochs[0]
                sep = _separation_km(f_epochs[ep], c_epochs[ep])
                if sep <= threshold_km:
                    encounters.append(
                        ScreenedEncounter(
                            catalog_object_id=cand_id,
                            fragment_id=frag_id,
                            epoch_s=ep,
                            separation_km=sep,
                        )
                    )
                continue

            best_sep = float("inf")
            best_ep = common_epochs[0]
            for i in range(len(common_epochs) - 1):
                t0 = common_epochs[i]
                t1 = common_epochs[i + 1]
                min_sep, min_ep = _minimum_distance_interval(
                    f_epochs[t0], f_epochs[t1], c_epochs[t0], c_epochs[t1]
                )
                if min_sep < best_sep:
                    best_sep = min_sep
                    best_ep = min_ep

            if best_sep <= threshold_km:
                encounters.append(
                    ScreenedEncounter(
                        catalog_object_id=cand_id,
                        fragment_id=frag_id,
                        epoch_s=best_ep,
                        separation_km=best_sep,
                    )
                )

    encounters.sort(key=lambda e: e.separation_km)
    return encounters
