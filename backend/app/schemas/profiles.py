"""Application user profile schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FarmerProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    phone: str | None = None
    village: str | None = None
    district: str | None = None
    state: str | None = None
    farm_size: float | None = Field(default=None, ge=0)


class FarmerProfileUpdate(FarmerProfileCreate):
    pass


class FarmerProfileResponse(FarmerProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    trust_score: float
    verified: bool
    created_at: datetime
    updated_at: datetime


class BuyerProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_name: str | None = None
    buyer_type: str | None = None
    location: str | None = None


class BuyerProfileUpdate(BuyerProfileCreate):
    pass


class BuyerProfileResponse(BuyerProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    trust_score: float
    verified: bool
    created_at: datetime
    updated_at: datetime


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    role: str
    farmer_profile: FarmerProfileResponse | None = None
    buyer_profile: BuyerProfileResponse | None = None


class ProfileListResponse(BaseModel):
    profiles: list[ProfileResponse]