"""Health endpoint route."""

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from heatsense_api.config import settings
from heatsense_api.schemas.health import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    """Return system operational status and model readiness."""
    # Check if model predictor is loaded in app state
    model_loaded = getattr(request.app.state, "model_loaded", False)

    return HealthResponse(
        status="ok",
        version=settings.version,
        model_loaded=model_loaded,
        supported_regions=settings.supported_regions,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
