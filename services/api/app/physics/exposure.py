"""Exposure intelligence: shell occupancy, ground projections, and entry crossings.

Altitude occupancy bins are derived from fragment state vectors.
Ground projections are computed independently from entry-crossing flags —
ground-track input alone never yields an entry warning.  Entry crossings
are flagged only when a fragment's altitude drops below the configured
threshold (default 120 km).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from .screening import StateVector

# ---------------------------------------------------------------------------
# Constants & Coordinate Transformations
# ---------------------------------------------------------------------------
R_EARTH_KM = 6378.137
ENTRY_THRESHOLD_KM = 120.0  # default atmospheric entry threshold
EARTH_ROTATION_RATE_RAD_S = 7.2921159e-5  # WGS-84 Earth angular velocity (rad/s)
J2000_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)
DEFAULT_SCENARIO_EPOCH_UTC = "2026-11-21T12:00:00Z"


def earth_rotation_angle_rad(
    epoch: datetime | str | None = None,
    epoch_s: float = 0.0,
) -> float:
    """Compute Earth Rotation Angle (ERA) in radians per IAU 2000.

    Theta(Tu) = 2*pi * (0.7790572732640 + 1.00273781191135448 * Tu) mod (2*pi)
    where Tu = JD_UT1 - 2451545.0 (days since J2000.0 12:00:00 UTC).
    """
    if epoch is None:
        epoch = DEFAULT_SCENARIO_EPOCH_UTC
    if isinstance(epoch, str):
        epoch_str = epoch.replace("Z", "+00:00")
        dt = datetime.fromisoformat(epoch_str)
    else:
        dt = epoch

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    if epoch_s != 0.0:
        dt = dt + timedelta(seconds=epoch_s)

    days_since_j2000 = (dt - J2000_EPOCH).total_seconds() / 86400.0
    theta = (2.0 * math.pi * ((0.7790572732640 + 1.00273781191135448 * days_since_j2000) % 1.0)) % (
        2.0 * math.pi
    )
    return theta


def gmst_rad(epoch_s: float, gmst0_rad: float = 0.0) -> float:
    """Greenwich Mean Sidereal Time in radians at epoch_s seconds from scenario epoch."""
    return (gmst0_rad + EARTH_ROTATION_RATE_RAD_S * epoch_s) % (2.0 * math.pi)


def gcrs_to_itrs(
    x_km: float, y_km: float, z_km: float, theta_rad: float
) -> tuple[float, float, float]:
    """Transform inertial GCRS coordinates to Earth-fixed ITRS via Earth rotation angle theta.

    [x_itrs]   [ cos(theta)   sin(theta)  0 ] [x_gcrs]
    [y_itrs] = [-sin(theta)   cos(theta)  0 ] [y_gcrs]
    [z_itrs]   [     0            0       1 ] [z_gcrs]
    """
    cos_t = math.cos(theta_rad)
    sin_t = math.sin(theta_rad)
    x_itrs = cos_t * x_km + sin_t * y_km
    y_itrs = -sin_t * x_km + cos_t * y_km
    z_itrs = z_km
    return x_itrs, y_itrs, z_itrs


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OccupancyBin:
    """Fragment count in an altitude shell."""

    altitude_min_km: float
    altitude_max_km: float
    resolved_count: int


@dataclass(frozen=True, slots=True)
class GroundProjection:
    """Sub-satellite point of a fragment at a given epoch.

    This is a projection only — NOT an impact warning.
    """

    fragment_id: str
    epoch_s: float
    latitude_deg: float
    longitude_deg: float
    altitude_km: float


@dataclass(frozen=True, slots=True)
class EntryCrossing:
    """A fragment crossing the atmospheric entry threshold."""

    fragment_id: str
    epoch_s: float
    threshold_altitude_km: float
    latitude_deg: float
    longitude_deg: float


@dataclass
class ExposureSummary:
    """Aggregated exposure intelligence from a simulation result."""

    occupancy: list[OccupancyBin] = field(default_factory=list)
    ground_projections: list[GroundProjection] = field(default_factory=list)
    entry_crossings: list[EntryCrossing] = field(default_factory=list)
    total_fragments_screened: int = 0
    provenance_notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _altitude_km(sv: StateVector) -> float:
    return sv.r_mag - R_EARTH_KM


def _ecef_to_geodetic(x_km: float, y_km: float, z_km: float) -> tuple[float, float, float]:
    """Approximate ECEF/ITRS → geodetic (lat, lon, alt_km).

    Uses spherical approximation which is acceptable for the
    visualization-grade projections in ASTRA.
    """
    r = math.sqrt(x_km**2 + y_km**2 + z_km**2)
    lat_deg = math.degrees(math.asin(z_km / r)) if r > 0 else 0.0
    lon_deg = math.degrees(math.atan2(y_km, x_km))
    alt_km = r - R_EARTH_KM
    return lat_deg, lon_deg, alt_km


# ---------------------------------------------------------------------------
# Occupancy
# ---------------------------------------------------------------------------


def compute_occupancy(
    fragment_states: Sequence[StateVector],
    bin_size_km: float = 100.0,
    max_altitude_km: float = 2000.0,
) -> list[OccupancyBin]:
    """Compute altitude-shell fragment counts from state vectors.

    Bins are [min, max) intervals of ``bin_size_km`` starting from 0.
    """
    n_bins = math.ceil(max_altitude_km / bin_size_km)
    counts: list[int] = [0] * n_bins

    seen: set[str] = set()
    for sv in fragment_states:
        # Count each fragment only once (use the first epoch encountered)
        if sv.object_id in seen:
            continue
        seen.add(sv.object_id)

        alt = _altitude_km(sv)
        if 0 <= alt < max_altitude_km:
            idx = int(alt // bin_size_km)
            counts[idx] += 1

    bins: list[OccupancyBin] = []
    for i, count in enumerate(counts):
        if count > 0:
            bins.append(
                OccupancyBin(
                    altitude_min_km=i * bin_size_km,
                    altitude_max_km=(i + 1) * bin_size_km,
                    resolved_count=count,
                )
            )
    return bins


# ---------------------------------------------------------------------------
# Ground projections (independent from entry crossings)
# ---------------------------------------------------------------------------


def compute_ground_projections(
    fragment_states: Sequence[StateVector],
    gmst0_rad: float | None = None,
    scenario_epoch_utc: datetime | str | None = None,
    is_inertial: bool = True,
) -> list[GroundProjection]:
    """Compute sub-satellite ground projections for all fragment states.

    If ``is_inertial=True`` (default), states in GCRS are transformed to Earth-fixed
    ITRS coordinates accounting for Earth rotation at each sample's epoch.
    When ``scenario_epoch_utc`` is provided, the IAU 2000 Earth Rotation Angle (ERA)
    is evaluated at the sample's timestamp. If ``gmst0_rad`` is provided, linear
    rotation is used instead.

    These are orbital projections ONLY. They are computed independently
    from entry-crossing flags. A ground projection does NOT imply
    atmospheric entry or surface impact.
    """
    projections: list[GroundProjection] = []
    for sv in fragment_states:
        if is_inertial:
            if scenario_epoch_utc is not None:
                theta = earth_rotation_angle_rad(scenario_epoch_utc, sv.epoch_s)
            elif gmst0_rad is not None:
                theta = gmst_rad(sv.epoch_s, gmst0_rad)
            else:
                theta = earth_rotation_angle_rad(DEFAULT_SCENARIO_EPOCH_UTC, sv.epoch_s)
            x_itrs, y_itrs, z_itrs = gcrs_to_itrs(sv.x, sv.y, sv.z, theta)
        else:
            x_itrs, y_itrs, z_itrs = sv.x, sv.y, sv.z

        lat, lon, alt = _ecef_to_geodetic(x_itrs, y_itrs, z_itrs)
        projections.append(
            GroundProjection(
                fragment_id=sv.object_id,
                epoch_s=sv.epoch_s,
                latitude_deg=lat,
                longitude_deg=lon,
                altitude_km=alt,
            )
        )
    return projections


# ---------------------------------------------------------------------------
# Entry crossings
# ---------------------------------------------------------------------------


def detect_entry_crossings(
    fragment_time_series: dict[str, list[StateVector]],
    threshold_km: float = ENTRY_THRESHOLD_KM,
    gmst0_rad: float | None = None,
    scenario_epoch_utc: datetime | str | None = None,
    is_inertial: bool = True,
) -> list[EntryCrossing]:
    """Detect fragments whose altitude crosses below ``threshold_km``.

    Only the first downward crossing per fragment is recorded.
    Coordinates are transformed to Earth-fixed ITRS at the crossing epoch.
    Entry crossings are determined solely from altitude trajectory,
    NOT from ground projections.
    """
    crossings: list[EntryCrossing] = []
    for frag_id, states in fragment_time_series.items():
        sorted_states = sorted(states, key=lambda s: s.epoch_s)
        prev_alt: float | None = None
        for sv in sorted_states:
            alt = _altitude_km(sv)
            if prev_alt is not None and prev_alt >= threshold_km and alt < threshold_km:
                if is_inertial:
                    if scenario_epoch_utc is not None:
                        theta = earth_rotation_angle_rad(scenario_epoch_utc, sv.epoch_s)
                    elif gmst0_rad is not None:
                        theta = gmst_rad(sv.epoch_s, gmst0_rad)
                    else:
                        theta = earth_rotation_angle_rad(DEFAULT_SCENARIO_EPOCH_UTC, sv.epoch_s)
                    x_itrs, y_itrs, z_itrs = gcrs_to_itrs(sv.x, sv.y, sv.z, theta)
                else:
                    x_itrs, y_itrs, z_itrs = sv.x, sv.y, sv.z

                lat, lon, _ = _ecef_to_geodetic(x_itrs, y_itrs, z_itrs)
                crossings.append(
                    EntryCrossing(
                        fragment_id=frag_id,
                        epoch_s=sv.epoch_s,
                        threshold_altitude_km=threshold_km,
                        latitude_deg=lat,
                        longitude_deg=lon,
                    )
                )
                break  # only first crossing per fragment
            prev_alt = alt
    return crossings


# ---------------------------------------------------------------------------
# Top-level summarization
# ---------------------------------------------------------------------------


def summarize_exposure(
    fragment_states: Sequence[StateVector],
    fragment_time_series: dict[str, list[StateVector]] | None = None,
    bin_size_km: float = 100.0,
    entry_threshold_km: float = ENTRY_THRESHOLD_KM,
    gmst0_rad: float | None = None,
    scenario_epoch_utc: datetime | str | None = None,
    is_inertial: bool = True,
    known_entry_crossings: list[EntryCrossing] | None = None,
) -> ExposureSummary:
    """Compute the full exposure summary from fragment simulation data.

    Args:
        fragment_states: Flat list of all fragment state vectors (any epoch).
        fragment_time_series: Per-fragment ordered time series for entry
            crossing detection. If None, entry crossings are skipped unless
            known_entry_crossings is provided.
        bin_size_km: Altitude bin width for occupancy computation.
        entry_threshold_km: Altitude threshold for entry crossing detection.
        gmst0_rad: Initial Greenwich Mean Sidereal Time in radians at epoch_s=0.
        is_inertial: Whether input StateVectors are in inertial GCRS (requiring
            ITRS rotation for geographic projections).
        known_entry_crossings: Direct crossings from the simulation engine to reuse.

    Returns:
        An ``ExposureSummary`` with occupancy, projections, and crossings.
    """
    summary = ExposureSummary()
    unique_frags = {sv.object_id for sv in fragment_states}
    summary.total_fragments_screened = len(unique_frags)

    summary.occupancy = compute_occupancy(fragment_states, bin_size_km)
    summary.ground_projections = compute_ground_projections(
        fragment_states,
        gmst0_rad=gmst0_rad,
        scenario_epoch_utc=scenario_epoch_utc,
        is_inertial=is_inertial,
    )

    if known_entry_crossings is not None:
        summary.entry_crossings = known_entry_crossings
    elif fragment_time_series is not None:
        summary.entry_crossings = detect_entry_crossings(
            fragment_time_series,
            threshold_km=entry_threshold_km,
            gmst0_rad=gmst0_rad,
            scenario_epoch_utc=scenario_epoch_utc,
            is_inertial=is_inertial,
        )

    summary.provenance_notes = [
        f"Occupancy bins: {bin_size_km} km shells",
        f"Entry threshold: {entry_threshold_km} km",
        "Ground projections are orbital sub-satellite points in Earth-fixed ITRS — not impact predictions",
        f"Fragments screened: {summary.total_fragments_screened}",
    ]

    return summary
