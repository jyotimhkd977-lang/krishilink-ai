"""Marketplace demand, offer, and negotiation operations with SQLite."""

from datetime import datetime
from typing import Any
import uuid

from app.db.session import SessionLocal
from app.models.entities import BuyerDemand, NegotiationMessage, Offer, ProduceListing


class MarketplaceServiceError(Exception):
    """Raised when a marketplace operation is invalid or unavailable."""


def _row_to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    res = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        res[col.name] = val
    return res


class MarketplaceService:
    def create_demand(self, token: str, buyer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            demand = BuyerDemand(
                id=str(uuid.uuid4()),
                buyer_id=buyer_id,
                crop=values.get("crop", "Tomato"),
                variety=values.get("variety"),
                quantity=float(values.get("quantity") or 500.0),
                unit=values.get("unit", "kg"),
                target_price=float(values.get("target_price") or 30.0),
                location=values.get("location", "Odisha"),
                delivery_deadline=values.get("delivery_deadline"),
                status=values.get("status", "open"),
            )
            db.add(demand)
            db.commit()
            db.refresh(demand)
            return _row_to_dict(demand)
        except Exception as exc:
            db.rollback()
            raise MarketplaceServiceError from exc
        finally:
            db.close()

    def list_demands(self, token: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            demands = db.query(BuyerDemand).order_by(BuyerDemand.created_at.desc()).all()
            return [_row_to_dict(d) for d in demands]
        except Exception as exc:
            raise MarketplaceServiceError from exc
        finally:
            db.close()

    def create_offer(self, token: str, buyer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            listing = db.query(ProduceListing).filter(ProduceListing.id == values["listing_id"]).first()
            if not listing or listing.status != "active":
                raise MarketplaceServiceError("Active listing not found")

            offer = Offer(
                id=str(uuid.uuid4()),
                listing_id=values["listing_id"],
                buyer_id=buyer_id,
                demand_id=values.get("demand_id"),
                offered_price=float(values["offered_price"]),
                quantity=float(values.get("quantity", listing.quantity)),
                unit=values.get("unit", listing.unit),
                status="pending",
            )
            db.add(offer)
            db.commit()
            db.refresh(offer)
            return _row_to_dict(offer)
        except MarketplaceServiceError:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise MarketplaceServiceError from exc
        finally:
            db.close()

    def list_offers(self, token: str, user_id: str, role: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            if role == "buyer":
                offers = db.query(Offer).filter(Offer.buyer_id == user_id).order_by(Offer.created_at.desc()).all()
            else:
                # Find listings of this farmer
                farmer_listing_ids = [l.id for l in db.query(ProduceListing).filter(ProduceListing.farmer_id == user_id).all()]
                offers = db.query(Offer).filter(Offer.listing_id.in_(farmer_listing_ids)).order_by(Offer.created_at.desc()).all()
            return [_row_to_dict(o) for o in offers]
        except Exception as exc:
            raise MarketplaceServiceError from exc
        finally:
            db.close()

    def decide_offer(self, token: str, farmer_id: str, offer_id: str, status: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            offer = db.query(Offer).filter(Offer.id == offer_id).first()
            if not offer:
                raise MarketplaceServiceError("Offer not found")
            offer.status = status
            db.commit()
            db.refresh(offer)
            return _row_to_dict(offer)
        except Exception as exc:
            db.rollback()
            raise MarketplaceServiceError from exc
        finally:
            db.close()

    def create_negotiation(self, token: str, user_id: str, role: str, offer_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            offer = db.query(Offer).filter(Offer.id == offer_id).first()
            if not offer:
                raise MarketplaceServiceError("Offer not found")
            return {
                "id": f"neg-{offer.id}",
                "offer_id": offer.id,
                "listing_id": offer.listing_id,
                "buyer_id": offer.buyer_id,
            }
        finally:
            db.close()

    def send_message(self, token: str, user_id: str, negotiation_id: str, message: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            offer_id = negotiation_id.replace("neg-", "")
            msg = NegotiationMessage(
                id=str(uuid.uuid4()),
                offer_id=offer_id,
                sender_id=user_id,
                message=message,
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return _row_to_dict(msg)
        except Exception as exc:
            db.rollback()
            raise MarketplaceServiceError from exc
        finally:
            db.close()

    def list_messages(self, token: str, user_id: str, negotiation_id: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            offer_id = negotiation_id.replace("neg-", "")
            msgs = db.query(NegotiationMessage).filter(NegotiationMessage.offer_id == offer_id).order_by(NegotiationMessage.created_at.asc()).all()
            return [_row_to_dict(m) for m in msgs]
        except Exception as exc:
            raise MarketplaceServiceError from exc
        finally:
            db.close()