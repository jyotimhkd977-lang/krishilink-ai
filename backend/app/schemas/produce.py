"""Farm and produce listing schemas."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ListingUnit(str, Enum):
    kg = "kg"
    quintal = "quintal"
    ton = "ton"
    piece = "piece"
    crate = "crate"


class ListingStatus(str, Enum):
    draft = "draft"
    active = "active"
    sold = "sold"
    expired = "expired"
    archived = "archived"


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    village: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    size: float = Field(gt=0, le=1_000_000)


class FarmResponse(FarmCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    farmer_id: str
    created_at: datetime
    updated_at: datetime


class ProduceListingCreate(BaseModel):
    farm_id: str
    crop_category_id: str | None = None
    crop: str = Field(min_length=1, max_length=120)
    quantity: float = Field(gt=0)
    unit: ListingUnit
    quality_grade: str | None = Field(default=None, max_length=40)
    quality_score: float | None = Field(default=None, ge=0, le=100)
    asking_price: float = Field(ge=0)
    ai_price: float | None = Field(default=None, ge=0)
    location: str = Field(min_length=1, max_length=240)
    harvest_date: date | None = None
    status: ListingStatus = ListingStatus.draft


class ProduceListingUpdate(BaseModel):
    crop_category_id: str | None = None
    crop: str | None = Field(default=None, min_length=1, max_length=120)
    quantity: float | None = Field(default=None, gt=0)
    unit: ListingUnit | None = None
    quality_grade: str | None = Field(default=None, max_length=40)
    quality_score: float | None = Field(default=None, ge=0, le=100)
    asking_price: float | None = Field(default=None, ge=0)
    ai_price: float | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, min_length=1, max_length=240)
    harvest_date: date | None = None
    status: ListingStatus | None = None


class ProduceImageResponse(BaseModel):
    id: str
    listing_id: str
    storage_path: str
    content_type: str
    file_size: int
    created_at: datetime


class ProduceListingResponse(ProduceListingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    farmer_id: str
    created_at: datetime
    updated_at: datetime
    images: list[ProduceImageResponse] = Field(default_factory=list)