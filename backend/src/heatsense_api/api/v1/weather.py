"""Weather, predictions, and map grid API routes."""

from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from starlette.concurrency import run_in_threadpool
from heatsense_api.config import settings
from heatsense_api.repositories.weather_grid import WeatherGridRepository
from heatsense_api.schemas.weather import (
    HistoricalResponse,
    MapGridResponse,
    PredictionResponse,
)
from heatsense_api.services.cache import cache

router = APIRouter(tags=["Weather & Predictions"])
weather_repo = WeatherGridRepository()


def parse_and_validate_bbox(bbox_str: Optional[str]) -> Optional[List[float]]:
    """Parse comma-separated bbox string and validate spatial limits."""
    if not bbox_str:
        return None
    try:
        parts = [float(p.strip()) for p in bbox_str.split(",")]
        if len(parts) != 4:
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bbox format. Expected 'min_lat,min_lon,max_lat,max_lon'",
        ) from None

    min_lat, min_lon, max_lat, max_lon = parts
    if min_lat >= max_lat or min_lon >= max_lon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bbox bounds: min coordinates must be strictly less than max coordinates.",
        )

    area = (max_lat - min_lat) * (max_lon - min_lon)
    if area > settings.max_grid_area_deg2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested grid bounding box area ({area:.1f} deg²) exceeds maximum allowed ({settings.max_grid_area_deg2} deg²).",
        )

    return parts


@router.get("/history", response_model=HistoricalResponse)
async def get_history(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=360.0, description="Longitude"),
    start: str = Query(..., description="Start ISO-8601 UTC timestamp"),
    end: str = Query(..., description="End ISO-8601 UTC timestamp"),
    interval: Literal["hourly", "daily"] = Query("hourly", description="Sampling interval"),
) -> HistoricalResponse:
    """Retrieve historical temperature time-series observations for nearest grid cell."""
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start timestamp must be earlier than or equal to end timestamp.",
        )

    cache_key = f"hist:{lat:.2f}:{lon:.2f}:{start[:13]}:{end[:13]}:{interval}:v1"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        res = await run_in_threadpool(
            weather_repo.get_history, lat, lon, start, end, interval=interval
        )
        cache.set(cache_key, res, ttl_seconds=settings.cache_ttl_seconds)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query historical data: {str(e)}",
        ) from e


@router.get("/predictions", response_model=PredictionResponse)
async def get_prediction(
    request: Request,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=360.0, description="Longitude"),
    horizon_hours: int = Query(24, description="Forecast horizon in hours (24 or 48)"),
) -> PredictionResponse:
    """Generate HeatSense ML temperature prediction for the nearest grid cell."""
    if horizon_hours not in (24, 48):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported horizon_hours '{horizon_hours}'. HeatSense supports 24 and 48 hours.",
        )

    pred_service = getattr(request.app.state, "prediction_service", None)
    if pred_service is None or not pred_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model prediction service is temporarily unavailable or model artifacts are missing.",
        )

    cache_key = f"pred:{lat:.2f}:{lon:.2f}:{horizon_hours}:{settings.model_version}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        res = await run_in_threadpool(
            pred_service.predict_point, lat=lat, lon=lon, horizon_hours=horizon_hours
        )
        cache.set(cache_key, res, ttl_seconds=settings.cache_ttl_seconds)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction inference failed: {str(e)}",
        ) from e


@router.get("/map/grid", response_model=MapGridResponse)
async def get_map_grid(
    request: Request,
    region_id: str = Query(..., description="Region identifier (e.g. state_IN_MH)"),
    layer: Literal["historical", "forecast24", "forecast48", "heat_risk"] = Query(
        ..., description="Map overlay layer type"
    ),
    bbox: Optional[str] = Query(None, description="Bounding box 'min_lat,min_lon,max_lat,max_lon'"),
) -> MapGridResponse:
    """Retrieve spatial grid cells for the requested region and layer."""
    if layer == "heat_risk":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Heat risk layer is deferred per ADR 0007 pending calibrated health threshold validation.",
        )

    parsed_bbox = parse_and_validate_bbox(bbox)
    cache_key = f"grid:{region_id}:{layer}:{bbox or 'all'}:{settings.model_version}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if layer == "historical":
        try:
            res = await run_in_threadpool(
                weather_repo.get_grid_slice, region_id=region_id, layer=layer, bbox=parsed_bbox
            )
            cache.set(cache_key, res, ttl_seconds=settings.cache_ttl_seconds)
            return res
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load historical map grid: {str(e)}",
            ) from e

    # Forecast layers: forecast24 or forecast48
    pred_service = getattr(request.app.state, "prediction_service", None)
    if pred_service is None or not pred_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forecast models are not available for grid inference.",
        )

    h_hours = 24 if layer == "forecast24" else 48
    try:
        res = await run_in_threadpool(
            pred_service.predict_grid_layer, region_id=region_id, horizon_hours=h_hours, bbox=parsed_bbox
        )
        cache.set(cache_key, res, ttl_seconds=settings.cache_ttl_seconds)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast grid: {str(e)}",
        ) from e
