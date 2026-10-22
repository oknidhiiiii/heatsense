"""Location search API routes."""

from fastapi import APIRouter, Query
from heatsense_api.config import settings
from heatsense_api.repositories.locations import LocationRepository
from heatsense_api.schemas.locations import LocationSearchResponse

router = APIRouter(prefix="/locations", tags=["Locations"])
repo = LocationRepository()


@router.get("/search", response_model=LocationSearchResponse)
async def search_locations(
    q: str = Query(..., min_length=1, description="Location search query (e.g. Mumbai)"),
    limit: int = Query(10, ge=1, le=settings.max_search_limit, description="Max results"),
) -> LocationSearchResponse:
    """Search for supported country, state, and city entities in India."""
    items = repo.search(q, limit=limit)
    return LocationSearchResponse(items=items)
