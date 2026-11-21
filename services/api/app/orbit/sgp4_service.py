"""SGP4 propagation service producing declared GCRS or ITRS state batches."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sgp4 import omm  # type: ignore[import-untyped]
from sgp4.api import Satrec, jday  # type: ignore[import-untyped]

from ..models.wire import (
    CartesianState,
    InertialState,
    Provenance,
    RenderStates,
    Vector3,
)
from ..orbit.frames import require_utc, teme_to_gcrs, teme_to_itrs
from ..storage.catalog_cache import STALE_AFTER_HOURS, CatalogSnapshot

MODEL_VERSION = "sgp4-2.27+astropy-teme"


@dataclass(frozen=True)
class PropagatedBatch:
    """Propagated Cartesian states in a declared frame and unit set."""

    at_utc: datetime
    frame: Literal["GCRS", "ITRS"]
    position_unit: Literal["km", "m"]
    velocity_unit: Literal["km/s", "m/s"]
    states: list[CartesianState]
    provenance: Provenance
    failed_ids: list[str]

    def to_render_states(self) -> RenderStates:
        if self.frame != "ITRS" or self.position_unit != "m" or self.velocity_unit != "m/s":
            raise ValueError("RenderStates requires ITRS frame in m and m/s")
        return RenderStates(
            at_utc=self.at_utc,
            frame="ITRS",
            position_unit="m",
            velocity_unit="m/s",
            states=self.states,
            provenance=self.provenance,
        )

    def to_inertial_states(self) -> list[InertialState]:
        if self.frame != "GCRS" or self.position_unit != "km" or self.velocity_unit != "km/s":
            raise ValueError("InertialState requires GCRS frame in km and km/s")
        return [
            InertialState(
                at_utc=self.at_utc,
                frame="GCRS",
                position_unit="km",
                velocity_unit="km/s",
                state=state,
            )
            for state in self.states
        ]


def _epoch_to_jday(epoch_utc: datetime) -> tuple[float, float]:
    utc = require_utc(epoch_utc)
    second = utc.second + utc.microsecond / 1_000_000.0
    jd, fr = jday(utc.year, utc.month, utc.day, utc.hour, utc.minute, second)
    return float(jd), float(fr)


def propagate_objects(
    ids: Sequence[str],
    epoch_utc: datetime,
    snapshot: CatalogSnapshot,
    *,
    frame: Literal["GCRS", "ITRS"] = "GCRS",
) -> PropagatedBatch:
    """Propagate requested catalog object IDs to `epoch_utc` in `GCRS` (km) or `ITRS` (m)."""
    utc = require_utc(epoch_utc)

    if snapshot.mode == "DEMO" and not snapshot.omm_by_id:
        if frame != "ITRS":
            raise ValueError("DEMO snapshot only provides static ITRS render states")
        demo_states = [
            snapshot.demo_states_by_id[obj_id]
            for obj_id in ids
            if obj_id in snapshot.demo_states_by_id
        ]
        provenance = Provenance(
            kind="SYNTHETIC_DEMO",
            mode="DEMO",
            source=", ".join(snapshot.sources) or "ASTRA synthetic fixtures",
            sourceUrl=None,
            sourceFetchedAtUtc=snapshot.fetched_at,
            sourceEpochUtc=snapshot.demo_epoch_utc,
            catalogSnapshotId=snapshot.catalog_snapshot_id,
            modelVersion="synthetic-demo-v1",
            coordinateFrame="ITRS",
            assumptions=["Static synthetic demo positions; no live SGP4 propagation."],
            limitations=["Not real catalog observations; educational demo only."],
            isStale=True,
        )
        return PropagatedBatch(
            at_utc=snapshot.demo_epoch_utc or utc,
            frame="ITRS",
            position_unit="m",
            velocity_unit="m/s",
            states=demo_states,
            provenance=provenance,
            failed_ids=[],
        )

    jd, fr = _epoch_to_jday(utc)
    states: list[CartesianState] = []
    failed_ids: list[str] = []
    min_epoch: datetime | None = None
    any_stale = False

    for obj_id in ids:
        rec = snapshot.omm_by_id.get(obj_id)
        if rec is None:
            failed_ids.append(obj_id)
            continue

        sat = Satrec()
        try:
            omm.initialize(sat, rec.to_omm_dict())
        except (ValueError, KeyError, TypeError):
            failed_ids.append(obj_id)
            continue
        err, r_teme, v_teme = sat.sgp4(jd, fr)
        if err != 0:
            failed_ids.append(obj_id)
            continue

        pos_teme: Vector3 = (float(r_teme[0]), float(r_teme[1]), float(r_teme[2]))
        vel_teme: Vector3 = (float(v_teme[0]), float(v_teme[1]), float(v_teme[2]))

        if frame == "GCRS":
            pos_out, vel_out = teme_to_gcrs(pos_teme, vel_teme, utc)
        else:
            pos_out, vel_out = teme_to_itrs(pos_teme, vel_teme, utc)

        states.append(CartesianState(object_id=obj_id, position=pos_out, velocity=vel_out))
        if min_epoch is None or rec.epoch_utc < min_epoch:
            min_epoch = rec.epoch_utc
        if abs((utc - rec.epoch_utc).total_seconds()) > STALE_AFTER_HOURS * 3600.0:
            any_stale = True

    limitations = [
        "SGP4 mean-element propagation is an estimate, not live telemetry.",
        "Accuracy degrades as propagation time departs from the OMM element epoch.",
    ]
    if failed_ids:
        sample_failed = ", ".join(failed_ids[:5])
        suffix = "…" if len(failed_ids) > 5 else ""
        limitations.append(
            f"{len(failed_ids)} requested object(s) could not be propagated ({sample_failed}{suffix})."
        )

    provenance = Provenance(
        kind="PROPAGATED_ESTIMATE",
        mode=snapshot.mode,
        source=", ".join(snapshot.sources) or "CelesTrak GP",
        sourceUrl="https://celestrak.org/NORAD/elements/",
        sourceFetchedAtUtc=snapshot.fetched_at,
        sourceEpochUtc=min_epoch,
        catalogSnapshotId=snapshot.catalog_snapshot_id,
        modelVersion=MODEL_VERSION,
        coordinateFrame=frame,
        assumptions=[
            "WGS72 gravity constants with TEME-to-target transformation via Astropy.",
        ],
        limitations=limitations,
        isStale=any_stale
        or (datetime.now(UTC) - (snapshot.fetched_at or utc)) > timedelta(hours=STALE_AFTER_HOURS),
    )

    return PropagatedBatch(
        at_utc=utc,
        frame=frame,
        position_unit="km" if frame == "GCRS" else "m",
        velocity_unit="km/s" if frame == "GCRS" else "m/s",
        states=states,
        provenance=provenance,
        failed_ids=failed_ids,
    )
