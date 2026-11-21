"""Tests for SGP4 propagation, TEME->GCRS/ITRS conversions, and km<->m boundaries."""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from app.connectors.celestrak import CelesTrakFetchResult, parse_omm_csv
from app.orbit.frames import teme_to_gcrs, teme_to_itrs
from app.orbit.sgp4_service import propagate_objects
from app.storage.catalog_cache import build_snapshot_from_fetch
from sgp4 import omm
from sgp4.api import Satrec, jday

ISS_OMM_CSV = """OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT
ISS (ZARYA),1998-067A,2026-11-21T12:00:00.000000,15.49560532,0.0006703,51.6416,247.4627,130.5360,325.0288,0,U,25544,999,48210,0.0001027,0.00016717,0
"""


def _norm(vec: tuple[float, float, float]) -> float:
    return math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)


def test_sgp4_propagation_matches_reference_and_preserves_units() -> None:
    records, _ = parse_omm_csv(ISS_OMM_CSV, "STATIONS")
    fetch = CelesTrakFetchResult(
        fetched_at_utc=datetime(2026, 11, 21, 12, 0, tzinfo=UTC),
        sources=["CelesTrak GP (STATIONS)"],
        omm_records=records,
        satcat_by_id={},
    )
    snap = build_snapshot_from_fetch(fetch, mode="LIVE")
    target = datetime(2026, 11, 21, 13, 0, tzinfo=UTC)

    gcrs_batch = propagate_objects(["NORAD:25544"], target, snap, frame="GCRS")
    itrs_batch = propagate_objects(["NORAD:25544"], target, snap, frame="ITRS")

    assert gcrs_batch.position_unit == "km"
    assert gcrs_batch.velocity_unit == "km/s"
    assert itrs_batch.position_unit == "m"
    assert itrs_batch.velocity_unit == "m/s"

    r_gcrs_km = gcrs_batch.states[0].position
    v_gcrs_kms = gcrs_batch.states[0].velocity
    r_itrs_m = itrs_batch.states[0].position

    # LEO ISS-like altitude: radius ~ 6750-6850 km, speed ~ 7.5-7.8 km/s.
    norm_gcrs_km = _norm(r_gcrs_km)
    norm_itrs_km = _norm(r_itrs_m) / 1000.0
    assert 6700.0 < norm_gcrs_km < 6900.0
    assert 7.4 < _norm(v_gcrs_kms) < 7.9
    # Pure rotation preserves position vector norm across TEME->GCRS and TEME->ITRS.
    assert abs(norm_gcrs_km - norm_itrs_km) < 1e-3

    # Cross-check directly against raw sgp4 + Astropy TEME->GCRS.
    sat = Satrec()
    omm.initialize(sat, records[0].to_omm_dict())
    jd, fr = jday(2026, 11, 21, 13, 0, 0.0)
    err, r_teme, v_teme = sat.sgp4(jd, fr)
    assert err == 0
    ref_gcrs_pos, ref_gcrs_vel = teme_to_gcrs(
        (r_teme[0], r_teme[1], r_teme[2]),
        (v_teme[0], v_teme[1], v_teme[2]),
        target,
    )
    assert all(abs(a - b) < 1e-9 for a, b in zip(r_gcrs_km, ref_gcrs_pos, strict=True))
    assert all(abs(a - b) < 1e-9 for a, b in zip(v_gcrs_kms, ref_gcrs_vel, strict=True))


def test_naive_epoch_rejected_in_frame_transforms() -> None:
    naive = datetime(2026, 11, 21, 12, 0, 0)
    with pytest.raises(ValueError, match="UTC"):
        teme_to_itrs((6800.0, 0.0, 0.0), (0.0, 7.6, 0.0), naive)
