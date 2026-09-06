"""User-owned notification and preference operations."""

from datetime import datetime, timezone
from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


class NotificationServiceError(Exception):
    """Raised when a notification operation is unavailable."""


class NotificationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise NotificationServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(token)
        return client

    def list_notifications(self, token: str, unread_only: bool, limit: int) -> list[dict[str, Any]]:
        try:
            query = self._client(token).table("notifications").select("*")
            if unread_only:
                query = query.is_("read_at", "null")
            response = query.order("created_at", desc=True).limit(limit).execute()
            return response.data or []
        except Exception as exc:
            raise NotificationServiceError from exc

    def unread_count(self, token: str) -> int:
        try:
            response = self._client(token).table("notifications").select("id", count="exact").is_("read_at", "null").execute()
            return response.count or 0
        except Exception as exc:
            raise NotificationServiceError from exc

    def mark_read(self, token: str, notification_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).table("notifications").update({"read_at": datetime.now(timezone.utc).isoformat()}).eq("id", notification_id).execute()
            if not response.data:
                raise NotificationServiceError
            return response.data[0]
        except Exception as exc:
            raise NotificationServiceError from exc

    def mark_all_read(self, token: str) -> None:
        try:
            self._client(token).table("notifications").update({"read_at": datetime.now(timezone.utc).isoformat()}).is_("read_at", "null").execute()
        except Exception as exc:
            raise NotificationServiceError from exc

    def get_preferences(self, token: str, user_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).table("notification_preferences").select("*").eq("user_id", user_id).single().execute()
            if response.data:
                return response.data
            return {"user_id": user_id, "preferences": {notification: True for notification in NotificationType}}
        except Exception as exc:
            raise NotificationServiceError from exc

    def update_preferences(self, token: str, user_id: str, preferences: dict[str, bool]) -> dict[str, Any]:
        try:
            response = self._client(token).table("notification_preferences").upsert({"user_id": user_id, "preferences": preferences}).execute()
            return response.data[0]
        except Exception as exc:
            raise NotificationServiceError from exc