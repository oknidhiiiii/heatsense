"""Pydantic schemas for location search and boundaries."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class LocationItem(BaseModel):
    """Location search item matching 06_API_CONTRACTS.md."""

    id: str
    name: str
    type: Literal["country", "state", "city"]
    country_code: str = "IN"
    admin1: Optional[str] = None
    admin2: Optional[str] = None
    latitude: float
    longitude: float
    bbox: Optional[List[float]] = Field(None, description="[min_lat, min_lon, max_lat, max_lon]")
    coverage_status: Literal["supported", "partial", "unsupported"]


class LocationSearchResponse(BaseModel):
    """Response wrapper for location search results."""

    items: List[LocationItem]
