"""Persistent catalog snapshot cache and LIVE/CACHED/DEMO state management."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ..connectors.celestrak import (
    MIN_REFRESH_INTERVAL_SECONDS,
    CelesTrakConnector,
    CelesTrakError,
    CelesTrakFetchResult,
    RawOmmRecord,
    map_object_kind,
    map_operational_status,
    parse_utc_epoch,
)
from ..models.wire import (
    CartesianState,
    CatalogObject,
    CatalogStatus,
    DemoBundle,
    ObjectKind,
    OrbitDescriptor,
    SatcatMetadata,
    SourceMode,
)

STALE_AFTER_HOURS = 24.0


@dataclass(frozen=True)
class CatalogSnapshot:
    """Immutable normalized catalog snapshot with provenance metadata."""

    catalog_snapshot_id: str
    mode: SourceMode
    sources: list[str]
    fetched_at: datetime | None
    objects: list[CatalogObject]
    omm_by_id: dict[str, RawOmmRecord] = field(default_factory=dict)
    satcat_by_id: dict[str, SatcatMetadata] = field(default_factory=dict)
    demo_states_by_id: dict[str, CartesianState] = field(default_factory=dict)
    demo_epoch_utc: datetime | None = None
    warning_codes: list[str] = field(default_factory=list)
    decayed_filtered_count: int = 0

    @property
    def objects_by_id(self) -> dict[str, CatalogObject]:
        return {obj.id: obj for obj in self.objects}

    def element_epoch_bounds(self) -> tuple[datetime | None, datetime | None]:
        epochs = [
            obj.element_epoch_utc for obj in self.objects if obj.element_epoch_utc is not None
        ]
        if not epochs:
            return None, None
        return min(epochs), max(epochs)

    def to_status(self, *, now_utc: datetime | None = None) -> CatalogStatus:
        now = (now_utc or datetime.now(UTC)).astimezone(UTC)
        ep_min, ep_max = self.element_epoch_bounds()
        warnings = list(self.warning_codes)
        if (
            ep_max is not None
            and (now - ep_max) > timedelta(hours=STALE_AFTER_HOURS)
            and "STALE_ELEMENTS" not in warnings
        ):
            warnings.append("STALE_ELEMENTS")
        displayable = len(self.demo_states_by_id) if self.mode == "DEMO" else len(self.omm_by_id)
        return CatalogStatus(
            mode=self.mode,
            sources=list(self.sources),
            fetched_at=self.fetched_at,
            element_epoch_min=ep_min,
            element_epoch_max=ep_max,
            records=len(self.objects),
            displayable_count=displayable,
            catalog_snapshot_id=self.catalog_snapshot_id,
            warning_codes=warnings,
        )


def _compute_snapshot_id(payload: list[dict[str, object]]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def build_snapshot_from_fetch(
    result: CelesTrakFetchResult, *, mode: SourceMode = "LIVE"
) -> CatalogSnapshot:
    """Construct an immutable CatalogSnapshot from a CelesTrakFetchResult."""
    hash_payload = [rec.to_omm_dict() for rec in result.omm_records]
    snapshot_id = _compute_snapshot_id(hash_payload)

    objects: list[CatalogObject] = []
    omm_by_id: dict[str, RawOmmRecord] = {}
    for rec in result.omm_records:
        obj_id = f"NORAD:{rec.norad_cat_id}"
        sat = result.satcat_by_id.get(rec.norad_cat_id)
        kind: ObjectKind = map_object_kind(sat.object_type_raw) if sat else "UNKNOWN"
        op_status = map_operational_status(sat.operational_status_code) if sat else "UNKNOWN"
        objects.append(
            CatalogObject(
                id=obj_id,
                name=rec.object_name,
                kind=kind,
                operational_status=op_status,
                state_source="CELESTRAK_GP",
                element_epoch_utc=rec.epoch_utc,
                catalog_snapshot_id=snapshot_id,
                mass_kg=None,
                effective_radius_m=None,
                physical_properties_basis="UNAVAILABLE",
                orbit=OrbitDescriptor(format="OMM_CSV", theory="SGP4", frame="TEME"),
            )
        )
        omm_by_id[obj_id] = rec

    warnings = list(result.warning_codes)
    if mode == "CACHED" and "CACHED_SNAPSHOT" not in warnings:
        warnings.append("CACHED_SNAPSHOT")

    return CatalogSnapshot(
        catalog_snapshot_id=snapshot_id,
        mode=mode,
        sources=result.sources,
        fetched_at=result.fetched_at_utc,
        objects=objects,
        omm_by_id=omm_by_id,
        satcat_by_id={f"NORAD:{k}": v for k, v in result.satcat_by_id.items()},
        warning_codes=warnings,
        decayed_filtered_count=result.decayed_filtered_count,
    )


def build_snapshot_from_demo(bundle: DemoBundle) -> CatalogSnapshot:
    """Construct an immutable DEMO CatalogSnapshot from the offline DemoBundle."""
    return CatalogSnapshot(
        catalog_snapshot_id=bundle.catalog.catalog_snapshot_id,
        mode="DEMO",
        sources=list(bundle.catalog.sources),
        fetched_at=bundle.catalog.fetched_at,
        objects=list(bundle.objects),
        demo_states_by_id={s.object_id: s for s in bundle.states.states},
        demo_epoch_utc=bundle.states.at_utc,
        warning_codes=list(bundle.catalog.warning_codes),
    )


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode("ascii")).decode("ascii")


def decode_cursor(cursor: str | None) -> int:
    if cursor is None or cursor == "":
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("ascii")
        offset = int(raw)
    except Exception as exc:
        raise ValueError("invalid pagination cursor") from exc
    if offset < 0:
        raise ValueError("invalid pagination cursor")
    return offset


class CatalogRepository:
    """Manages persistent last-good catalog cache, offline demo fallback, and search."""

    def __init__(
        self,
        *,
        cache_path: Path,
        demo_path: Path,
        connector: CelesTrakConnector | None = None,
    ) -> None:
        self.cache_path = cache_path
        self.demo_path = demo_path
        self.connector = connector or CelesTrakConnector()
        self._snapshot: CatalogSnapshot | None = None

    @property
    def snapshot(self) -> CatalogSnapshot:
        if self._snapshot is None:
            return self.load_startup()
        return self._snapshot

    def load_startup(self) -> CatalogSnapshot:
        """Load persistent cache if valid, else offline demo fixture without network."""
        cached = self._read_cache()
        if cached is not None:
            self._snapshot = cached
            return cached

        if self.demo_path.exists():
            bundle = DemoBundle.model_validate_json(self.demo_path.read_text(encoding="utf-8"))
            demo_snap = build_snapshot_from_demo(bundle)
            self._snapshot = demo_snap
            return demo_snap

        raise RuntimeError("Neither cached catalog nor offline demo fixture is available")

    def _read_cache(self) -> CatalogSnapshot | None:
        if not self.cache_path.exists():
            return None
        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            fetched_at = parse_utc_epoch(raw["fetched_at_utc"])
            omm_records = [
                RawOmmRecord(
                    norad_cat_id=str(item["norad_cat_id"]),
                    object_name=str(item["object_name"]),
                    object_id=str(item.get("object_id", "")),
                    epoch_utc=parse_utc_epoch(str(item["epoch_utc"])),
                    mean_motion=float(item["mean_motion"]),
                    eccentricity=float(item["eccentricity"]),
                    inclination=float(item["inclination"]),
                    ra_of_asc_node=float(item["ra_of_asc_node"]),
                    arg_of_pericenter=float(item["arg_of_pericenter"]),
                    mean_anomaly=float(item["mean_anomaly"]),
                    bstar=float(item["bstar"]),
                    mean_motion_dot=float(item["mean_motion_dot"]),
                    mean_motion_ddot=float(item["mean_motion_ddot"]),
                    ephemeris_type=int(item["ephemeris_type"]),
                    classification_type=str(item["classification_type"]),
                    element_set_no=int(item["element_set_no"]),
                    rev_at_epoch=int(item["rev_at_epoch"]),
                    source_group=str(item.get("source_group", "CACHED")),
                )
                for item in raw["omm_records"]
            ]
            satcat_by_id = {
                str(k): SatcatMetadata.model_validate(v)
                for k, v in raw.get("satcat_by_id", {}).items()
            }
            fetch_result = CelesTrakFetchResult(
                fetched_at_utc=fetched_at,
                sources=list(raw.get("sources", ["CelesTrak GP (cached)"])),
                omm_records=omm_records,
                satcat_by_id=satcat_by_id,
                warning_codes=list(raw.get("warning_codes", [])),
                decayed_filtered_count=int(raw.get("decayed_filtered_count", 0)),
            )
            return build_snapshot_from_fetch(fetch_result, mode="CACHED")
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _write_cache(self, result: CelesTrakFetchResult) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched_at_utc": result.fetched_at_utc.isoformat(),
            "sources": result.sources,
            "warning_codes": result.warning_codes,
            "decayed_filtered_count": result.decayed_filtered_count,
            "omm_records": [
                {
                    "norad_cat_id": rec.norad_cat_id,
                    "object_name": rec.object_name,
                    "object_id": rec.object_id,
                    "epoch_utc": rec.epoch_utc.isoformat(),
                    "mean_motion": rec.mean_motion,
                    "eccentricity": rec.eccentricity,
                    "inclination": rec.inclination,
                    "ra_of_asc_node": rec.ra_of_asc_node,
                    "arg_of_pericenter": rec.arg_of_pericenter,
                    "mean_anomaly": rec.mean_anomaly,
                    "bstar": rec.bstar,
                    "mean_motion_dot": rec.mean_motion_dot,
                    "mean_motion_ddot": rec.mean_motion_ddot,
                    "ephemeris_type": rec.ephemeris_type,
                    "classification_type": rec.classification_type,
                    "element_set_no": rec.element_set_no,
                    "rev_at_epoch": rec.rev_at_epoch,
                    "source_group": rec.source_group,
                }
                for rec in result.omm_records
            ],
            "satcat_by_id": {k: v.model_dump(mode="json") for k, v in result.satcat_by_id.items()},
        }
        self.cache_path.write_text(json.dumps(payload), encoding="utf-8")

    def fetch_snapshot(
        self, *, now_utc: datetime | None = None
    ) -> tuple[CatalogSnapshot, bool, str]:
        """Refresh from CelesTrak respecting 2-hour policy, falling back cleanly on failure."""
        now = (now_utc or datetime.now(UTC)).astimezone(UTC)
        current = self.snapshot

        if (
            current.mode in {"LIVE", "CACHED"}
            and current.fetched_at is not None
            and (now - current.fetched_at).total_seconds() < MIN_REFRESH_INTERVAL_SECONDS
        ):
            remaining_min = int(
                (MIN_REFRESH_INTERVAL_SECONDS - (now - current.fetched_at).total_seconds()) // 60
            )
            return (
                current,
                False,
                f"CelesTrak usage policy limits GP downloads to once every 2 hours (~{remaining_min} min remaining).",
            )

        try:
            fetched = self.connector.fetch(now_utc=now)
        except CelesTrakError as exc:
            warnings = list(current.warning_codes)
            if "PROVIDER_UNAVAILABLE" not in warnings:
                warnings.append("PROVIDER_UNAVAILABLE")
            fallback_mode: SourceMode = "CACHED" if current.mode in {"LIVE", "CACHED"} else "DEMO"
            fallback = CatalogSnapshot(
                catalog_snapshot_id=current.catalog_snapshot_id,
                mode=fallback_mode,
                sources=current.sources,
                fetched_at=current.fetched_at,
                objects=current.objects,
                omm_by_id=current.omm_by_id,
                satcat_by_id=current.satcat_by_id,
                demo_states_by_id=current.demo_states_by_id,
                demo_epoch_utc=current.demo_epoch_utc,
                warning_codes=warnings,
                decayed_filtered_count=current.decayed_filtered_count,
            )
            self._snapshot = fallback
            return (
                fallback,
                False,
                f"Provider unavailable ({exc}); retaining {fallback_mode} snapshot.",
            )

        self._write_cache(fetched)
        live_snap = build_snapshot_from_fetch(fetched, mode="LIVE")
        self._snapshot = live_snap
        return live_snap, True, f"Fetched {len(live_snap.objects)} objects from CelesTrak."

    def search_objects(
        self,
        *,
        query: str | None = None,
        kind: ObjectKind | None = None,
        operational_status: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[CatalogObject], str | None, int]:
        offset = decode_cursor(cursor)
        q = (query or "").strip().lower()

        filtered = [
            obj
            for obj in self.snapshot.objects
            if (not q or q in obj.name.lower() or q in obj.id.lower())
            and (kind is None or obj.kind == kind)
            and (operational_status is None or obj.operational_status == operational_status)
        ]
        total = len(filtered)
        page = filtered[offset : offset + limit]
        next_cursor = encode_cursor(offset + limit) if (offset + limit) < total else None
        return page, next_cursor, total

    def get_object(
        self, object_id: str, *, now_utc: datetime | None = None
    ) -> tuple[CatalogObject, SatcatMetadata | None, float | None, bool] | None:
        snap = self.snapshot
        obj = snap.objects_by_id.get(object_id)
        if obj is None:
            return None
        sat = snap.satcat_by_id.get(object_id)
        staleness_hours: float | None = None
        is_stale = snap.mode == "DEMO"
        if obj.element_epoch_utc is not None:
            now = (now_utc or datetime.now(UTC)).astimezone(UTC)
            staleness_hours = max(0.0, (now - obj.element_epoch_utc).total_seconds() / 3600.0)
            is_stale = staleness_hours > STALE_AFTER_HOURS
        return obj, sat, staleness_hours, is_stale
