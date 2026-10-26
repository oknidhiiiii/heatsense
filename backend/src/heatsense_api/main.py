"""FastAPI Application factory and entrypoint for HeatSense."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from heatsense_api.middleware.etag import ETagMiddleware

from heatsense_api.api.v1.health import router as health_router
from heatsense_api.api.v1.locations import router as locations_router
from heatsense_api.api.v1.models import router as models_router
from heatsense_api.api.v1.weather import router as weather_router
from heatsense_api.config import settings
from heatsense_api.schemas.errors import ErrorDetail, ErrorResponse
from heatsense_api.services.prediction_service import PredictionService

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("heatsense_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize prediction service and model bundle once."""
    logger.info("Initializing HeatSense API %s in %s mode...", settings.version, settings.env)

    # Initialize PredictionService and load models once on startup
    try:
        pred_service = PredictionService()
        app.state.prediction_service = pred_service
        app.state.model_loaded = pred_service.is_ready
        if pred_service.is_ready:
            logger.info("HeatSense ML prediction service successfully loaded models for v1 (24h, 48h).")
        else:
            logger.warning("PredictionService initialized, but model artifacts were not fully loaded.")
    except Exception as e:
        logger.error("Failed to initialize PredictionService on startup: %s", e)
        app.state.prediction_service = None
        app.state.model_loaded = False

    yield

    logger.info("Shutting down HeatSense API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="HeatSense API",
        version=settings.version,
        description="Predictive Analytics for Heat Risk API (India Focus with Global Architecture)",
        lifespan=lifespan,
    )

    # ETag and 304 conditional caching
    app.add_middleware(ETagMiddleware)

    # Dynamic payload compression for responses >= 1000 bytes
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Standard error handlers matching 06_API_CONTRACTS.md
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=f"HTTP_{exc.status_code}",
                    message=str(exc.detail),
                    request_id=request.headers.get("x-request-id"),
                )
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message="Invalid request parameters or payload.",
                    request_id=request.headers.get("x-request-id"),
                    details={"errors": exc.errors()},
                )
            ).model_dump(),
        )

    # Register API routers matching 06_API_CONTRACTS.md
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(locations_router, prefix=settings.api_prefix)
    app.include_router(models_router, prefix=settings.api_prefix)
    app.include_router(weather_router, prefix=settings.api_prefix)

    # Mount static frontend SPA if distribution exists (enables single-container online deployment)
    import os
    from fastapi.staticfiles import StaticFiles

    for dist_candidate in ["frontend_dist", "/app/frontend_dist", "frontend/dist"]:
        if os.path.isdir(dist_candidate):
            app.mount("/", StaticFiles(directory=dist_candidate, html=True), name="frontend-static")
            logger.info("Serving static frontend SPA from %s", dist_candidate)
            break

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("heatsense_api.main:app", host=settings.host, port=settings.port, reload=True)
