"""Payment and settlement schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    payment_pending = "PAYMENT_PENDING"
    payment_authorized = "PAYMENT_AUTHORIZED"
    escrow = "ESCROW"
    delivery_confirmed = "DELIVERY_CONFIRMED"
    settlement = "SETTLEMENT"
    farmer_paid = "FARMER_PAID"
    failed = "FAILED"


class SettlementStatus(str, Enum):
    settlement = "SETTLEMENT"
    farmer_paid = "FARMER_PAID"
    failed = "FAILED"


class PaymentCreate(BaseModel):
    order_id: str
    idempotency_key: str = Field(min_length=8, max_length=128)


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    buyer_id: str
    farmer_id: str
    gross_amount: float
    logistics_fee: float
    platform_fee: float
    net_settlement: float
    status: PaymentStatus
    transaction_reference: str | None = None
    created_at: datetime
    updated_at: datetime


class SettlementResponse(BaseModel):
    id: str
    payment_id: str
    order_id: str
    farmer_id: str
    amount: float
    status: SettlementStatus
    transaction_reference: str
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime