"""Farm, listing, and produce image persistence with SQLite."""

from datetime import datetime, timezone
from typing import Any
import uuid

from fastapi import UploadFile

from app.db.session import SessionLocal
from app.models.entities import Farm, ProduceImage, ProduceListing
from app.schemas.produce import ListingStatus

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ProduceServiceError(Exception):
    """Raised when farm or listing persistence fails."""


def _row_to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    res = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        res[col.name] = val
    if hasattr(obj, "images"):
        res["produce_images"] = [_row_to_dict(img) for img in obj.images]
    return res


class ProduceService:
    def create_farm(self, access_token: str, farmer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            farm = Farm(
                id=str(uuid.uuid4()),
                farmer_id=farmer_id,
                name=values.get("name", "My Farm"),
                location=values.get("location", "Odisha"),
                size_acres=float(values.get("size_acres") or 1.0),
                soil_type=values.get("soil_type"),
                irrigation_type=values.get("irrigation_type"),
            )
            db.add(farm)
            db.commit()
            db.refresh(farm)
            return _row_to_dict(farm)
        except Exception as exc:
            db.rollback()
            raise ProduceServiceError from exc
        finally:
            db.close()

    def list_farms(self, access_token: str, farmer_id: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            farms = db.query(Farm).filter(Farm.farmer_id == farmer_id).all()
            return [_row_to_dict(f) for f in farms]
        except Exception as exc:
            raise ProduceServiceError from exc
        finally:
            db.close()

    def create_listing(self, access_token: str, farmer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            listing_id = values.get("id") or str(uuid.uuid4())
            listing = ProduceListing(
                id=listing_id,
                farmer_id=farmer_id,
                farm_id=values.get("farm_id"),
                crop=values.get("crop", "Produce"),
                variety=values.get("variety", "Standard"),
                quantity=float(values.get("quantity") or 100.0),
                unit=values.get("unit", "kg"),
                harvest_date=values.get("harvest_date"),
                expected_price=float(values.get("expected_price") or 30.0),
                min_price=float(values.get("min_price") or 28.0) if values.get("min_price") else None,
                status=values.get("status", ListingStatus.active.value),
                quality_grade=values.get("quality_grade", "Grade A"),
                ai_quality_score=float(values.get("ai_quality_score") or 90.0),
                freshness_score=float(values.get("freshness_score") or 95.0),
                uniformity_score=float(values.get("uniformity_score") or 90.0),
                damage_percent=float(values.get("damage_percent") or 3.0),
                ai_price_min=float(values.get("ai_price_min") or 30.0),
                ai_price_max=float(values.get("ai_price_max") or 34.0),
                image_url=values.get("image_url") or "assets/images/tomato.jpg",
            )
            db.add(listing)
            db.commit()
            db.refresh(listing)
            return _row_to_dict(listing)
        except Exception as exc:
            db.rollback()
            raise ProduceServiceError from exc
        finally:
            db.close()

    def list_listings(self, access_token: str | None, farmer_id: str | None, role: str | None) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(ProduceListing)
            if role == "farmer" and farmer_id:
                query = query.filter(ProduceListing.farmer_id == farmer_id)
            else:
                query = query.filter(ProduceListing.status == ListingStatus.active.value)
            listings = query.order_by(ProduceListing.created_at.desc()).all()
            return [_row_to_dict(item) for item in listings]
        except Exception as exc:
            raise ProduceServiceError from exc
        finally:
            db.close()

    def get_listing(self, access_token: str | None, listing_id: str, farmer_id: str | None, role: str | None) -> dict[str, Any]:
        db = SessionLocal()
        try:
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
            if not listing:
                raise ProduceServiceError("Listing not found")
            return _row_to_dict(listing)
        finally:
            db.close()

    def update_listing(self, access_token: str, listing_id: str, farmer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id, ProduceListing.farmer_id == farmer_id).first()
            if not listing:
                raise ProduceServiceError("Listing not found")
            for k, v in values.items():
                if hasattr(listing, k):
                    setattr(listing, k, v)
            db.commit()
            db.refresh(listing)
            return _row_to_dict(listing)
        except Exception as exc:
            db.rollback()
            raise ProduceServiceError from exc
        finally:
            db.close()

    def delete_listing(self, access_token: str, listing_id: str, farmer_id: str) -> None:
        db = SessionLocal()
        try:
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id, ProduceListing.farmer_id == farmer_id).first()
            if listing:
                db.delete(listing)
                db.commit()
        except Exception as exc:
            db.rollback()
            raise ProduceServiceError from exc
        finally:
            db.close()

    async def upload_image(self, access_token: str, farmer_id: str, listing_id: str, image: UploadFile) -> dict[str, Any]:
        content_type = image.content_type or ""
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise ProduceServiceError("Only JPEG, PNG, and WebP images are allowed")

        db = SessionLocal()
        try:
            listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id, ProduceListing.farmer_id == farmer_id).first()
            if not listing:
                raise ProduceServiceError("Listing not found")

            # Store simulated asset URL or image
            image_url = f"assets/images/{image.filename}"
            prod_img = ProduceImage(
                id=str(uuid.uuid4()),
                listing_id=listing_id,
                image_url=image_url,
                is_primary=True,
            )
            db.add(prod_img)
            listing.image_url = image_url
            db.commit()
            return _row_to_dict(prod_img)
        except Exception as exc:
            db.rollback()
            raise ProduceServiceError from exc
        finally:
            db.close()