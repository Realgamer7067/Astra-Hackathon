"""Catalog object search, detail, and propagated state routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal, cast
from uuid import uuid4

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ..models.wire import (
    CatalogStatus,
    Epoch,
    ErrorDetail,
    ErrorEnvelope,
    ObjectDetail,
    ObjectKind,
    ObjectSearchPage,
    Provenance,
    RenderStates,
)
from ..orbit.sgp4_service import propagate_objects
from ..storage.catalog_cache import STALE_AFTER_HOURS, CatalogRepository

router = APIRouter(prefix="/api/v1", tags=["objects"])


def _get_repo(request: Request) -> CatalogRepository | None:
    return cast(CatalogRepository | None, getattr(request.app.state, "catalog_repo", None))


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(code=code, message=message),
        request_id=uuid4().hex,
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))


def _catalog_provenance(status: CatalogStatus) -> Provenance:
    if status.mode == "DEMO":
        return Provenance(
            kind="SYNTHETIC_DEMO",
            mode="DEMO",
            source=", ".join(status.sources) or "ASTRA synthetic fixtures",
            sourceUrl=None,
            sourceFetchedAtUtc=status.fetched_at,
            sourceEpochUtc=status.element_epoch_max,
            catalogSnapshotId=status.catalog_snapshot_id,
            modelVersion=None,
            coordinateFrame=None,
            assumptions=["Synthetic demo catalog; not real-world observations."],
            limitations=["Limited 12-object fixture dataset."],
            isStale=True,
        )
    is_stale = "STALE_ELEMENTS" in status.warning_codes
    return Provenance(
        kind="CATALOG_OBSERVATION",
        mode=status.mode,
        source=", ".join(status.sources) or "CelesTrak GP + SATCAT",
        sourceUrl="https://celestrak.org/NORAD/elements/",
        sourceFetchedAtUtc=status.fetched_at,
        sourceEpochUtc=status.element_epoch_max,
        catalogSnapshotId=status.catalog_snapshot_id,
        modelVersion=None,
        coordinateFrame="TEME",
        assumptions=["NORAD catalog IDs preserved as full strings; unknown mass/radius."],
        limitations=[
            "GP mean elements are not live telemetry.",
            "Catalog coverage depends on ingested CelesTrak groups.",
        ],
        isStale=is_stale,
    )


@router.get(
    "/objects",
    response_model=ObjectSearchPage,
    responses={422: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
    operation_id="searchObjects",
)
def search_objects(
    request: Request,
    query: Annotated[str | None, Query(max_length=120)] = None,
    kind: Annotated[ObjectKind | None, Query()] = None,
    operational_status: Annotated[Literal["ACTIVE", "INACTIVE", "UNKNOWN"] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query()] = None,
) -> ObjectSearchPage | JSONResponse:
    repo = _get_repo(request)
    if repo is None:
        return _error_response(503, "CATALOG_UNAVAILABLE", "Catalog repository is unavailable.")
    try:
        items, next_cursor, total = repo.search_objects(
            query=query,
            kind=kind,
            operational_status=operational_status,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        return _error_response(422, "INVALID_CURSOR", str(exc))

    now = datetime.now(UTC)
    status = repo.snapshot.to_status(now_utc=now)
    return ObjectSearchPage(
        generated_at_utc=now,
        items=items,
        next_cursor=next_cursor,
        total=total,
        catalog_snapshot_id=status.catalog_snapshot_id,
        provenance=_catalog_provenance(status),
    )


@router.get(
    "/objects/{object_id}",
    response_model=ObjectDetail,
    responses={404: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
    operation_id="getObjectDetail",
)
def get_object_detail(request: Request, object_id: str) -> ObjectDetail | JSONResponse:
    repo = _get_repo(request)
    if repo is None:
        return _error_response(503, "CATALOG_UNAVAILABLE", "Catalog repository is unavailable.")
    now = datetime.now(UTC)
    found = repo.get_object(object_id, now_utc=now)
    if found is None:
        return _error_response(404, "OBJECT_NOT_FOUND", f"Object {object_id} was not found.")
    obj, satcat, staleness_hours, is_stale = found
    status = repo.snapshot.to_status(now_utc=now)
    provenance = _catalog_provenance(status)
    if staleness_hours is not None and staleness_hours > STALE_AFTER_HOURS:
        provenance.is_stale = True
    return ObjectDetail(
        generated_at_utc=now,
        object=obj,
        satcat=satcat,
        staleness_hours=staleness_hours,
        is_stale=is_stale,
        provenance=provenance,
    )


@router.get(
    "/states",
    response_model=RenderStates,
    responses={422: {"model": ErrorEnvelope}, 503: {"model": ErrorEnvelope}},
    operation_id="getRenderStates",
)
def get_render_states(
    request: Request,
    at: Annotated[Epoch | None, Query()] = None,
    scope: Annotated[Literal["visible", "selected", "preset"], Query()] = "visible",
    ids: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> RenderStates | JSONResponse:
    repo = _get_repo(request)
    if repo is None:
        return _error_response(503, "CATALOG_UNAVAILABLE", "Catalog repository is unavailable.")

    snap = repo.snapshot
    target_epoch = at or snap.demo_epoch_utc or datetime.now(UTC)

    if scope == "selected":
        raw_ids: list[str] = []
        for item in ids or []:
            raw_ids.extend(part.strip() for part in item.split(",") if part.strip())
        target_ids = raw_ids[:limit]
    else:
        target_ids = [obj.id for obj in snap.objects[:limit]]

    batch = propagate_objects(target_ids, target_epoch, snap, frame="ITRS")
    return batch.to_render_states()
