"""Tests for CelesTrak OMM CSV and SATCAT parsing, policy, and failure modes."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
from app.connectors.celestrak import (
    CelesTrakConnector,
    CelesTrakError,
    map_operational_status,
    parse_omm_csv,
    validate_celestrak_url,
)

SAMPLE_OMM_CSV = """OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT
ISS (ZARYA),1998-067A,2026-11-21T12:00:00.000000,15.49560532,0.0006703,51.6416,247.4627,130.5360,325.0288,0,U,25544,999,48210,0.0001027,0.00016717,0
SIX-DIGIT SAT,2024-010A,2026-11-21T10:00:00.000000,14.80000000,0.0012000,97.5000,120.0000,90.0000,180.0000,0,U,123456,999,1200,0.00005,0.00001,0
NINE-DIGIT ANALYST,2025-999Z,2026-11-21T08:00:00.000000,14.20000000,0.0020000,53.0000,10.0000,20.0000,30.0000,0,U,990000123,999,10,0.00001,0.0,0
DECAYED DEB,1999-025A,2026-11-20T00:00:00.000000,16.10000000,0.0050000,98.0000,15.0000,45.0000,90.0000,0,U,654321,999,50000,0.001,0.001,0
"""

SAMPLE_SATCAT_CSV = """OBJECT_NAME,NORAD_CAT_ID,OBJECT_TYPE,OPS_STATUS_CODE,OWNER,LAUNCH_DATE,DECAY_DATE,RCS
ISS (ZARYA),25544,PAY,+,ISS,1998-11-20,,402.5
SIX-DIGIT SAT,123456,PAY,?,US,2024-01-15,,1.2
NINE-DIGIT ANALYST,990000123,DEB,,UNK,2025-01-01,,
DECAYED DEB,654321,DEB,-,PRC,1999-05-10,2026-11-20,0.05
"""


def test_six_and_nine_digit_norad_ids_preserved() -> None:
    records, warnings = parse_omm_csv(SAMPLE_OMM_CSV, "TEST")
    assert not warnings
    ids = [r.norad_cat_id for r in records]
    assert ids == ["25544", "123456", "990000123", "654321"]


def test_empty_and_malformed_csv_rejected() -> None:
    with pytest.raises(CelesTrakError, match="Empty OMM CSV"):
        parse_omm_csv("   \n  ", "ACTIVE")

    with pytest.raises(CelesTrakError, match="missing"):
        parse_omm_csv("OBJECT_NAME,NORAD_CAT_ID\nFOO,25544\n", "ACTIVE")


def test_unknown_operational_status_never_marked_active() -> None:
    assert map_operational_status("?") == "UNKNOWN"
    assert map_operational_status("") == "UNKNOWN"
    assert map_operational_status(None) == "UNKNOWN"
    assert map_operational_status("+") == "ACTIVE"
    assert map_operational_status("-") == "INACTIVE"


def test_connector_deduplicates_filters_decayed_and_avoids_retry_hammering() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if "GROUP=ACTIVE" in str(request.url):
            return httpx.Response(200, text=SAMPLE_OMM_CSV)
        if "GROUP=STATIONS" in str(request.url):
            # Duplicate 25544 with newer epoch -> should trigger DUPLICATE_EPOCH_CONFLICT
            newer_iss = SAMPLE_OMM_CSV.replace("2026-11-21T12:00:00", "2026-11-21T14:00:00")
            return httpx.Response(200, text=newer_iss)
        if "satcat.csv" in str(request.url):
            return httpx.Response(200, text=SAMPLE_SATCAT_CSV)
        return httpx.Response(404, text="Not Found")

    connector = CelesTrakConnector(
        groups=("ACTIVE", "STATIONS"),
        transport=httpx.MockTransport(handler),
    )
    result = connector.fetch(now_utc=datetime(2026, 11, 21, 15, 0, tzinfo=UTC))
    ids = {r.norad_cat_id: r for r in result.omm_records}
    assert "654321" not in ids
    assert result.decayed_filtered_count == 1
    assert set(ids.keys()) == {"25544", "123456", "990000123"}
    assert ids["25544"].epoch_utc == datetime(2026, 11, 21, 14, 0, tzinfo=UTC)
    assert "DUPLICATE_EPOCH_CONFLICT" in result.warning_codes
    assert "DECAYED_OBJECTS_FILTERED" in result.warning_codes

    # Non-200 response must fail immediately without retry hammering.
    fail_calls = 0

    def fail_handler(_request: httpx.Request) -> httpx.Response:
        nonlocal fail_calls
        fail_calls += 1
        return httpx.Response(503, text="Service Unavailable")

    failing = CelesTrakConnector(
        groups=("ACTIVE",),
        transport=httpx.MockTransport(fail_handler),
    )
    with pytest.raises(CelesTrakError, match="HTTP 503"):
        failing.fetch()
    assert fail_calls == 1


def test_disallowed_provider_host_rejected() -> None:
    with pytest.raises(CelesTrakError, match="Disallowed"):
        validate_celestrak_url("http://celestrak.org/satcat/satcat.csv")
    with pytest.raises(CelesTrakError, match="Disallowed"):
        validate_celestrak_url("https://example.com/gp.csv")
