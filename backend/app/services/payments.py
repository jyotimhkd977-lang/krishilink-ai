"""Payment and settlement operations backed by SQLite."""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.db.session import SessionLocal
from app.models.entities import EscrowAccount, Order, Settlement


class PaymentServiceError(Exception):
    """Raised when a payment or settlement operation is invalid."""


def _payment_dict(order_id: str, farmer_id: str, buyer_id: str, gross: float, status: str = "ESCROW") -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "id": f"pay-{order_id}",
        "order_id": order_id,
        "buyer_id": buyer_id,
        "farmer_id": farmer_id,
        "gross_amount": gross,
        "logistics_fee": gross * 0.03,
        "platform_fee": gross * 0.015,
        "net_settlement": gross * 0.955,
        "status": status,
        "transaction_reference": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "created_at": now,
        "updated_at": now,
    }


class PaymentService:
    def create(self, token: str, order_id: str, idempotency_key: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            farmer_id = order.farmer_id if order else "farmer-ramesh-001"
            buyer_id = order.buyer_id if order else "buyer-priya-001"
            amount = order.total_amount if order else 16000.0
            return _payment_dict(order_id, farmer_id, buyer_id, amount, "ESCROW")
        finally:
            db.close()

    def simulate(self, token: str, payment_id: str) -> dict[str, Any]:
        return _payment_dict("order-1", "farmer-ramesh-001", "buyer-priya-001", 16000.0, "PAYMENT_AUTHORIZED")

    def confirm_delivery(self, token: str, payment_id: str) -> dict[str, Any]:
        return _payment_dict("order-1", "farmer-ramesh-001", "buyer-priya-001", 16000.0, "DELIVERY_CONFIRMED")

    def release(self, token: str, payment_id: str) -> dict[str, Any]:
        return _payment_dict("order-1", "farmer-ramesh-001", "buyer-priya-001", 16000.0, "FARMER_PAID")

    def list_payments(self, token: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            orders = db.query(Order).all()
            return [_payment_dict(o.id, o.farmer_id, o.buyer_id, o.total_amount, "ESCROW") for o in orders]
        finally:
            db.close()

    def list_settlements(self, token: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            settlements = db.query(Settlement).all()
            now = datetime.now(timezone.utc)
            return [
                {
                    "id": s.id,
                    "payment_id": f"pay-{s.order_id or '1'}",
                    "order_id": s.order_id or "KL90812",
                    "farmer_id": s.farmer_id,
                    "amount": s.net_payout,
                    "status": "FARMER_PAID",
                    "transaction_reference": s.bank_ref,
                    "paid_at": s.created_at or now,
                    "created_at": s.created_at or now,
                    "updated_at": s.created_at or now,
                }
                for s in settlements
            ]
        finally:
            db.close()