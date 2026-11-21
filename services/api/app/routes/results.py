"""Results and report API routes for TASK-005 (Lane D).

Endpoints:
  GET /api/v1/scenarios/{id}/results  — scenario result with exposure data
  GET /api/v1/scenarios/{id}/report   — factual provenance-safe report
"""

from __future__ import annotations

from typing import cast
from uuid import uuid4

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from ..models.wire import (
    DemoBundle,
    ErrorDetail,
    ErrorEnvelope,
    ScenarioResult,
)
from ..services.report import build_report

router = APIRouter(prefix="/api/v1/scenarios", tags=["results"])


def _get_demo(request: Request) -> DemoBundle | None:
    return cast(DemoBundle | None, getattr(request.app.state, "demo", None))


def _error_response(code: str, message: str, status: int = 404) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(code=code, message=message),
        request_id=uuid4().hex,
    )
    return JSONResponse(status_code=status, content=envelope.model_dump(mode="json"))


@router.get(
    "/{scenario_id}/results",
    response_model=ScenarioResult,
    responses={
        404: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
    },
    operation_id="getScenarioResults",
)
def get_results(request: Request, scenario_id: str) -> ScenarioResult | JSONResponse:
    """Return the scenario result including occupancy, encounters, and entry crossings."""
    demo = _get_demo(request)
    if demo is None:
        return _error_response(
            "DEMO_UNAVAILABLE",
            "The offline demo data is unavailable.",
            status=503,
        )
    if demo.result.scenario_id != scenario_id:
        return _error_response(
            "SCENARIO_NOT_FOUND",
            f"No results found for scenario '{scenario_id}'.",
        )
    return demo.result


@router.get(
    "/{scenario_id}/report",
    responses={
        200: {"content": {"application/json": {}, "text/markdown": {}}},
        404: {"model": ErrorEnvelope},
        503: {"model": ErrorEnvelope},
    },
    operation_id="getScenarioReport",
)
def get_report(
    request: Request,
    scenario_id: str,
    format: str = Query("json", pattern="^(json|markdown)$"),
) -> Response:
    """Return a factual provenance-preserving report of the scenario.

    Supports ``format=json`` (default) and ``format=markdown``.
    Hypothetical labels are preserved in all output formats.
    """
    demo = _get_demo(request)
    if demo is None:
        return _error_response(
            "DEMO_UNAVAILABLE",
            "The offline demo data is unavailable.",
            status=503,
        )
    if demo.result.scenario_id != scenario_id:
        return _error_response(
            "SCENARIO_NOT_FOUND",
            f"No results found for scenario '{scenario_id}'.",
        )

    result = demo.result
    scenario = demo.scenario

    # Build participants list from scenario
    participants = [
        {
            "object_id": p.object_id,
            "assumed_mass_kg": p.assumed_mass_kg,
            "assumed_radius_m": p.assumed_radius_m,
        }
        for p in scenario.participants
    ]

    # Serialize modification if present
    modification_dict = None
    if result.modification is not None:
        modification_dict = result.modification.model_dump(mode="json")

    # Build the report
    report = build_report(
        scenario_id=scenario_id,
        scenario_type=scenario.type,
        seed=scenario.simulation.seed,
        participants=participants,
        modification=modification_dict,
        occupancy=[b.model_dump(mode="json") for b in result.occupancy],
        encounters=[e.model_dump(mode="json") for e in result.encounters],
        entry_crossings=[c.model_dump(mode="json") for c in result.entry_crossings],
        fragment_count=result.resolved_fragment_count,
        unresolved_mass_kg=result.unresolved_mass_kg,
        provenance=result.provenance.model_dump(mode="json", by_alias=True),
    )

    if format == "markdown":
        return PlainTextResponse(
            content=report.to_markdown(),
            media_type="text/markdown",
        )

    return JSONResponse(content=report.to_dict())
