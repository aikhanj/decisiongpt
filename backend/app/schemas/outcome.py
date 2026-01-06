from datetime import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional


class OutcomeCreate(BaseModel):
    """Request to log an outcome."""

    progress_yesno: bool = Field(..., description="Did the move make progress?")
    sentiment_2h: Optional[int] = Field(
        None, ge=-2, le=2, description="Sentiment after 2 hours (-2 to +2)"
    )
    sentiment_24h: Optional[int] = Field(
        None, ge=-2, le=2, description="Sentiment after 24 hours (-2 to +2)"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")


class OutcomeResponse(BaseModel):
    """Response for an outcome."""

    id: UUID
    node_id: UUID
    progress_yesno: Optional[bool] = None
    sentiment_2h: Optional[int] = None
    sentiment_24h: Optional[int] = None
    brier_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
