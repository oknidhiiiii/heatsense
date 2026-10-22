"""Model metrics API route."""

from fastapi import APIRouter, HTTPException, status
from heatsense_api.config import settings
from heatsense_api.schemas.weather import ModelMetricsResponse
from heatsense_ml.inference.predictor import HeatSensePredictorBundle

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/metrics", response_model=ModelMetricsResponse)
async def get_model_metrics() -> ModelMetricsResponse:
    """Return held-out evaluation metrics from saved HeatSense model artifacts."""
    artifacts_dir = settings.artifacts_dir / "models" / settings.model_version
    bundle = HeatSensePredictorBundle(artifacts_dir)
    if not bundle.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model evaluation artifacts are not loaded or incomplete.",
        )

    items = bundle.get_all_metrics()
    return ModelMetricsResponse(items=items)  # type: ignore[arg-type]
