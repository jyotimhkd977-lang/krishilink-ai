"""AI request and response contracts."""

from pydantic import BaseModel, Field


class PricePredictionInput(BaseModel):
    crop: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    market_price: float = Field(ge=0)
    historical_price: list[float] = Field(min_length=1, max_length=120)
    season: str = Field(min_length=1, max_length=40)
    demand: float = Field(ge=0)
    supply: float = Field(gt=0)


class PriceRange(BaseModel):
    minimum: float
    maximum: float


class PricePredictionOutput(BaseModel):
    predicted_price: float
    price_range: PriceRange
    recommendation: str
    confidence_score: float


class DemandForecastInput(BaseModel):
    crop: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    historical_orders: list[float] = Field(min_length=1, max_length=120)
    season: str = Field(min_length=1, max_length=40)
    market_trends: list[float] = Field(min_length=1, max_length=120)


class DemandForecastOutput(BaseModel):
    predicted_demand: float
    demand_level: str
    confidence: float


class BuyerMatchResponse(BaseModel):
    buyer_id: str
    business_name: str | None = None
    match_score: float
    explanation: str


class BuyerMatchListResponse(BaseModel):
    listing_id: str
    ranked_buyers: list[BuyerMatchResponse]