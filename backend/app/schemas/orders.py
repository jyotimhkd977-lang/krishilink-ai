"""Order lifecycle schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    pickup_scheduled = "pickup_scheduled"
    collected = "collected"
    quality_check = "quality_check"
    in_transit = "in_transit"
    delivered = "delivered"
    completed = "completed"


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str
    crop: str
    quantity: float
    unit: str
    unit_price: float


class OrderStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_status: OrderStatus | None
    to_status: OrderStatus
    changed_by: str
    changed_at: datetime
    note: str | None = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    offer_id: str
    listing_id: str
    buyer_id: str
    farmer_id: str
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = Field(default_factory=list)
    status_history: list[OrderStatusHistoryResponse] = Field(default_factory=list)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: str | None = Field(default=None, max_length=500)