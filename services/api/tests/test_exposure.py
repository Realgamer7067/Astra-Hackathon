"""Tests for TASK-005: screening, exposure, results routes, and report.

Covers:
  - Bounded broad-phase screening cross-checked against brute force
  - Shell occupancy from states
  - Ground projections independent from entry crossings
  - Entry crossing detection
  - Provenance preservation in reports
  - API route responses
"""

from __future__ import annotations

import json
import math

import pytest
from app.physics.exposure import (
    R_EARTH_KM,
    compute_ground_projections,
    compute_occupancy,
    detect_entry_crossings,
    summarize_exposure,
)
from app.physics.screening import (
    ScreeningLimits,
    StateVector,
    brute_force_screen,
    screen_encounters,
)
from app.services.report import build_report

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _sv(oid: str, epoch: float, alt_km: float, theta_deg: float = 0.0) -> StateVector:
    """Create a StateVector on a spherical shell at given altitude and angle."""
    r = R_EARTH_KM + alt_km
    theta = math.radians(theta_deg)
    return StateVector(
        object_id=oid,
        epoch_s=epoch,
        x=r * math.cos(theta),
        y=r * math.sin(theta),
        z=0.0,
        vx=0.0,
        vy=7.5,
        vz=0.0,
    )


def _sv_xyz(oid: str, epoch: float, x: float, y: float, z: float) -> StateVector:
    return StateVector(
        object_id=oid,
        epoch_s=epoch,
        x=x,
        y=y,
        z=z,
        vx=0.0,
        vy=0.0,
        vz=0.0,
    )


# ===========================================================================
# Screening tests
# ===========================================================================


class TestScreeningBroadPhaseVsBruteForce:
    """Cross-check: bounded screening must find every encounter that
    brute force finds within the same threshold."""

    def test_encounters_match_brute_force(self):
        """All brute-force encounters within threshold appear in bounded results."""
        frags = [
            _sv("frag-A", 0.0, 400.0, 0.0),
            _sv("frag-B", 0.0, 405.0, 1.0),
            _sv("frag-C", 0.0, 800.0, 0.0),  # far away
        ]
        cands = [
            _sv("cat-1", 0.0, 402.0, 0.5),
            _sv("cat-2", 0.0, 410.0, 0.0),
            _sv("cat-3", 0.0, 1200.0, 0.0),  # far away
        ]

        threshold = 100.0
        limits = ScreeningLimits(
            broad_phase_bin_km=200.0,
            refine_threshold_km=threshold,
            max_encounters=500,
            max_candidate_pairs=100_000,
        )

        bounded = screen_encounters(frags, cands, limits)
        brute = brute_force_screen(frags, cands, threshold)

        # Every brute-force encounter must appear in bounded results
        brute_pairs = {(e.fragment_id, e.catalog_object_id) for e in brute}
        bounded_pairs = {(e.fragment_id, e.catalog_object_id) for e in bounded.encounters}

        assert brute_pairs.issubset(bounded_pairs), (
            f"Brute force found encounters not in bounded: {brute_pairs - bounded_pairs}"
        )

    def test_separations_match(self):
        """Separations from bounded screening match brute force exactly."""
        frags = [_sv("frag-1", 60.0, 500.0, 2.0)]
        cands = [_sv("cat-1", 60.0, 505.0, 2.5)]

        bounded = screen_encounters(frags, cands)
        brute = brute_force_screen(frags, cands, 100.0)

        for be in brute:
            match = [
                e
                for e in bounded.encounters
                if e.fragment_id == be.fragment_id and e.catalog_object_id == be.catalog_object_id
            ]
            assert len(match) == 1
            assert abs(match[0].separation_km - be.separation_km) < 1e-10

    def test_near_miss_not_promoted_to_contact(self):
        """Near misses are reported with separation — never as contacts."""
        frags = [_sv("frag-1", 0.0, 400.0, 0.0)]
        cands = [_sv("cat-1", 0.0, 400.5, 0.0)]

        result = screen_encounters(frags, cands)
        for enc in result.encounters:
            assert enc.separation_km > 0, "Near miss must not be reported as zero-distance contact"

    def test_distant_objects_rejected(self):
        """Objects in very different shells produce no encounters."""
        frags = [_sv("frag-1", 0.0, 400.0)]
        cands = [_sv("cat-1", 0.0, 2000.0)]

        result = screen_encounters(frags, cands)
        assert len(result.encounters) == 0

    def test_max_encounters_cap(self):
        """Output is capped at limits.max_encounters."""
        # Create many close pairs
        frags = [_sv(f"f-{i}", 0.0, 400.0 + i * 0.001, i * 0.001) for i in range(50)]
        cands = [_sv(f"c-{i}", 0.0, 400.0 + i * 0.001, i * 0.001 + 0.0001) for i in range(50)]

        limits = ScreeningLimits(max_encounters=5, max_candidate_pairs=100_000)
        result = screen_encounters(frags, cands, limits)
        assert len(result.encounters) <= 5
        assert result.truncated

    def test_empty_inputs(self):
        result = screen_encounters([], [])
        assert result.encounters == []
        assert result.screened_pair_count == 0


# ===========================================================================
# Occupancy tests
# ===========================================================================


class TestOccupancy:
    def test_shell_counts_from_states(self):
        """Occupancy bins correctly count fragments per shell."""
        states = [
            _sv("f-1", 0.0, 50.0),  # 0–100 km shell
            _sv("f-2", 0.0, 150.0),  # 100–200 km shell
            _sv("f-3", 0.0, 350.0),  # 300–400 km shell
            _sv("f-4", 0.0, 350.5),  # 300–400 km shell (same shell, different fragment)
        ]
        bins = compute_occupancy(states, bin_size_km=100.0)

        bin_dict = {(b.altitude_min_km, b.altitude_max_km): b.resolved_count for b in bins}
        assert bin_dict.get((0.0, 100.0)) == 1
        assert bin_dict.get((100.0, 200.0)) == 1
        assert bin_dict.get((300.0, 400.0)) == 2

    def test_duplicate_fragment_counted_once(self):
        """Same fragment at multiple epochs counted only once."""
        states = [
            _sv("f-1", 0.0, 400.0),
            _sv("f-1", 60.0, 405.0),  # same fragment, later epoch
        ]
        bins = compute_occupancy(states, bin_size_km=100.0)
        total = sum(b.resolved_count for b in bins)
        assert total == 1

    def test_empty_input(self):
        assert compute_occupancy([]) == []


# ===========================================================================
# Ground projection tests
# ===========================================================================


class TestGroundProjections:
    def test_projections_computed_independently(self):
        """Projections exist for all fragments regardless of altitude."""
        states = [
            _sv("f-high", 0.0, 800.0),  # well above entry
            _sv("f-low", 0.0, 100.0),  # near entry threshold
        ]
        projections = compute_ground_projections(states)
        assert len(projections) == 2

        # Projections are NOT entry warnings
        for p in projections:
            assert hasattr(p, "latitude_deg")
            assert hasattr(p, "longitude_deg")

    def test_projection_does_not_imply_entry(self):
        """A ground projection for a high-altitude fragment is NOT an entry warning."""
        states = [_sv("f-high", 0.0, 800.0)]
        projections = compute_ground_projections(states)
        assert len(projections) == 1
        assert projections[0].altitude_km > 700  # far above 120 km entry


# ===========================================================================
# Entry crossing tests
# ===========================================================================


class TestEntryCrossings:
    def test_crossing_detected(self):
        """Fragment descending through 120 km triggers crossing."""
        series = {
            "f-1": [
                _sv("f-1", 0.0, 200.0),
                _sv("f-1", 60.0, 150.0),
                _sv("f-1", 120.0, 100.0),  # crosses 120 km between 60s and 120s
            ]
        }
        crossings = detect_entry_crossings(series, threshold_km=120.0)
        assert len(crossings) == 1
        assert crossings[0].fragment_id == "f-1"
        assert crossings[0].threshold_altitude_km == 120.0

    def test_no_crossing_above_threshold(self):
        """Fragment staying above threshold triggers no crossing."""
        series = {
            "f-1": [
                _sv("f-1", 0.0, 400.0),
                _sv("f-1", 60.0, 350.0),
            ]
        }
        crossings = detect_entry_crossings(series, threshold_km=120.0)
        assert len(crossings) == 0

    def test_only_first_crossing(self):
        """Only the first downward crossing per fragment is recorded."""
        series = {
            "f-1": [
                _sv("f-1", 0.0, 200.0),
                _sv("f-1", 60.0, 100.0),  # first crossing
                _sv("f-1", 120.0, 200.0),  # back up
                _sv("f-1", 180.0, 80.0),  # second crossing — ignored
            ]
        }
        crossings = detect_entry_crossings(series, threshold_km=120.0)
        assert len(crossings) == 1

    def test_ground_projection_independent_from_entry(self):
        """Projections and entries are computed independently."""
        high_states = [_sv("f-high", 0.0, 800.0)]
        low_series = {
            "f-low": [
                _sv("f-low", 0.0, 200.0),
                _sv("f-low", 60.0, 100.0),
            ]
        }

        projections = compute_ground_projections(high_states)
        crossings = detect_entry_crossings(low_series, threshold_km=120.0)

        # High fragment has projection but no crossing
        assert len(projections) == 1
        assert projections[0].fragment_id == "f-high"

        # Low fragment has crossing
        assert len(crossings) == 1
        assert crossings[0].fragment_id == "f-low"


# ===========================================================================
# Full exposure summary tests
# ===========================================================================


class TestExposureSummary:
    def test_summarize_combines_all(self):
        states = [
            _sv("f-1", 0.0, 400.0),
            _sv("f-2", 0.0, 500.0),
        ]
        series = {
            "f-3": [
                _sv("f-3", 0.0, 200.0),
                _sv("f-3", 60.0, 100.0),
            ],
        }
        summary = summarize_exposure(states, series)
        assert summary.total_fragments_screened == 2
        assert len(summary.occupancy) > 0
        assert len(summary.ground_projections) == 2
        assert len(summary.entry_crossings) == 1
        assert len(summary.provenance_notes) > 0


# ===========================================================================
# Report tests
# ===========================================================================


class TestReport:
    def _build_sample_report(self):
        return build_report(
            scenario_id="test-scenario-01",
            scenario_type="FORCED_HYPOTHETICAL",
            seed=42,
            participants=[
                {"object_id": "DEMO:001", "assumed_mass_kg": 500, "assumed_radius_m": 2},
                {"object_id": "DEMO:009", "assumed_mass_kg": 5, "assumed_radius_m": 0.2},
            ],
            modification={
                "original_separation_km": 1234.5,
                "original_state": {"frame": "GCRS"},
                "modified_state": {"frame": "GCRS"},
            },
            occupancy=[
                {"altitude_min_km": 300, "altitude_max_km": 400, "resolved_count": 15},
                {"altitude_min_km": 400, "altitude_max_km": 500, "resolved_count": 8},
            ],
            encounters=[
                {
                    "catalog_object_id": "DEMO:003",
                    "fragment_id": "frag-1",
                    "at_utc": "2026-11-21T13:00:00Z",
                    "separation_km": 45.2,
                },
            ],
            entry_crossings=[
                {
                    "fragment_id": "frag-5",
                    "at_utc": "2026-11-21T18:00:00Z",
                    "threshold_altitude_km": 120.0,
                    "latitude_deg": 35.0,
                    "longitude_deg": -80.0,
                },
            ],
            fragment_count=23,
            unresolved_mass_kg=50.0,
            provenance={
                "kind": "HYPOTHETICAL_SIMULATION",
                "mode": "DEMO",
                "source": "ASTRA synthetic fixtures",
                "catalogSnapshotId": "sha256:abc123",
                "assumptions": ["Assumed mass for both participants"],
                "limitations": ["No drag model"],
            },
        )

    def test_report_preserves_hypothetical_label(self):
        report = self._build_sample_report()
        md = report.to_markdown()
        assert "HYPOTHETICAL" in md
        assert "NOT A PREDICTION" in md

    def test_report_preserves_provenance(self):
        report = self._build_sample_report()
        data = report.to_dict()
        for section in data["sections"]:
            assert "provenance" in section
            assert section["provenance"]["kind"] == "HYPOTHETICAL_SIMULATION"
            assert section["provenance"]["source"] == "ASTRA synthetic fixtures"

    def test_json_roundtrip(self):
        report = self._build_sample_report()
        j = report.to_json()
        parsed = json.loads(j)
        assert parsed["scenario_id"] == "test-scenario-01"
        assert parsed["seed"] == 42
        assert len(parsed["sections"]) > 0

    def test_markdown_contains_all_sections(self):
        report = self._build_sample_report()
        md = report.to_markdown()
        assert "Collision Participants" in md
        assert "Forced State Modification" in md
        assert "Fragment Summary" in md
        assert "Orbital Shell Occupancy" in md
        assert "Secondary Encounters" in md
        assert "Atmospheric Entry Crossings" in md
        assert "Global Limitations" in md

    def test_no_probability_language(self):
        """Report must not contain unsupported probability language."""
        report = self._build_sample_report()
        md = report.to_markdown().lower()
        for forbidden in [
            "collision probability",
            "predicted outage",
            "casualty",
            "service outage",
            "population affected",
        ]:
            assert forbidden not in md, f"Report contains forbidden language: '{forbidden}'"

    def test_global_limitations_present(self):
        report = self._build_sample_report()
        assert len(report.global_limitations) > 0
        md = report.to_markdown()
        assert "not a prediction" in md.lower()


# ===========================================================================
# API route tests
# ===========================================================================


class TestResultsAPI:
    """Test the results and report API endpoints via TestClient."""

    @pytest.fixture
    def client(self):
        from app.main import create_app
        from fastapi.testclient import TestClient

        with TestClient(create_app()) as test_client:
            yield test_client

    def test_get_results_success(self, client):
        resp = client.get("/api/v1/scenarios/demo-preset-01/results")
        assert resp.status_code == 200
        data = resp.json()
        assert data["schema_version"] == "1.0"
        assert data["scenario_id"] == "demo-preset-01"
        assert "provenance" in data
        assert data["provenance"]["kind"] == "SYNTHETIC_DEMO"

    def test_get_results_not_found(self, client):
        resp = client.get("/api/v1/scenarios/nonexistent/results")
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "SCENARIO_NOT_FOUND"

    def test_get_report_json(self, client):
        resp = client.get("/api/v1/scenarios/demo-preset-01/report?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_id"] == "demo-preset-01"
        assert data["scenario_type"] == "FORCED_HYPOTHETICAL"
        assert len(data["sections"]) > 0
        assert len(data["global_limitations"]) > 0

    def test_get_report_markdown(self, client):
        resp = client.get("/api/v1/scenarios/demo-preset-01/report?format=markdown")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers.get("content-type", "")
        text = resp.text
        assert "HYPOTHETICAL" in text
        assert "NOT A PREDICTION" in text

    def test_get_report_not_found(self, client):
        resp = client.get("/api/v1/scenarios/nonexistent/report")
        assert resp.status_code == 404

    def test_provenance_survives_export(self, client):
        """Provenance fields must be present in every report section."""
        resp = client.get("/api/v1/scenarios/demo-preset-01/report?format=json")
        data = resp.json()
        for section in data["sections"]:
            prov = section["provenance"]
            assert prov["kind"] in (
                "CATALOG_OBSERVATION",
                "PROPAGATED_ESTIMATE",
                "HYPOTHETICAL_SIMULATION",
                "SYNTHETIC_DEMO",
            )
            assert "source" in prov
            assert "assumptions" in prov
            assert "limitations" in prov
