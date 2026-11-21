"""Results and report API routes for TASK-005 (Lane D).

Endpoints:
  GET /api/v1/scenarios/{id}/results  — scenario result with exposure data
  GET /api/v1/scenarios/{id}/report   — factual provenance-safe report
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast
from uuid import uuid4

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError

from ..models.wire import (
    DemoBundle,
    ErrorDetail,
    ErrorEnvelope,
    ScenarioRequest,
    ScenarioResult,
)
from ..services.report import build_report

router = APIRouter(prefix="/api/v1/scenarios", tags=["results"])


@dataclass
class ScenarioData:
    """Internal container for resolved scenario result and associated metadata."""

    result: ScenarioResult
    scenario: ScenarioRequest | None = None
    seed: int = 42
    participants: list[dict[str, Any]] = field(default_factory=list)
    scenario_type: str = "FORCED_HYPOTHETICAL"
    modification: dict[str, Any] | None = None


def _get_demo(request: Request) -> DemoBundle | None:
    return cast(DemoBundle | None, getattr(request.app.state, "demo", None))


def _extract_scenario_data(entry: Any, scenario_id: str) -> ScenarioData | None:
    """Extract ScenarioData from a candidate dict, tuple, or object if it matches scenario_id."""
    res_candidate: Any = None
    scen_candidate: Any = None
    job_candidate: Any = None
    seed_candidate: int | None = None
    participants_candidate: list[dict[str, Any]] | None = None
    type_candidate: str | None = None
    mod_candidate: dict[str, Any] | None = None
    matches_id = False

    if isinstance(entry, ScenarioResult):
        if entry.scenario_id == scenario_id:
            res_candidate = entry
            matches_id = True
    elif isinstance(entry, tuple):
        if (
            len(entry) > 0
            and isinstance(entry[0], ScenarioResult)
            and entry[0].scenario_id == scenario_id
        ):
            res_candidate = entry[0]
            matches_id = True
            if len(entry) > 1 and isinstance(entry[1], ScenarioRequest):
                scen_candidate = entry[1]
            if len(entry) > 2 and isinstance(entry[2], int):
                seed_candidate = entry[2]
    elif isinstance(entry, dict):
        # Match checks
        if entry.get("scenario_id") == scenario_id:
            matches_id = True
        res_val = entry.get("result")
        if res_val is not None:
            r_id = getattr(res_val, "scenario_id", None) or (
                res_val.get("scenario_id") if isinstance(res_val, dict) else None
            )
            if r_id == scenario_id:
                matches_id = True
            res_candidate = res_val
        elif "resolved_fragment_count" in entry or "occupancy" in entry:
            res_candidate = entry
            matches_id = True

        scen_val = entry.get("scenario")
        if scen_val is not None:
            s_id = getattr(scen_val, "scenario_id", None) or (
                scen_val.get("scenario_id") if isinstance(scen_val, dict) else None
            )
            if s_id == scenario_id:
                matches_id = True
            scen_candidate = scen_val

        job_val = entry.get("job")
        if job_val is not None:
            j_id = getattr(job_val, "scenario_id", None) or (
                job_val.get("scenario_id") if isinstance(job_val, dict) else None
            )
            if j_id == scenario_id:
                matches_id = True
            job_candidate = job_val

        seed_candidate = entry.get("seed")
        participants_candidate = entry.get("participants")
        type_candidate = entry.get("scenario_type")
        mod_candidate = entry.get("modification")
    else:
        # Object with attributes
        r_id = getattr(entry, "scenario_id", None)
        if r_id == scenario_id:
            matches_id = True
        res_val = getattr(entry, "result", None)
        if res_val is not None:
            if getattr(res_val, "scenario_id", None) == scenario_id:
                matches_id = True
            res_candidate = res_val
        scen_val = getattr(entry, "scenario", None)
        if scen_val is not None:
            if getattr(scen_val, "scenario_id", None) == scenario_id:
                matches_id = True
            scen_candidate = scen_val
        job_val = getattr(entry, "job", None)
        if job_val is not None:
            if getattr(job_val, "scenario_id", None) == scenario_id:
                matches_id = True
            job_candidate = job_val

        seed_candidate = getattr(entry, "seed", None)
        participants_candidate = getattr(entry, "participants", None)
        type_candidate = getattr(entry, "scenario_type", None)
        mod_candidate = getattr(entry, "modification", None)

    if not matches_id or res_candidate is None:
        return None

    # Validate result to ScenarioResult
    if isinstance(res_candidate, ScenarioResult):
        final_result = res_candidate
    elif isinstance(res_candidate, dict):
        final_result = ScenarioResult.model_validate(res_candidate)
    else:
        return None

    # Validate scenario
    final_scenario: ScenarioRequest | None = None
    if isinstance(scen_candidate, ScenarioRequest):
        final_scenario = scen_candidate
    elif isinstance(scen_candidate, dict):
        try:
            final_scenario = ScenarioRequest.model_validate(scen_candidate)
        except (ValueError, TypeError, ValidationError):
            final_scenario = None

    # Resolve seed: candidate -> job -> scenario -> result -> default(42)
    final_seed = 42
    if seed_candidate is not None:
        final_seed = int(seed_candidate)
    elif job_candidate is not None:
        j_seed = getattr(job_candidate, "seed", None) or (
            job_candidate.get("seed") if isinstance(job_candidate, dict) else None
        )
        if j_seed is not None:
            final_seed = int(j_seed)
    elif final_scenario is not None:
        final_seed = final_scenario.simulation.seed
    elif hasattr(res_candidate, "seed") and res_candidate.seed is not None:
        final_seed = int(res_candidate.seed)

    # Resolve participants
    final_participants: list[dict[str, Any]] = []
    if participants_candidate is not None:
        final_participants = list(participants_candidate)
    elif final_scenario is not None:
        final_participants = [
            {
                "object_id": p.object_id,
                "assumed_mass_kg": p.assumed_mass_kg,
                "assumed_radius_m": p.assumed_radius_m,
            }
            for p in final_scenario.participants
        ]

    # Resolve scenario_type
    final_type = "FORCED_HYPOTHETICAL"
    if type_candidate is not None:
        final_type = str(type_candidate)
    elif final_scenario is not None:
        final_type = str(final_scenario.type)

    # Resolve modification
    final_mod = mod_candidate
    if final_mod is None and final_result.modification is not None:
        final_mod = final_result.modification.model_dump(mode="json")

    return ScenarioData(
        result=final_result,
        scenario=final_scenario,
        seed=final_seed,
        participants=final_participants,
        scenario_type=final_type,
        modification=final_mod,
    )


def _get_scenario_data(request: Request, scenario_id: str) -> ScenarioData | None:
    """Retrieve result and scenario data by scenario_id.

    Checks:
      1. app.state.runs (dictionary or list of runs)
      2. app.state.scenario_jobs (TASK-003 scenario jobs store)
      3. app.state.jobs (job records store)
      4. app.state.demo (offline demo fixture fallback)
    """
    # 1. Search app.state.runs and app.state.scenario_jobs
    for store_name in ("runs", "scenario_jobs", "jobs"):
        store = getattr(request.app.state, store_name, None)
        if not store:
            continue
        if isinstance(store, dict):
            # Direct key lookup
            if scenario_id in store:
                data = _extract_scenario_data(store[scenario_id], scenario_id)
                if data is not None:
                    return data
            # Value iteration lookup (e.g. keyed by job_id instead of scenario_id)
            for entry in store.values():
                data = _extract_scenario_data(entry, scenario_id)
                if data is not None:
                    return data
        elif isinstance(store, list):
            for entry in store:
                data = _extract_scenario_data(entry, scenario_id)
                if data is not None:
                    return data

    # 2. Check offline demo fixture fallback
    demo = _get_demo(request)
    if demo is not None and (
        demo.result.scenario_id == scenario_id or demo.job.scenario_id == scenario_id
    ):
        mod_dict = None
        if demo.result.modification is not None:
            mod_dict = demo.result.modification.model_dump(mode="json")
        return ScenarioData(
            result=demo.result,
            scenario=demo.scenario,
            seed=demo.scenario.simulation.seed,
            participants=[
                {
                    "object_id": p.object_id,
                    "assumed_mass_kg": p.assumed_mass_kg,
                    "assumed_radius_m": p.assumed_radius_m,
                }
                for p in demo.scenario.participants
            ],
            scenario_type=demo.scenario.type,
            modification=mod_dict,
        )

    return None


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
    data = _get_scenario_data(request, scenario_id)
    if data is not None:
        return data.result

    demo = _get_demo(request)
    if demo is None:
        return _error_response(
            "DEMO_UNAVAILABLE",
            "The offline demo data is unavailable.",
            status=503,
        )
    return _error_response(
        "SCENARIO_NOT_FOUND",
        f"No results found for scenario '{scenario_id}'.",
    )


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
    data = _get_scenario_data(request, scenario_id)
    if data is None:
        demo = _get_demo(request)
        if demo is None:
            return _error_response(
                "DEMO_UNAVAILABLE",
                "The offline demo data is unavailable.",
                status=503,
            )
        return _error_response(
            "SCENARIO_NOT_FOUND",
            f"No results found for scenario '{scenario_id}'.",
        )

    result = data.result

    # Build the report
    report = build_report(
        scenario_id=scenario_id,
        scenario_type=data.scenario_type,
        seed=data.seed,
        participants=data.participants,
        modification=data.modification,
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
