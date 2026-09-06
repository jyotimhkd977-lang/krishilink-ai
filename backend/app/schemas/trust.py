"""Review and trust score schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    order_id: str
    reviewee_id: str
    rating: float = Field(ge=1, le=5)
    quality_rating: float | None = Field(default=None, ge=1, le=5)
    delivery_rating: float | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewResponse(ReviewCreate):
    id: str
    reviewer_id: str
    created_at: datetime


class TrustScoreResponse(BaseModel):
    user_id: str
    score: float
    successful_orders: int
    quality_score: float
    delivery_reliability: float
    payment_reliability: float
    ratings: float
    dispute_history: float
    badges: list[str]
    calculated_at: datetime
    updated_at: datetime