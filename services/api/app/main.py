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

from .connectors.celestrak import CelesTrakConnector
from .models.wire import DemoBundle, ErrorDetail, ErrorEnvelope, Health
from .routes import catalog as catalog_routes
from .routes import objects as object_routes
from .storage.catalog_cache import CatalogRepository

ROOT = Path(__file__).resolve().parents[3]
DEMO_FILE = ROOT / "data/fixtures/demo.json"
DEFAULT_CACHE_FILE = ROOT / ".cache/astra/catalog_snapshot.json"
VERSION = "0.1.0"
logger = logging.getLogger(__name__)


def create_app(
    fixture_path: Path = DEMO_FILE,
    cache_path: Path | None = None,
    connector: CelesTrakConnector | None = None,
) -> FastAPI:
    resolved_cache = (
        cache_path
        if cache_path is not None
        else (
            DEFAULT_CACHE_FILE
            if fixture_path == DEMO_FILE
            else fixture_path.parent / "catalog_cache.json"
        )
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            app.state.demo = DemoBundle.model_validate_json(fixture_path.read_bytes())
        except (OSError, ValidationError):
            logger.warning("Offline demo fixture could not be loaded")
            app.state.demo = None
        if not hasattr(app.state, "runs"):
            app.state.runs = {}

        repo = CatalogRepository(
            cache_path=resolved_cache,
            demo_path=fixture_path,
            connector=connector,
        )
        try:
            repo.load_startup()
            app.state.catalog_repo = repo
        except RuntimeError:
            logger.warning("Catalog repository could not load cache or demo fixture")
            app.state.catalog_repo = None
        yield

    api = FastAPI(title="ASTRA Orbital Collision Lab", version=VERSION, lifespan=lifespan)
    api.include_router(catalog_routes.router)
    api.include_router(object_routes.router)

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

    # --- Lane D: results & report routes (TASK-005) ---
    from .routes.results import router as results_router

    api.include_router(results_router)

    return api


app = create_app()
