import json
from pathlib import Path

from app.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]


def test_offline_demo_serves_catalog_and_frames() -> None:
    with TestClient(create_app()) as client:
        health = client.get("/health").json()
        assert health["cache_ready"] is True
        assert health["simulation_ready"] is True
        response = client.get("/api/v1/demo")
        assert response.status_code == 200
        demo = response.json()
        assert demo["catalog"]["mode"] == "DEMO"
        assert len(demo["objects"]) == 12
        assert demo["states"]["frame"] == "ITRS"
        assert demo["states"]["position_unit"] == "m"
        assert demo["frames"]["provenance"]["kind"] == "SYNTHETIC_DEMO"
        assert demo["scenario"]["type"] == "FORCED_HYPOTHETICAL"
        assert demo["result"]["resolved_fragment_count"] == 0
        assert demo["frames"]["samples"][0]["positions"] == []
        assert client.get("/openapi.json").json() == json.loads(
            (ROOT / "packages/contracts/openapi.json").read_text(encoding="utf-8")
        )


def test_unavailable_fixture_returns_safe_error(tmp_path: Path) -> None:
    with TestClient(create_app(tmp_path / "missing.json")) as client:
        assert client.get("/health").json()["cache_ready"] is False
        response = client.get("/api/v1/demo")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DEMO_UNAVAILABLE"
        assert response.json()["request_id"]
        assert str(tmp_path) not in response.text
