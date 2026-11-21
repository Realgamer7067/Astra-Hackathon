from datetime import UTC, datetime

import numpy as np
import pytest
from app.models.wire import CartesianState, InertialState
from app.orbit.numerical import EARTH_MU, EARTH_RADIUS, propagate
from app.physics.collision import compute_impact
from app.physics.fragmentation import fragment

EPOCH = datetime(2026, 11, 21, 12, tzinfo=UTC)


def state(object_id: str, x: float, z_velocity: float) -> InertialState:
    return InertialState(
        at_utc=EPOCH,
        frame="GCRS",
        position_unit="km",
        velocity_unit="km/s",
        state=CartesianState(
            object_id=object_id, position=(x, 0, 0), velocity=(0, 7.5, z_velocity)
        ),
    )


def impact(z_velocity: float = 1):
    return compute_impact((state("a", 7000, 0), state("b", 7002, z_velocity)), (1000, 500), 1)


def test_forced_contact_preserves_original_state_and_computes_si_energy():
    event = impact()
    modification = event.modification
    assert modification.original_separation_km == 2
    assert modification.original_state.state.position == (7002, 0, 0)
    assert modification.modified_state.state.position == (7000, 0, 0)
    assert modification.modified_state.state.velocity == (0, 7.5, 1)
    assert event.relative_speed_km_s == pytest.approx(1)
    assert event.energy_j == pytest.approx(166_666_666.6666667)


def test_fragmentation_seed_and_physical_budgets():
    event = impact()
    first = fragment(event, seed=42, count=128, maximum_length_m=4)
    repeat = fragment(event, seed=42, count=128, maximum_length_m=4)
    np.testing.assert_array_equal(first.masses_kg, repeat.masses_kg)
    np.testing.assert_array_equal(first.velocities_km_s, repeat.velocities_km_s)
    assert not np.array_equal(first.masses_kg, fragment(event, 43, 128, 4).masses_kg)
    assert np.all(first.masses_kg > 0)
    assert first.masses_kg.sum() + first.unresolved_mass_kg == pytest.approx(1500)
    offsets = first.velocities_km_s - event.com_velocity_km_s
    np.testing.assert_allclose(first.masses_kg @ offsets, np.zeros(3), atol=1e-8)
    assert 0.5e6 * np.sum(first.masses_kg[:, None] * offsets**2) <= first.energy_budget_j + 1e-6


def test_zero_energy_cannot_create_relative_fragment_motion():
    event = impact(z_velocity=0)
    cloud = fragment(event, seed=42, count=1, maximum_length_m=4)
    np.testing.assert_array_equal(cloud.velocities_km_s[0], event.com_velocity_km_s)


def test_two_body_circular_orbit_matches_analytic_reference():
    radius = 7000.0
    speed = np.sqrt(EARTH_MU / radius)
    samples = propagate(
        np.array([[radius, 0, 0]]),
        np.array([[0, speed, 0]]),
        duration_s=5400,
        sample_step_s=60,
        axis=np.array([0.0, 0.0, 1.0]),
        j2=0,
    )
    theta = speed / radius * samples.seconds[-1]
    expected = [radius * np.cos(theta), radius * np.sin(theta), 0]
    np.testing.assert_allclose(samples.positions_km[-1, 0], expected, rtol=0, atol=0.02)
    assert not samples.crossings


def test_j2_regresses_ascending_node_for_prograde_orbit():
    radius = 7000.0
    speed = np.sqrt(EARTH_MU / radius)
    cases = {"duration_s": 5400, "sample_step_s": 60, "axis": np.array([0.0, 0.0, 1.0])}
    initial_position = np.array([[radius, 0, 0]])
    initial_velocity = np.array([[0, speed / np.sqrt(2), speed / np.sqrt(2)]])
    plain = propagate(initial_position, initial_velocity, **cases, j2=0)
    j2 = propagate(initial_position, initial_velocity, **cases)

    def node(run):
        h = np.cross(run.positions_km[-1, 0], run.final_velocities_km_s[0])
        return np.arctan2(h[0], -h[1])

    assert node(j2) < node(plain) - 0.001


def test_entry_threshold_terminates_only_crossing_fragment():
    radius = EARTH_RADIUS + 121
    samples = propagate(
        np.array([[radius, 0, 0], [7000, 0, 0]]),
        np.array([[-1, 7, 0], [0, np.sqrt(EARTH_MU / 7000), 0]]),
        duration_s=120,
        sample_step_s=60,
        axis=np.array([0.0, 0.0, 1.0]),
        j2=0,
    )
    [crossing] = samples.crossings
    assert crossing.fragment_index == 0 and 0 < crossing.elapsed_s < 2
    assert np.linalg.norm(crossing.position_km) == pytest.approx(EARTH_RADIUS + 120, abs=0.001)
    assert np.isnan(samples.positions_km[1:, 0]).all()
    assert np.isfinite(samples.positions_km[:, 1]).all()
