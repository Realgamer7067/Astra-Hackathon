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
from app.main import create_app
from app.models.wire import (
    CartesianState,
    CloseApproach,
    ForcedModification,
    InertialState,
    OccupancyBin,
    Provenance,
    ScenarioRequest,
    ScenarioResult,
)
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
from fastapi.testclient import TestClient

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

    def test_interior_approach_swept_filtering(self):
        """Regression test: endpoints 200+ km apart but coincident at midpoint t=120s.

        Fragment: (7000, -400, 0) -> (7000, 400, 0)
        Candidate: (7600, -400, 0) -> (6400, 400, 0)
        At t=0: sep = 600 km (different shells / rejected by discrete endpoints).
        At t=240: sep = 600 km.
        At t=120: sep = 0 km (coincident).
        Conservative swept altitude interval filtering and relative-motion refinement
        must detect this interior approach.
        """
        f0 = StateVector("frag-int", 0.0, 7000.0, -400.0, 0.0, 0.0, 0.0, 0.0)
        f1 = StateVector("frag-int", 240.0, 7000.0, 400.0, 0.0, 0.0, 0.0, 0.0)

        c0 = StateVector("cand-int", 0.0, 7600.0, -400.0, 0.0, 0.0, 0.0, 0.0)
        c1 = StateVector("cand-int", 240.0, 6400.0, 400.0, 0.0, 0.0, 0.0, 0.0)

        res = screen_encounters([f0, f1], [c0, c1])
        assert len(res.encounters) >= 1
        best = min(res.encounters, key=lambda e: e.separation_km)
        assert best.catalog_object_id == "cand-int"
        assert best.fragment_id == "frag-int"
        assert abs(best.epoch_s - 120.0) < 1e-4
        assert best.separation_km < 1e-4

    def test_real_near_miss_interior_minimum(self):
        """Interior minimum approach with non-zero near miss (e.g. 15 km separation)."""
        # At t=0, sep = 200 km; at t=200, sep = 200 km; at t=100, sep = 15 km
        f0 = StateVector("frag-nm", 0.0, 7000.0, -100.0, 0.0, 0.0, 0.0, 0.0)
        f1 = StateVector("frag-nm", 200.0, 7000.0, 100.0, 0.0, 0.0, 0.0, 0.0)

        c0 = StateVector("cand-nm", 0.0, 7015.0, -100.0, 200.0, 0.0, 0.0, 0.0)
        c1 = StateVector("cand-nm", 200.0, 7015.0, 100.0, -200.0, 0.0, 0.0, 0.0)

        res = screen_encounters([f0, f1], [c0, c1])
        assert len(res.encounters) >= 1
        best = min(res.encounters, key=lambda e: e.separation_km)
        assert abs(best.epoch_s - 100.0) < 1e-4
        assert abs(best.separation_km - 15.0) < 1e-2

    def test_max_encounters_cap(self):
        """Output is capped at limits.max_encounters."""
        # Create many close pairs
        frags = [_sv(f"f-{i}", 0.0, 400.0 + i * 0.001, i * 0.001) for i in range(50)]
        cands = [_sv(f"c-{i}", 0.0, 400.0 + i * 0.001, i * 0.001 + 0.0001) for i in range(50)]

        limits = ScreeningLimits(max_encounters=5, max_candidate_pairs=100_000)
        result = screen_encounters(frags, cands, limits)
        assert len(result.encounters) <= 5
        assert result.truncated

    def test_interior_minimum_between_samples(self):
        """Objects far apart at sample endpoints but crossing close in-between must be detected."""
        # Frag at x= -100 at t=0, x= +100 at t=10; y=0, z=0
        # Cand at y= -100 at t=0, y= +100 at t=10; x=0, z=0
        # At t=0: sep = sqrt((-100)^2 + (100)^2) = 141.42 km (outside 100km threshold!)
        # At t=10: sep = sqrt((100)^2 + (-100)^2) = 141.42 km (outside 100km threshold!)
        # At t=5: frag at (0,0,0), cand at (0,0,0) -> separation = 0 km!
        r_base = R_EARTH_KM + 400.0
        f0 = _sv_xyz("frag-int", 0.0, r_base - 100.0, 0.0, 0.0)
        f1 = _sv_xyz("frag-int", 10.0, r_base + 100.0, 0.0, 0.0)

        c0 = _sv_xyz("cand-int", 0.0, r_base, -100.0, 0.0)
        c1 = _sv_xyz("cand-int", 10.0, r_base, 100.0, 0.0)

        frags = [f0, f1]
        cands = [c0, c1]

        result = screen_encounters(frags, cands, ScreeningLimits(refine_threshold_km=100.0))
        assert len(result.encounters) == 1
        enc = result.encounters[0]
        assert enc.separation_km < 1.0  # accurately detected close approach at midpoint
        assert abs(enc.epoch_s - 5.0) < 0.1

    def test_real_near_miss_interval_refinement(self):
        """Relative-motion interval refinement correctly detects a non-zero near miss."""
        r_base = R_EARTH_KM + 500.0
        # Frag moves along x: -50 to +50 km, offset z = 12 km
        # Cand stationary at (r_base, 0, 0)
        # Endpoints separation: sqrt(50^2 + 12^2) = 51.42 km
        # Interior minimum at t=5: separation = 12 km
        f0 = _sv_xyz("frag-nm", 0.0, r_base - 50.0, 0.0, 12.0)
        f1 = _sv_xyz("frag-nm", 10.0, r_base + 50.0, 0.0, 12.0)

        c0 = _sv_xyz("cand-nm", 0.0, r_base, 0.0, 0.0)
        c1 = _sv_xyz("cand-nm", 10.0, r_base, 0.0, 0.0)

        result = screen_encounters([f0, f1], [c0, c1])
        assert len(result.encounters) == 1
        assert abs(result.encounters[0].separation_km - 12.0) < 1e-4
        assert abs(result.encounters[0].epoch_s - 5.0) < 1e-4

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

    def test_earth_rotation_longitude_at_known_epoch(self):
        """GCRS to ITRS transformation rotates longitude by Earth's rotation angle."""
        # Satellite on GCRS +X axis: lat=0, lon_gcrs=0
        # After 6 hours (21600 s), Earth rotates 90 degrees eastward.
        # In ITRS (Earth-fixed), longitude should be -90 deg (or 270 deg).
        r = R_EARTH_KM + 500.0
        dt_s = 21600.0  # 6 hours
        expected_theta_rad = (7.2921159e-5 * dt_s) % (2.0 * math.pi)
        expected_lon_deg = math.degrees(-expected_theta_rad)

        sv = StateVector(
            object_id="f-rot",
            epoch_s=dt_s,
            x=r,
            y=0.0,
            z=0.0,
            vx=0.0,
            vy=0.0,
            vz=0.0,
        )
        projections = compute_ground_projections([sv], gmst0_rad=0.0, is_inertial=True)
        assert len(projections) == 1
        p = projections[0]
        assert abs(p.latitude_deg) < 1e-4
        assert abs(p.longitude_deg - expected_lon_deg) < 1e-4

    def test_absolute_longitude_at_fixture_epoch(self):
        """Regression test: GCRS (7000, 0, 0) at 2026-11-21T12:00:00Z yields ~119.84 deg E.

        Matches standard IAU 2000 Earth Rotation Angle (ERA) conversion:
        Days since J2000.0 (2000-01-01 12:00:00 UTC) = 9821.0.
        ERA theta ~ 240.1589 deg.
        GCRS +X rotated by -theta yields ITRS lon = +119.8411 deg E.
        """
        sv = StateVector(
            object_id="f-gcrs",
            epoch_s=0.0,
            x=7000.0,
            y=0.0,
            z=0.0,
            vx=0.0,
            vy=0.0,
            vz=0.0,
        )
        projections = compute_ground_projections(
            [sv],
            scenario_epoch_utc="2026-11-21T12:00:00Z",
            is_inertial=True,
        )
        assert len(projections) == 1
        p = projections[0]
        assert abs(p.latitude_deg) < 1e-4
        assert abs(p.longitude_deg - 119.8411) < 0.05


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

    def test_computed_run_data_used_in_results_and_report(self):
        """Computed runs (TASK-003) stored in app.state.runs are returned correctly."""
        app = create_app()

        computed_result = ScenarioResult(
            schema_version="1.0",
            generated_at_utc="2026-11-21T14:00:00Z",
            scenario_id="computed-scenario-42",
            resolved_fragment_count=128,
            unresolved_mass_kg=12.5,
            modification=ForcedModification(
                original_state=InertialState(
                    at_utc="2026-11-21T12:00:00Z",
                    frame="GCRS",
                    position_unit="km",
                    velocity_unit="km/s",
                    state=CartesianState(
                        object_id="NORAD:11111",
                        position=(7000.0, 0.0, 0.0),
                        velocity=(0.0, 7.5, 0.0),
                    ),
                ),
                modified_state=InertialState(
                    at_utc="2026-11-21T12:00:00Z",
                    frame="GCRS",
                    position_unit="km",
                    velocity_unit="km/s",
                    state=CartesianState(
                        object_id="NORAD:11111",
                        position=(6999.0, 0.0, 0.0),
                        velocity=(0.0, 7.5, 0.0),
                    ),
                ),
                original_separation_km=1.0,
            ),
            occupancy=[
                OccupancyBin(altitude_min_km=500.0, altitude_max_km=600.0, resolved_count=128)
            ],
            encounters=[
                CloseApproach(
                    catalog_object_id="NORAD:22222",
                    fragment_id="frag-42",
                    at_utc="2026-11-21T13:30:00Z",
                    separation_km=8.45,
                )
            ],
            entry_crossings=[],
            provenance=Provenance(
                kind="HYPOTHETICAL_SIMULATION",
                mode="LIVE",
                source="ASTRA Numerical Integrator",
                catalogSnapshotId="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                modelVersion="v1.0.0",
                coordinateFrame="GCRS",
                assumptions=["J2 perturbation included"],
                limitations=["No drag model"],
            ),
        )

        computed_scenario = ScenarioRequest(
            schema_version="1.0",
            type="FORCED_HYPOTHETICAL",
            epoch_utc="2026-11-21T12:00:00Z",
            participants=[
                {"object_id": "NORAD:11111", "assumed_mass_kg": 1000.0, "assumed_radius_m": 2.0},
                {"object_id": "NORAD:99999", "assumed_mass_kg": 500.0, "assumed_radius_m": 1.5},
            ],
            forced_contact={"move_participant_index": 0, "impact_geometry": "CENTERED"},
            simulation={
                "seed": 99,
                "duration_hours": 2.0,
                "output_step_seconds": 60,
                "max_resolved_fragments": 128,
                "max_cascade_generations": 0,
            },
            requested_products=["TRAJECTORIES", "SECONDARY_ENCOUNTERS"],
        )

        app.state.runs = {
            "computed-scenario-42": {
                "result": computed_result,
                "scenario": computed_scenario,
            }
        }

        with TestClient(app) as test_client:
            # 1. /results route returns the computed run
            resp_results = test_client.get("/api/v1/scenarios/computed-scenario-42/results")
            assert resp_results.status_code == 200
            res_data = resp_results.json()
            assert res_data["scenario_id"] == "computed-scenario-42"
            assert res_data["resolved_fragment_count"] == 128
            assert res_data["modification"]["original_separation_km"] == 1.0

            # 2. /report route returns the computed run with seed, participants, modification
            resp_report = test_client.get(
                "/api/v1/scenarios/computed-scenario-42/report?format=json"
            )
            assert resp_report.status_code == 200
            rep_data = resp_report.json()
            assert rep_data["scenario_id"] == "computed-scenario-42"
            assert rep_data["seed"] == 99
            assert rep_data["sections"][0]["title"] == "Collision Participants"
            assert rep_data["sections"][1]["title"] == "Forced State Modification"
            assert rep_data["sections"][1]["content"]["original_separation_km"] == 1.0

            # 3. Genuinely unknown scenario ID returns 404
            resp_unknown = test_client.get("/api/v1/scenarios/unknown-9999/results")
            assert resp_unknown.status_code == 404
            assert resp_unknown.json()["error"]["code"] == "SCENARIO_NOT_FOUND"

            resp_unknown_report = test_client.get("/api/v1/scenarios/unknown-9999/report")
            assert resp_unknown_report.status_code == 404
            assert resp_unknown_report.json()["error"]["code"] == "SCENARIO_NOT_FOUND"

    def test_scenario_jobs_result_only_preserves_seed_73(self):
        """TASK-003 completed collision runs in app.state.scenario_jobs.

        Result-only records carrying custom seeds (e.g. seed 73) must return 200
        on /results, export seed 73 in /report (not default to 42), and preserve
        all provenance and modification states.
        """
        app = create_app()
        app.state.scenario_jobs = {
            "job-task003-73": {
                "scenario_id": "scenario-73",
                "seed": 73,
                "result": ScenarioResult(
                    schema_version="1.0",
                    generated_at_utc="2026-11-21T12:00:00Z",
                    scenario_id="scenario-73",
                    resolved_fragment_count=64,
                    unresolved_mass_kg=25.0,
                    modification=None,
                    occupancy=[
                        OccupancyBin(
                            altitude_min_km=400.0,
                            altitude_max_km=500.0,
                            resolved_count=64,
                        )
                    ],
                    encounters=[],
                    entry_crossings=[],
                    provenance=Provenance(
                        kind="HYPOTHETICAL_SIMULATION",
                        mode="LIVE",
                        source="ASTRA Collision Worker (TASK-003)",
                        catalogSnapshotId="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                        modelVersion="v1.0.0",
                        coordinateFrame="GCRS",
                        assumptions=["Physical conservation verified"],
                        limitations=["Hypothetical debris only"],
                    ),
                ),
            }
        }

        with TestClient(app) as client:
            # 1. /results finds scenario via scenario_jobs
            resp_res = client.get("/api/v1/scenarios/scenario-73/results")
            assert resp_res.status_code == 200
            res = resp_res.json()
            assert res["scenario_id"] == "scenario-73"
            assert res["resolved_fragment_count"] == 64
            assert res["provenance"]["source"] == "ASTRA Collision Worker (TASK-003)"

            # 2. /report exports seed 73
            resp_rep = client.get("/api/v1/scenarios/scenario-73/report?format=json")
            assert resp_rep.status_code == 200
            rep = resp_rep.json()
            assert rep["scenario_id"] == "scenario-73"
            assert rep["seed"] == 73
            assert len(rep["sections"]) > 0
            assert rep["sections"][0]["provenance"]["kind"] == "HYPOTHETICAL_SIMULATION"
            assert rep["sections"][0]["provenance"]["source"] == "ASTRA Collision Worker (TASK-003)"
