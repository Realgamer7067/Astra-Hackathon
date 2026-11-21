from copy import deepcopy
from threading import Event
from time import monotonic, sleep

import numpy as np
import pytest
from app.jobs import scenario_jobs
from app.main import create_app
from fastapi.testclient import TestClient


def payload(client: TestClient, other: str = "DEMO:009") -> dict:
    scenario = deepcopy(client.get("/api/v1/demo").json()["scenario"])
    scenario["participants"][1]["object_id"] = other
    scenario["simulation"].update(
        duration_hours=0.05, output_step_seconds=1, max_resolved_fragments=16
    )
    scenario["requested_products"] = ["TRAJECTORIES", "ENTRY_CROSSINGS"]
    return scenario


def wait_for_job(client: TestClient, job_id: str) -> dict:
    deadline = monotonic() + 8
    while monotonic() < deadline:
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["state"] not in {"queued", "running"}:
            return job
        sleep(0.02)
    pytest.fail("job did not reach a terminal state")


@pytest.mark.parametrize("other", ["DEMO:002", "DEMO:009"])
def test_synthetic_pair_computes_and_pages_trajectory(other: str):
    with TestClient(create_app()) as client:
        created = client.post("/api/v1/scenarios", json=payload(client, other))
        assert created.status_code == 201, created.text
        scenario_id = created.json()["scenario_id"]
        path = f"/api/v1/scenarios/{scenario_id}"
        assert client.get(f"{path}/frames").status_code == 409
        job = client.post(f"{path}/run")
        assert job.status_code == 202
        done = wait_for_job(client, job.json()["job_id"])
        assert done["state"] == "completed", done
        assert done["seed"] == 42
        summary = client.get(f"{path}/simulation").json()
        assert summary["scenario_type"] == "FORCED_HYPOTHETICAL"
        assert summary["impact_energy_j"] > 0
        assert summary["resolved_fragment_count"] == 16
        assert summary["modification"]["original_state"]["state"]["object_id"] == other
        assert summary["provenance"]["kind"] == "SYNTHETIC_DEMO"
        first = client.get(f"{path}/frames").json()
        assert first["frame"] == "ITRS" and first["position_unit"] == "m"
        assert len(first["samples"]) == 120
        assert len(first["samples"][0]["positions"]) == 16
        target = client.get("/api/v1/demo").json()["states"]["states"][0]
        np.testing.assert_allclose(
            first["samples"][0]["positions"][0]["position"], target["position"], rtol=0, atol=1e-5
        )
        assert (
            first["samples"][0]["positions"][0]["position"]
            != first["samples"][1]["positions"][0]["position"]
        )
        assert first["provenance"]["coordinateFrame"] == "ITRS"
        second = client.get(f"{path}/frames", params={"cursor": first["next_cursor"]}).json()
        assert len(second["samples"]) == 61
        assert second["next_cursor"] is None
        assert first["samples"][-1]["at_utc"] < second["samples"][0]["at_utc"]
        assert client.get(f"{path}/frames", params={"cursor": 1000}).status_code == 422
        assert (
            client.get(f"{path}/frames", params={"from": "2026-11-21T12:05:00Z"}).json()["samples"]
            == []
        )


def test_rejects_missing_inputs_and_excessive_payloads():
    with TestClient(create_app()) as client:
        scenario = payload(client, "unknown")
        missing = client.post("/api/v1/scenarios", json=scenario)
        assert (missing.status_code, missing.json()["error"]["code"]) == (404, "OBJECT_NOT_FOUND")
        scenario = payload(client)
        scenario["participants"][0].pop("assumed_mass_kg")
        missing = client.post("/api/v1/scenarios", json=scenario)
        assert (missing.status_code, missing.json()["error"]["code"]) == (
            422,
            "ASSUMPTIONS_REQUIRED",
        )
        scenario = payload(client)
        scenario["simulation"].update(duration_hours=24, max_resolved_fragments=1500)
        excessive = client.post("/api/v1/scenarios", json=scenario)
        assert (excessive.status_code, excessive.json()["error"]["code"]) == (422, "SAMPLE_BUDGET")
        assert client.post("/api/v1/scenarios", content="{}").status_code == 415
        excessive = client.post(
            "/api/v1/scenarios",
            content=b" " * (1_048_576 + 1),
            headers={"Content-Type": "application/json"},
        )
        assert (excessive.status_code, excessive.json()["error"]["code"]) == (413, "BODY_TOO_LARGE")


def test_capacity_and_cancel_are_cooperative(monkeypatch: pytest.MonkeyPatch):
    release = Event()

    def wait_for_release(_prepared, _scenario_id, checkpoint):
        release.wait(5)
        checkpoint(0.5)
        raise AssertionError("expected the fixture job to be cancelled")

    monkeypatch.setattr(scenario_jobs, "simulate", wait_for_release)
    with TestClient(create_app()) as client:
        ids = [
            client.post("/api/v1/scenarios", json=payload(client)).json()["scenario_id"]
            for _ in range(3)
        ]
        jobs = [client.post(f"/api/v1/scenarios/{key}/run").json() for key in ids[:2]]
        try:
            assert (
                client.post(f"/api/v1/scenarios/{ids[0]}/run").json()["job_id"] == jobs[0]["job_id"]
            )
            assert client.post(f"/api/v1/scenarios/{ids[2]}/run").status_code == 429
            for job in jobs:
                assert client.post(f"/api/v1/jobs/{job['job_id']}/cancel").status_code == 202
        finally:
            release.set()
        for job in jobs:
            assert wait_for_job(client, job["job_id"])["state"] == "cancelled"
            assert (
                client.post(f"/api/v1/jobs/{job['job_id']}/cancel").json()["state"] == "cancelled"
            )
