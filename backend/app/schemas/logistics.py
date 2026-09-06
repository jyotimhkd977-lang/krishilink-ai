"""Logistics and delivery schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    unassigned = "unassigned"
    assigned = "assigned"
    pickup_scheduled = "pickup_scheduled"
    en_route = "en_route"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class DeliveryCreate(BaseModel):
    order_id: str
    pickup_address: str = Field(min_length=1, max_length=500)
    delivery_address: str = Field(min_length=1, max_length=500)
    scheduled_pickup_at: datetime | None = None


class DeliveryAssignment(BaseModel):
    driver_id: str
    vehicle_id: str
    scheduled_pickup_at: datetime | None = None


class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus
    estimated_arrival: datetime | None = None


class VehicleCreate(BaseModel):
    driver_id: str
    registration_number: str = Field(min_length=2, max_length=30)
    vehicle_type: str = Field(min_length=1, max_length=80)
    capacity: float = Field(gt=0)


class VehicleResponse(VehicleCreate):
    id: str
    is_available: bool
    created_at: datetime
    updated_at: datetime


class LocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_kph: float | None = Field(default=None, ge=0)
    heading: float | None = Field(default=None, ge=0, le=360)


class VehicleLocationResponse(LocationUpdate):
    id: str
    vehicle_id: str
    delivery_id: str
    driver_id: str
    recorded_at: datetime


class DeliveryResponse(DeliveryCreate):
    id: str
    farmer_id: str
    buyer_id: str
    driver_id: str | None = None
    vehicle_id: str | None = None
    estimated_arrival: datetime | None = None
    route: list[dict] = Field(default_factory=list)
    status: DeliveryStatus
    created_at: datetime
    updated_at: datetime