"""Pydantic schemas for bid endpoints."""

from pydantic import BaseModel, Field


class BidRequest(BaseModel):
    """Validated query parameters for ``GET /bid``."""

    campaign_id: str = Field(
        ..., min_length=1, description="Campaign identifier"
    )
    geo: str | None = Field(
        None, description="Geographic context (accepted, ignored in v1)"
    )


class BidResponse(BaseModel):
    """Response body containing the recommended bid."""

    bid: float = Field(..., ge=0, description="Recommended bid amount in dollars")
    campaign_id: str
