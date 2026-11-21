"""Scenario creation, job controls and paginated replay API."""

from datetime import datetime
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..jobs.scenario_jobs import ScenarioJobs
from ..models.scenarios import ScenarioCreated, SimulationSummary
from ..models.wire import DemoBundle, ErrorDetail, ErrorEnvelope, FramePage, Job, ScenarioRequest
from ..physics.scenario import ScenarioError, prepare_scenario

MAX_BODY_BYTES = 1_048_576
router = APIRouter(
    prefix="/api/v1",
    tags=["scenarios"],
    responses={code: {"model": ErrorEnvelope} for code in (404, 409, 413, 415, 422, 429, 503)},
)


def error_response(error: ScenarioError) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(code=error.code, message=error.message), request_id=uuid4().hex
    )
    return JSONResponse(status_code=error.status_code, content=envelope.model_dump(mode="json"))


def jobs(request: Request) -> ScenarioJobs:
    return cast(ScenarioJobs, request.app.state.scenario_jobs)


@router.post(
    "/scenarios",
    status_code=201,
    operation_id="createScenario",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ScenarioRequest"}},
            },
        },
    },
)
async def create_scenario(request: Request) -> ScenarioCreated:
    demo = cast(DemoBundle | None, request.app.state.demo)
    if demo is None:
        raise ScenarioError(503, "DEMO_UNAVAILABLE", "The offline demo data is unavailable.")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise ScenarioError(415, "JSON_REQUIRED", "Use Content-Type: application/json.")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            raise ScenarioError(413, "BODY_TOO_LARGE", "Scenario requests are limited to 1 MiB.")
        body.extend(chunk)
    try:
        scenario = ScenarioRequest.model_validate_json(body)
    except ValidationError as exc:
        issue = exc.errors(include_input=False, include_url=False, include_context=False)[0]
        # Field paths from arbitrary requests may contain user-controlled text.
        message = "Supply two distinct participants and valid bounded simulation settings."
        if issue["type"] == "json_invalid":
            message = "Send valid scenario JSON."
        raise ScenarioError(422, "INVALID_SCENARIO", message) from exc
    return jobs(request).create(prepare_scenario(scenario, demo))


@router.post("/scenarios/{scenario_id}/run", status_code=202, operation_id="startScenario")
def start_scenario(request: Request, scenario_id: str) -> Job:
    return jobs(request).start(scenario_id)


@router.get("/jobs/{job_id}", operation_id="getJob")
def get_job(request: Request, job_id: str) -> Job:
    return jobs(request).status(job_id)


@router.post("/jobs/{job_id}/cancel", status_code=202, operation_id="cancelJob")
def cancel_job(request: Request, job_id: str) -> Job:
    return jobs(request).cancel(job_id)


@router.get("/scenarios/{scenario_id}/simulation", operation_id="getSimulation")
def get_simulation(request: Request, scenario_id: str) -> SimulationSummary:
    return jobs(request).result(scenario_id).summary


@router.get("/scenarios/{scenario_id}/frames", operation_id="getScenarioFrames")
def get_frames(
    request: Request,
    scenario_id: str,
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
    step: Annotated[int | None, Query(ge=1, le=86400)] = None,
    cursor: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
) -> FramePage:
    run = jobs(request).result(scenario_id)
    step_s = step or run.output_step_s
    indices = run.frame_indices(start, end, step_s)
    if cursor and cursor >= len(indices):
        raise ScenarioError(422, "INVALID_CURSOR", "Frame cursor is outside the requested range.")
    return run.frame_page(indices, cursor, step_s)
