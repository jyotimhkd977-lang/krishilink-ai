"""Logistics and delivery service with SQLite."""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.db.session import SessionLocal
from app.models.entities import Order, Shipment, ShipmentUpdate


class LogisticsServiceError(Exception):
    """Raised when a logistics operation is invalid or unavailable."""


def _shipment_to_delivery(s: Shipment, order: Order | None = None) -> dict[str, Any]:
    now = s.created_at or datetime.now(timezone.utc)
    return {
        "id": s.id,
        "order_id": s.order_id,
        "farmer_id": order.farmer_id if order else "farmer-ramesh-001",
        "buyer_id": order.buyer_id if order else "buyer-priya-001",
        "pickup_address": s.origin,
        "delivery_address": s.destination,
        "scheduled_pickup_at": now,
        "driver_id": "driver-santosh-001",
        "vehicle_id": s.vehicle_number,
        "status": "in_transit" if s.status == "in_transit" else "assigned",
        "tracking_number": f"TRK-{s.id[:8].upper()}",
        "estimated_arrival": now,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


class LogisticsService:
    def create_delivery(self, token: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == values["order_id"]).first()
            if not order:
                raise LogisticsServiceError("Order not found")

            now = datetime.now(timezone.utc)
            shipment = Shipment(
                id=str(uuid.uuid4()),
                order_id=order.id,
                origin=values.get("pickup_address", "Farm Location"),
                destination=values.get("delivery_address", "Buyer Hub"),
                carrier_name="KrishiLink Network",
                status="assigned",
                created_at=now,
                updated_at=now,
            )
            db.add(shipment)
            db.commit()
            db.refresh(shipment)
            return _shipment_to_delivery(shipment, order)
        except Exception as exc:
            db.rollback()
            raise LogisticsServiceError from exc
        finally:
            db.close()

    def list_deliveries(self, token: str, user_id: str, role: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            shipments = db.query(Shipment).all()
            res = []
            for s in shipments:
                order = db.query(Order).filter(Order.id == s.order_id).first()
                res.append(_shipment_to_delivery(s, order))
            return res
        except Exception as exc:
            raise LogisticsServiceError from exc
        finally:
            db.close()

    def get_delivery(self, token: str, delivery_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            shipment = db.query(Shipment).filter(Shipment.id == delivery_id).first()
            if not shipment:
                raise LogisticsServiceError("Delivery not found")
            order = db.query(Order).filter(Order.id == shipment.order_id).first()
            return _shipment_to_delivery(shipment, order)
        finally:
            db.close()

    def list_locations(self, token: str, delivery_id: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": f"loc-{delivery_id}-1",
                "delivery_id": delivery_id,
                "vehicle_id": "OD-02-KL-9081",
                "driver_id": "driver-santosh-001",
                "latitude": 20.1825,
                "longitude": 85.6174,
                "speed_kph": 42.0,
                "heading": 85.0,
                "recorded_at": now,
            }
        ]

    def assign_delivery(self, token: str, delivery_id: str, values: dict[str, Any]) -> dict[str, Any]:
        return self.get_delivery(token, delivery_id)

    def update_status(self, token: str, delivery_id: str, status: str, eta: Any = None) -> dict[str, Any]:
        db = SessionLocal()
        try:
            shipment = db.query(Shipment).filter(Shipment.id == delivery_id).first()
            if not shipment:
                raise LogisticsServiceError("Delivery not found")
            shipment.status = status
            db.commit()
            db.refresh(shipment)
            order = db.query(Order).filter(Order.id == shipment.order_id).first()
            return _shipment_to_delivery(shipment, order)
        finally:
            db.close()

    def create_vehicle(self, token: str, values: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "id": f"veh-{uuid.uuid4().hex[:6]}",
            "driver_id": values.get("driver_id", "driver-1"),
            "registration_number": values.get("registration_number", "OD-02-KL-9081"),
            "vehicle_type": values.get("vehicle_type", "Refrigerated Mini Truck"),
            "capacity": float(values.get("capacity", 2000.0)),
            "is_available": True,
            "created_at": now,
            "updated_at": now,
        }

    def list_vehicles(self, token: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": "veh-1",
                "driver_id": "driver-santosh-001",
                "registration_number": "OD-02-KL-9081",
                "vehicle_type": "Insulated Tata Ace EV",
                "capacity": 1500.0,
                "is_available": True,
                "created_at": now,
                "updated_at": now,
            }
        ]

    def record_location(self, token: str, vehicle_id: str, values: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "id": f"loc-{uuid.uuid4().hex[:6]}",
            "vehicle_id": vehicle_id,
            "delivery_id": "del-1",
            "driver_id": "driver-santosh-001",
            "latitude": float(values.get("latitude", 20.18)),
            "longitude": float(values.get("longitude", 85.61)),
            "speed_kph": float(values.get("speed_kph", 40.0)),
            "heading": float(values.get("heading", 90.0)),
            "recorded_at": now,
        }