"""Run the local API and serve the validated, offline demo snapshot."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .models.wire import DemoBundle, ErrorDetail, ErrorEnvelope, Health

ROOT = Path(__file__).resolve().parents[3]
DEMO_FILE = ROOT / "data/fixtures/demo.json"
VERSION = "0.1.0"
logger = logging.getLogger(__name__)


def create_app(fixture_path: Path = DEMO_FILE) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            app.state.demo = DemoBundle.model_validate_json(fixture_path.read_bytes())
        except (OSError, ValidationError):
            logger.warning("Offline demo fixture could not be loaded")
            app.state.demo = None
        yield

    api = FastAPI(title="ASTRA Orbital Collision Lab", version=VERSION, lifespan=lifespan)

    @api.get("/health", operation_id="getHealth")
    def health(request: Request) -> Health:
        ready = request.app.state.demo is not None
        return Health(
            status="ok" if ready else "degraded",
            version=VERSION,
            cache_ready=ready,
            simulation_ready=False,
        )

    @api.get(
        "/api/v1/demo",
        response_model=DemoBundle,
        responses={503: {"model": ErrorEnvelope}},
        operation_id="getDemo",
    )
    def demo(request: Request) -> DemoBundle | JSONResponse:
        bundle = cast(DemoBundle | None, request.app.state.demo)
        if bundle is not None:
            return bundle
        error = ErrorEnvelope(
            error=ErrorDetail(
                code="DEMO_UNAVAILABLE", message="The offline demo data is unavailable."
            ),
            request_id=uuid4().hex,
        )
        return JSONResponse(status_code=503, content=error.model_dump(mode="json"))

    return api


app = create_app()
