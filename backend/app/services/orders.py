"""Order service with SQLite database."""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.db.session import SessionLocal
from app.models.entities import EscrowAccount, Offer, Order, OrderStatusHistory, ProduceListing, Settlement, Shipment


class OrderServiceError(Exception):
    """Raised when an order operation is invalid or unavailable."""


def _order_to_dict(order: Order, db: Any) -> dict[str, Any]:
    listing = db.query(ProduceListing).filter(ProduceListing.id == order.listing_id).first() if order.listing_id else None
    crop_name = listing.crop if listing else "Produce"

    item = {
        "id": f"item-{order.id}",
        "listing_id": order.listing_id or "",
        "crop": crop_name,
        "quantity": order.quantity,
        "unit": order.unit,
        "unit_price": order.unit_price,
    }

    history_records = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == order.id).order_by(OrderStatusHistory.created_at.asc()).all()
    history = [
        {
            "id": h.id,
            "from_status": None,
            "to_status": h.status,
            "changed_by": order.farmer_id,
            "changed_at": h.created_at,
            "note": h.note,
        }
        for h in history_records
    ]

    return {
        "id": order.id,
        "offer_id": f"off-{order.id}",
        "listing_id": order.listing_id or "",
        "buyer_id": order.buyer_id,
        "farmer_id": order.farmer_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [item],
        "status_history": history,
    }


class OrderService:
    def create_from_offer(self, token: str, offer_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            offer = db.query(Offer).filter(Offer.id == offer_id).first()
            if not offer:
                raise OrderServiceError("Offer not found")

            listing = db.query(ProduceListing).filter(ProduceListing.id == offer.listing_id).first()
            if not listing:
                raise OrderServiceError("Listing not found")

            now = datetime.now(timezone.utc)
            order_id = f"KL{uuid.uuid4().hex[:6].upper()}"
            total = offer.offered_price * offer.quantity

            order = Order(
                id=order_id,
                listing_id=listing.id,
                buyer_id=offer.buyer_id,
                farmer_id=listing.farmer_id,
                quantity=offer.quantity,
                unit=offer.unit,
                unit_price=offer.offered_price,
                total_amount=total,
                status="confirmed",
                vehicle_no="OD-02-KL-9081",
                driver_name="Santosh Das",
                driver_phone="+91 94371 90234",
                pickup_eta="Today 11:30 AM",
                created_at=now,
                updated_at=now,
            )
            db.add(order)

            offer.status = "accepted"

            # Create shipment and escrow
            shipment = Shipment(
                id=str(uuid.uuid4()),
                order_id=order_id,
                carrier_name="KrishiLink Smart Consolidation Network",
                driver_name="Santosh Das",
                driver_phone="+91 94371 90234",
                vehicle_number="OD-02-KL-9081",
                origin="Khordha Farm Field, Odisha",
                destination="ABC Foods Facility, Bhubaneswar",
                status="in_transit",
                created_at=now,
            )
            db.add(shipment)

            escrow = EscrowAccount(
                id=str(uuid.uuid4()),
                order_id=order_id,
                amount=total,
                status="locked",
                created_at=now,
            )
            db.add(escrow)

            history = OrderStatusHistory(
                id=str(uuid.uuid4()),
                order_id=order_id,
                status="confirmed",
                note="Order confirmed from offer. Escrow payment locked.",
                created_at=now,
            )
            db.add(history)

            db.commit()
            db.refresh(order)
            return _order_to_dict(order, db)
        except Exception as exc:
            db.rollback()
            raise OrderServiceError from exc
        finally:
            db.close()

    def create_direct_order(
        self,
        buyer_id: str,
        listing_id: str,
        quantity: float,
        unit_price: float,
    ) -> dict[str, Any]:
        db = SessionLocal()
        try:
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
            farmer_id = listing.farmer_id if listing else "farmer-ramesh-001"
            total = quantity * unit_price
            order_id = f"KL{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now(timezone.utc)

            order = Order(
                id=order_id,
                listing_id=listing_id,
                buyer_id=buyer_id,
                farmer_id=farmer_id,
                quantity=quantity,
                unit="kg",
                unit_price=unit_price,
                total_amount=total,
                status="confirmed",
                created_at=now,
                updated_at=now,
            )
            db.add(order)

            history = OrderStatusHistory(
                id=str(uuid.uuid4()),
                order_id=order_id,
                status="confirmed",
                note="Direct consumer cart checkout. Smart logistics assigned.",
                created_at=now,
            )
            db.add(history)

            db.commit()
            db.refresh(order)
            return _order_to_dict(order, db)
        except Exception as exc:
            db.rollback()
            raise OrderServiceError from exc
        finally:
            db.close()

    def list_orders(self, token: str, user_id: str, role: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            if role == "buyer":
                orders = db.query(Order).filter(Order.buyer_id == user_id).order_by(Order.created_at.desc()).all()
            elif role == "farmer":
                orders = db.query(Order).filter(Order.farmer_id == user_id).order_by(Order.created_at.desc()).all()
            else:
                orders = db.query(Order).order_by(Order.created_at.desc()).all()
            return [_order_to_dict(o, db) for o in orders]
        except Exception as exc:
            raise OrderServiceError from exc
        finally:
            db.close()

    def get_order(self, token: str, order_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise OrderServiceError("Order not found")
            return _order_to_dict(order, db)
        finally:
            db.close()

    def advance_status(self, token: str, order_id: str, status: str, note: str | None) -> dict[str, Any]:
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise OrderServiceError("Order not found")
            order.status = status
            order.updated_at = datetime.now(timezone.utc)

            history = OrderStatusHistory(
                id=str(uuid.uuid4()),
                order_id=order_id,
                status=status,
                note=note or f"Status changed to {status}",
                created_at=datetime.now(timezone.utc),
            )
            db.add(history)

            if status == "completed":
                # Create settlement statement
                settlement = Settlement(
                    id=str(uuid.uuid4()),
                    order_id=order.id,
                    farmer_id=order.farmer_id,
                    gross_amount=order.total_amount,
                    logistics_fee=order.total_amount * 0.03,
                    platform_fee=order.total_amount * 0.015,
                    net_payout=order.total_amount * 0.955,
                    bank_ref=f"DBT-KL-{uuid.uuid4().hex[:6].upper()}",
                    status="settled",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(settlement)

            db.commit()
            db.refresh(order)
            return _order_to_dict(order, db)
        except Exception as exc:
            db.rollback()
            raise OrderServiceError from exc
        finally:
            db.close()