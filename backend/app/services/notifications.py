"""User-owned notification and preference operations with SQLite."""

from datetime import datetime, timezone
from typing import Any

from app.db.session import SessionLocal
from app.models.entities import Notification
from app.schemas.notifications import NotificationType


class NotificationServiceError(Exception):
    """Raised when a notification operation is unavailable."""


def _notif_to_dict(n: Notification) -> dict[str, Any]:
    type_map = {
        "price_alert": NotificationType.ai_alert,
        "match": NotificationType.buyer,
        "logistics": NotificationType.logistics,
        "payment": NotificationType.payment,
        "order": NotificationType.order,
        "quality": NotificationType.quality,
        "dispute": NotificationType.dispute,
        "weather": NotificationType.weather,
    }
    notif_type = type_map.get(n.type, NotificationType.ai_alert)
    read_at = n.created_at if n.is_read else None

    return {
        "id": n.id,
        "user_id": n.user_id,
        "type": notif_type,
        "title": n.title,
        "body": n.message,
        "data": {},
        "read_at": read_at,
        "created_at": n.created_at,
    }


class NotificationService:
    def list_notifications(self, token: str, unread_only: bool, limit: int) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(Notification)
            if unread_only:
                query = query.filter(Notification.is_read == False)
            notifs = query.order_by(Notification.created_at.desc()).limit(limit).all()
            return [_notif_to_dict(n) for n in notifs]
        finally:
            db.close()

    def unread_count(self, token: str) -> int:
        db = SessionLocal()
        try:
            return db.query(Notification).filter(Notification.is_read == False).count()
        finally:
            db.close()

    def mark_read(self, token: str, notification_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            notif = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notif:
                raise NotificationServiceError("Notification not found")
            notif.is_read = True
            db.commit()
            db.refresh(notif)
            return _notif_to_dict(notif)
        finally:
            db.close()

    def mark_all_read(self, token: str) -> None:
        db = SessionLocal()
        try:
            db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
            db.commit()
        finally:
            db.close()

    def get_preferences(self, token: str, user_id: str) -> dict[str, Any]:
        return {
            "preferences": {
                NotificationType.order: True,
                NotificationType.payment: True,
                NotificationType.buyer: True,
                NotificationType.ai_alert: True,
                NotificationType.logistics: True,
                NotificationType.weather: True,
                NotificationType.quality: True,
                NotificationType.dispute: True,
            }
        }

    def update_preferences(self, token: str, user_id: str, preferences: dict[str, bool]) -> dict[str, Any]:
        return {"preferences": preferences}