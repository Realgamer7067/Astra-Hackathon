"""Tests for persistent catalog cache, LIVE/CACHED/DEMO modes, and catalog routes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from app.connectors.celestrak import CelesTrakConnector
from app.main import create_app
from fastapi.testclient import TestClient

FIXTURE = Path(__file__).resolve().parents[3] / "data/fixtures/demo.json"

OMM_CSV = """OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT
ISS (ZARYA),1998-067A,2026-11-21T12:00:00.000000,15.49560532,0.0006703,51.6416,247.4627,130.5360,325.0288,0,U,25544,999,48210,0.0001027,0.00016717,0
SIX-DIGIT DEBRIS,2024-010B,2026-11-21T10:00:00.000000,14.80000000,0.0012000,97.5000,120.0000,90.0000,180.0000,0,U,123456,999,1200,0.00005,0.00001,0
"""

SATCAT_CSV = """OBJECT_NAME,NORAD_CAT_ID,OBJECT_TYPE,OPS_STATUS_CODE,OWNER,LAUNCH_DATE,DECAY_DATE,RCS
ISS (ZARYA),25544,PAY,+,ISS,1998-11-20,,402.5
SIX-DIGIT DEBRIS,123456,DEB,?,US,2024-01-15,,0.2
"""


def _ok_connector() -> CelesTrakConnector:
    def handler(request: httpx.Request) -> httpx.Response:
        if "satcat.csv" in str(request.url):
            return httpx.Response(200, text=SATCAT_CSV)
        return httpx.Response(200, text=OMM_CSV)

    return CelesTrakConnector(groups=("ACTIVE",), transport=httpx.MockTransport(handler))


def _failing_connector() -> CelesTrakConnector:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Upstream outage")

    return CelesTrakConnector(groups=("ACTIVE",), transport=httpx.MockTransport(handler))


def test_demo_fallback_live_refresh_and_persistent_cached_mode(tmp_path: Path) -> None:
    cache_file = tmp_path / "catalog_cache.json"

    # 1. Absent cache starts in DEMO mode without network.
    with TestClient(
        create_app(FIXTURE, cache_path=cache_file, connector=_failing_connector())
    ) as client:
        status = client.get("/api/v1/catalog/status").json()
        assert status["mode"] == "DEMO"
        assert "SYNTHETIC_ONLY" in status["warning_codes"]

        # Refresh fails -> stays DEMO with PROVIDER_UNAVAILABLE, never fake LIVE.
        refresh = client.post("/api/v1/catalog/refresh").json()
        assert refresh["refreshed"] is False
        assert refresh["status"]["mode"] == "DEMO"
        assert "PROVIDER_UNAVAILABLE" in refresh["status"]["warning_codes"]

    # 2. Successful refresh transitions to LIVE and writes persistent cache.
    with TestClient(
        create_app(FIXTURE, cache_path=cache_file, connector=_ok_connector())
    ) as client:
        refresh = client.post("/api/v1/catalog/refresh").json()
        assert refresh["refreshed"] is True
        assert refresh["status"]["mode"] == "LIVE"
        assert refresh["status"]["records"] == 2
        assert cache_file.exists()

        # Immediate second refresh respects CelesTrak 2-hour policy.
        second = client.post("/api/v1/catalog/refresh").json()
        assert second["refreshed"] is False
        assert "2 hours" in second["message"]

    # 3. Restart with failing network loads persistent cache in CACHED mode.
    with TestClient(
        create_app(FIXTURE, cache_path=cache_file, connector=_failing_connector())
    ) as client:
        status = client.get("/api/v1/catalog/status").json()
        assert status["mode"] == "CACHED"
        assert "CACHED_SNAPSHOT" in status["warning_codes"]
        assert status["records"] == 2

        # Search & pagination
        page1 = client.get("/api/v1/objects?limit=1").json()
        assert len(page1["items"]) == 1
        assert page1["total"] == 2
        assert page1["next_cursor"] is not None

        page2 = client.get(f"/api/v1/objects?limit=1&cursor={page1['next_cursor']}").json()
        assert len(page2["items"]) == 1
        assert page2["next_cursor"] is None

        # Filter by six-digit ID and kind
        filtered = client.get("/api/v1/objects?query=123456&kind=DEBRIS").json()
        assert filtered["total"] == 1
        assert filtered["items"][0]["id"] == "NORAD:123456"
        assert filtered["items"][0]["operational_status"] == "UNKNOWN"

        # Object detail & 404
        detail = client.get("/api/v1/objects/NORAD:25544").json()
        assert detail["object"]["id"] == "NORAD:25544"
        assert detail["satcat"]["rcs_m2"] == 402.5
        assert "not a measured physical radius or mass" in detail["satcat"]["note"]
        assert client.get("/api/v1/objects/NORAD:999999").status_code == 404

        # Invalid cursor returns 422
        assert client.get("/api/v1/objects?cursor=!!!").status_code == 422

        # Propagated ITRS render states in meters
        target_at = (datetime.now(UTC) + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        states = client.get(f"/api/v1/states?at={target_at}&scope=visible").json()
        assert states["frame"] == "ITRS"
        assert states["position_unit"] == "m"
        assert states["velocity_unit"] == "m/s"
        assert len(states["states"]) == 2
        assert states["provenance"]["kind"] == "PROPAGATED_ESTIMATE"
