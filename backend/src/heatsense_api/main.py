"""FastAPI Application factory and entrypoint for HeatSense."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from heatsense_api.api.v1.health import router as health_router
from heatsense_api.config import settings
from heatsense_api.schemas.errors import ErrorDetail, ErrorResponse

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("heatsense_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize services and predictors once."""
    logger.info("Initializing HeatSense API %s in %s mode...", settings.version, settings.env)
    # Model loading state will be hooked up when artifacts exist
    app.state.model_loaded = False
    app.state.predictor = None

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

    # Register API routers
    app.include_router(health_router, prefix=settings.api_prefix)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("heatsense_api.main:app", host=settings.host, port=settings.port, reload=True)
