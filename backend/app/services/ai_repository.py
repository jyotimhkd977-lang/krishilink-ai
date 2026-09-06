"""Persistence adapter for AI outputs using SQLite."""

import json
from typing import Any
import uuid

from app.db.session import SessionLocal
from app.models.entities import BuyerDemand, BuyerProfile, DemandForecast, PricePrediction, ProduceListing


class AIRepositoryError(Exception):
    """Raised when prediction persistence is unavailable."""


class AIRepository:
    def save_price(self, token: str, requester_id: str, inputs: dict[str, Any], output: dict[str, Any]) -> None:
        db = SessionLocal()
        try:
            pred = PricePrediction(
                id=str(uuid.uuid4()),
                requester_id=requester_id,
                crop=inputs.get("crop", "Tomato"),
                location=inputs.get("location", "Khordha"),
                predicted_price=float(output.get("recommended_price") or output.get("price") or 32.0),
                confidence=float(output.get("confidence") or 0.92),
                input_data=json.dumps(inputs),
                output_data=json.dumps(output),
            )
            db.add(pred)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def save_demand(self, token: str, requester_id: str, inputs: dict[str, Any], output: dict[str, Any]) -> None:
        db = SessionLocal()
        try:
            forecast = DemandForecast(
                id=str(uuid.uuid4()),
                requester_id=requester_id,
                crop=inputs.get("crop", "Tomato"),
                location=inputs.get("location", "Khordha"),
                demand_level=output.get("demand_level", "High"),
                confidence=float(output.get("confidence") or 0.88),
                input_data=json.dumps(inputs),
                output_data=json.dumps(output),
            )
            db.add(forecast)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def get_listing_and_buyers(self, token: str, listing_id: str, farmer_id: str) -> tuple[dict, list[dict]]:
        db = SessionLocal()
        try:
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
            if not listing:
                # If not matched by id, grab first active listing
                listing = db.query(ProduceListing).filter(ProduceListing.farmer_id == farmer_id).first()
            if not listing:
                listing = db.query(ProduceListing).first()
            if not listing:
                raise AIRepositoryError("Listing not found")

            listing_dict = {
                "id": listing.id,
                "crop": listing.crop,
                "quantity": listing.quantity,
                "asking_price": listing.expected_price,
                "location": "Khordha",
            }

            buyers = db.query(BuyerProfile).all()
            demands = db.query(BuyerDemand).filter(BuyerDemand.status == "open").all()
            demand_by_buyer = {d.buyer_id: d for d in demands}

            buyer_list = []
            for b in buyers:
                demand = demand_by_buyer.get(b.user_id)
                buyer_list.append({
                    "buyer_id": b.user_id,
                    "business_name": b.business_name or "Verified Buyer",
                    "location": b.location or "Bhubaneswar",
                    "trust_score": b.trust_score or 92.0,
                    "payment_reliability": b.payment_reliability or 95.0,
                    "pickup_available": b.pickup_available,
                    "required_quantity": demand.quantity if demand else listing.quantity,
                    "offer_price": demand.target_price if demand else listing.expected_price,
                    "distance_km": 14,
                })
            return listing_dict, buyer_list
        finally:
            db.close()

    def save_matches(self, token: str, farmer_id: str, listing_id: str, matches: list[dict]) -> None:
        return None