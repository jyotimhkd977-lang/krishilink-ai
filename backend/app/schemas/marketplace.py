"""Marketplace demand, offer, and negotiation schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.produce import ListingUnit


class DemandStatus(str, Enum):
    open = "open"
    fulfilled = "fulfilled"
    closed = "closed"


class OfferStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class NegotiationStatus(str, Enum):
    open = "open"
    accepted = "accepted"
    rejected = "rejected"
    closed = "closed"


class DemandCreate(BaseModel):
    crop: str = Field(min_length=1, max_length=120)
    quantity: float = Field(gt=0)
    unit: ListingUnit
    target_price: float = Field(ge=0)
    location: str = Field(min_length=1, max_length=240)
    minimum_quality_score: float | None = Field(default=None, ge=0, le=100)


class DemandResponse(DemandCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    buyer_id: str
    status: DemandStatus
    created_at: datetime
    updated_at: datetime


class OfferCreate(BaseModel):
    listing_id: str
    quantity: float = Field(gt=0)
    unit: ListingUnit
    offered_price: float = Field(ge=0)
    message: str | None = Field(default=None, max_length=2000)


class OfferResponse(OfferCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    buyer_id: str
    status: OfferStatus
    created_at: datetime
    updated_at: datetime


class OfferDecision(BaseModel):
    status: OfferStatus


class NegotiationCreate(BaseModel):
    offer_id: str


class NegotiationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str
    offer_id: str | None
    buyer_id: str
    farmer_id: str
    status: NegotiationStatus
    created_at: datetime
    updated_at: datetime


class NegotiationMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class NegotiationMessageResponse(NegotiationMessageCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    negotiation_id: str
    sender_id: str
    created_at: datetime