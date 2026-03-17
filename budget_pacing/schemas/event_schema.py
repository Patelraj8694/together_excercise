"""Pydantic schemas for event endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EventRequest(BaseModel):
    """Validated payload for ``POST /event``."""

    campaign_id: str = Field(
        ..., min_length=1, description="Campaign identifier"
    )
    cost: float = Field(
        ..., gt=0, description="Auction win cost in dollars (must be > 0)"
    )
    timestamp: datetime = Field(
        ..., description="ISO 8601 timestamp of the auction win"
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_z_suffix(cls, v):
        """Accept ``2025-03-05T10:00:00Z`` (trailing Z) as valid ISO."""
        if isinstance(v, str) and v.endswith("Z"):
            v = v[:-1] + "+00:00"
        return v

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "campaign_id": "A1",
                "cost": 0.50,
                "timestamp": "2025-03-05T10:00:00Z",
            }
        ]
    }}


class EventResponse(BaseModel):
    """Response body after successfully recording an event."""

    status: str = "recorded"
    campaign_id: str
    daily_spend: float
    daily_limit: float
