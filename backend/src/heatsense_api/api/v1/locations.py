"""Location search and GeoJSON administrative boundary API routes."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status
from heatsense_api.config import settings
from heatsense_api.repositories.locations import LocationRepository
from heatsense_api.schemas.locations import LocationSearchResponse

router = APIRouter(prefix="/locations", tags=["Locations"])
repo = LocationRepository()

_GEOJSON_PATH = settings.data_dir / "geojson" / "india_city_boundaries.geojson"
_boundaries_cache: Optional[Dict[str, Any]] = None


def _get_boundaries_geojson() -> Dict[str, Any]:
    """Load and memory-cache administrative boundaries GeoJSON."""
    global _boundaries_cache
    if _boundaries_cache is None:
        target_path = _GEOJSON_PATH
        if not target_path.exists():
            # Fallback path relative to project root
            target_path = Path(__file__).resolve().parents[4] / "data" / "geojson" / "india_city_boundaries.geojson"
        if not target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrative boundaries GeoJSON not found on server.",
            )
        with open(target_path, "r", encoding="utf-8") as f:
            _boundaries_cache = json.load(f)
    return _boundaries_cache


@router.get("/search", response_model=LocationSearchResponse)
async def search_locations(
    q: str = Query(..., min_length=1, description="Location search query (e.g. Mumbai)"),
    limit: int = Query(10, ge=1, le=settings.max_search_limit, description="Max results"),
) -> LocationSearchResponse:
    """Search for supported country, state, and city entities in India."""
    items = repo.search(q, limit=limit)
    return LocationSearchResponse(items=items)


@router.get("/boundaries")
async def get_all_boundaries(
    state: Optional[str] = Query(None, description="Optional state filter (e.g. Maharashtra)"),
    tier: Optional[int] = Query(None, ge=1, le=3, description="Spatial clustering tier filter (1, 2, or 3)"),
) -> Dict[str, Any]:
    """Retrieve GeoJSON FeatureCollection of administrative city boundaries in India."""
    geojson = _get_boundaries_geojson()
    if not state and not tier:
        return geojson

    filtered_features = []
    for feat in geojson.get("features", []):
        props = feat.get("properties", {})
        if state and props.get("state", "").lower() != state.lower():
            continue
        if tier is not None and props.get("tier") != tier:
            continue
        filtered_features.append(feat)

    return {
        "type": "FeatureCollection",
        "features": filtered_features,
    }


@router.get("/boundaries/{city_id}")
async def get_city_boundary(city_id: str) -> Dict[str, Any]:
    """Retrieve GeoJSON Feature for a specific city boundary."""
    geojson = _get_boundaries_geojson()
    for feat in geojson.get("features", []):
        if feat.get("id") == city_id or feat.get("properties", {}).get("id") == city_id:
            return feat

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Boundary feature for city '{city_id}' not found.",
    )
