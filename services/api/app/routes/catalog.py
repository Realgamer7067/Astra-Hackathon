"""Catalog status and policy-compliant refresh routes."""

from __future__ import annotations

from typing import cast
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..models.wire import CatalogRefreshResult, CatalogStatus, ErrorDetail, ErrorEnvelope
from ..storage.catalog_cache import CatalogRepository

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


def _get_repo(request: Request) -> CatalogRepository | None:
    return cast(CatalogRepository | None, getattr(request.app.state, "catalog_repo", None))


def _unavailable_response() -> JSONResponse:
    error = ErrorEnvelope(
        error=ErrorDetail(
            code="CATALOG_UNAVAILABLE",
            message="The catalog repository is not initialized.",
        ),
        request_id=uuid4().hex,
    )
    return JSONResponse(status_code=503, content=error.model_dump(mode="json"))


@router.get(
    "/status",
    response_model=CatalogStatus,
    responses={503: {"model": ErrorEnvelope}},
    operation_id="getCatalogStatus",
)
def catalog_status(request: Request) -> CatalogStatus | JSONResponse:
    repo = _get_repo(request)
    if repo is None:
        return _unavailable_response()
    return repo.snapshot.to_status()


@router.post(
    "/refresh",
    response_model=CatalogRefreshResult,
    responses={503: {"model": ErrorEnvelope}},
    operation_id="refreshCatalog",
)
def catalog_refresh(request: Request) -> CatalogRefreshResult | JSONResponse:
    repo = _get_repo(request)
    if repo is None:
        return _unavailable_response()
    snapshot, refreshed, message = repo.fetch_snapshot()
    return CatalogRefreshResult(
        status=snapshot.to_status(),
        refreshed=refreshed,
        message=message,
    )
