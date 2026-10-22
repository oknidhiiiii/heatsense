"""Pydantic schemas for health and system status."""

from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status (ok, degraded, error)")
    version: str = Field(..., description="API version")
    model_loaded: bool = Field(..., description="Whether trained ML models are ready for inference")
    supported_regions: List[str] = Field(..., description="List of supported region codes")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Current server UTC timestamp",
    )
