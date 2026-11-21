"""Convert local fixture and replay coordinates using bundled Earth orientation data."""

from datetime import datetime

import numpy as np
from astropy import units as u  # type: ignore[import-untyped]
from astropy.coordinates import (  # type: ignore[import-untyped]
    GCRS,
    ITRS,
    CartesianDifferential,
    CartesianRepresentation,
    EarthLocation,
)
from astropy.time import Time  # type: ignore[import-untyped]
from astropy.utils import iers  # type: ignore[import-untyped]

from ..models.wire import CartesianState, InertialState
from ..physics.collision import FloatArray, vector_tuple

# The only supported source in this lane is a fixed offline snapshot.
iers.conf.auto_download = False


def to_inertial(
    states: tuple[CartesianState, CartesianState], epoch: datetime
) -> tuple[InertialState, InertialState]:
    time = Time(epoch, scale="utc")
    positions = np.asarray([state.position for state in states], dtype=np.float64)
    velocities = np.asarray([state.velocity for state in states], dtype=np.float64)
    along = CartesianDifferential(velocities.T * u.m / u.s)
    original = ITRS(CartesianRepresentation(positions.T * u.m, differentials=along), obstime=time)
    inertial = original.transform_to(GCRS(obstime=time))
    positions = np.asarray(inertial.cartesian.xyz.to_value(u.km).T, dtype=np.float64)
    velocities = np.asarray(inertial.velocity.d_xyz.to_value(u.km / u.s).T, dtype=np.float64)

    def row(index: int) -> InertialState:
        return InertialState(
            at_utc=epoch,
            frame="GCRS",
            position_unit="km",
            velocity_unit="km/s",
            state=CartesianState(
                object_id=states[index].object_id,
                position=vector_tuple(positions[index]),
                velocity=vector_tuple(velocities[index]),
            ),
        )

    return row(0), row(1)


def earth_axis(epoch: datetime) -> FloatArray:
    time = Time(epoch, scale="utc")
    pole = ITRS(CartesianRepresentation([0, 0, 1] * u.km), obstime=time)
    xyz = np.asarray(
        pole.transform_to(GCRS(obstime=time)).cartesian.xyz.to_value(u.km), dtype=np.float64
    )
    return xyz / float(np.linalg.norm(xyz))


def to_render(positions_km: FloatArray, epochs: list[datetime]) -> FloatArray:
    if not epochs:
        return np.empty((0, 3))
    times = Time(epochs, scale="utc")
    inertial = GCRS(CartesianRepresentation(positions_km.T * u.km), obstime=times)
    fixed = inertial.transform_to(ITRS(obstime=times))
    return np.asarray(fixed.cartesian.xyz.to_value(u.m).T, dtype=np.float64)


def entry_coordinates(positions_m: FloatArray) -> list[tuple[float, float]]:
    if not len(positions_m):
        return []
    location = EarthLocation.from_geocentric(*positions_m.T, unit=u.m)
    return [
        (float(lat), float(lon))
        for lat, lon in zip(location.lat.deg, location.lon.deg, strict=True)
    ]
