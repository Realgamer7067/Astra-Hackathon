"""Validated coordinate frame transformations using Astropy (TEME, GCRS, ITRS)."""

from __future__ import annotations

from datetime import datetime, timedelta

from astropy import units as u  # type: ignore[import-untyped]
from astropy.coordinates import (  # type: ignore[import-untyped]
    GCRS,
    ITRS,
    TEME,
    CartesianDifferential,
    CartesianRepresentation,
)
from astropy.time import Time  # type: ignore[import-untyped]

from ..models.wire import Vector3


def require_utc(epoch_utc: datetime) -> datetime:
    """Validate that an epoch is timezone-aware UTC."""
    if epoch_utc.tzinfo is None or epoch_utc.utcoffset() != timedelta(0):
        raise ValueError("epoch_utc must be timezone-aware UTC")
    return epoch_utc


def _to_teme(pos_km: Vector3, vel_kms: Vector3, epoch_utc: datetime) -> TEME:
    utc = require_utc(epoch_utc)
    obstime = Time(utc, scale="utc")
    rep = CartesianRepresentation(
        x=pos_km[0] * u.km,
        y=pos_km[1] * u.km,
        z=pos_km[2] * u.km,
        differentials=CartesianDifferential(
            d_x=vel_kms[0] * (u.km / u.s),
            d_y=vel_kms[1] * (u.km / u.s),
            d_z=vel_kms[2] * (u.km / u.s),
        ),
    )
    return TEME(rep, obstime=obstime)


def teme_to_gcrs(pos_km: Vector3, vel_kms: Vector3, epoch_utc: datetime) -> tuple[Vector3, Vector3]:
    """Transform TEME state (km, km/s) to GCRS inertial state (km, km/s)."""
    teme = _to_teme(pos_km, vel_kms, epoch_utc)
    gcrs = teme.transform_to(GCRS(obstime=teme.obstime))
    cart = gcrs.cartesian
    pos = cart.xyz.to_value(u.km)
    vel = cart.differentials["s"].d_xyz.to_value(u.km / u.s)
    return (float(pos[0]), float(pos[1]), float(pos[2])), (
        float(vel[0]),
        float(vel[1]),
        float(vel[2]),
    )


def teme_to_itrs(pos_km: Vector3, vel_kms: Vector3, epoch_utc: datetime) -> tuple[Vector3, Vector3]:
    """Transform TEME state (km, km/s) to ITRS Earth-fixed render state (m, m/s)."""
    teme = _to_teme(pos_km, vel_kms, epoch_utc)
    itrs = teme.transform_to(ITRS(obstime=teme.obstime))
    cart = itrs.cartesian
    pos = cart.xyz.to_value(u.m)
    vel = cart.differentials["s"].d_xyz.to_value(u.m / u.s)
    return (float(pos[0]), float(pos[1]), float(pos[2])), (
        float(vel[0]),
        float(vel[1]),
        float(vel[2]),
    )


def gcrs_to_itrs(pos_km: Vector3, vel_kms: Vector3, epoch_utc: datetime) -> tuple[Vector3, Vector3]:
    """Transform GCRS inertial state (km, km/s) to ITRS render state (m, m/s)."""
    utc = require_utc(epoch_utc)
    obstime = Time(utc, scale="utc")
    rep = CartesianRepresentation(
        x=pos_km[0] * u.km,
        y=pos_km[1] * u.km,
        z=pos_km[2] * u.km,
        differentials=CartesianDifferential(
            d_x=vel_kms[0] * (u.km / u.s),
            d_y=vel_kms[1] * (u.km / u.s),
            d_z=vel_kms[2] * (u.km / u.s),
        ),
    )
    gcrs = GCRS(rep, obstime=obstime)
    itrs = gcrs.transform_to(ITRS(obstime=obstime))
    cart = itrs.cartesian
    pos = cart.xyz.to_value(u.m)
    vel = cart.differentials["s"].d_xyz.to_value(u.m / u.s)
    return (float(pos[0]), float(pos[1]), float(pos[2])), (
        float(vel[0]),
        float(vel[1]),
        float(vel[2]),
    )
