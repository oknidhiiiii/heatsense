"""Standard error response schemas matching API contracts."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error object."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    request_id: Optional[str] = Field(None, description="Request correlation identifier")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional context"
    )


class ErrorResponse(BaseModel):
    """API error response wrapper."""

    error: ErrorDetail
