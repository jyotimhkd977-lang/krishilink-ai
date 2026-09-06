"""Review creation and trust score retrieval service."""

from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


class TrustServiceError(Exception):
    """Raised when a review or trust score operation is invalid."""


class TrustService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise TrustServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(token)
        return client

    def create_review(self, token: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("create_review", {
                "p_order_id": values["order_id"],
                "p_reviewee_id": values["reviewee_id"],
                "p_rating": values["rating"],
                "p_quality_rating": values.get("quality_rating"),
                "p_delivery_rating": values.get("delivery_rating"),
                "p_comment": values.get("comment"),
            }).execute()
            return response.data[0] if isinstance(response.data, list) else response.data
        except Exception as exc:
            raise TrustServiceError from exc

    def list_reviews(self, token: str, user_id: str) -> list[dict[str, Any]]:
        try:
            response = self._client(token).table("reviews").select("*").eq("reviewee_id", user_id).order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise TrustServiceError from exc

    def get_score(self, token: str, user_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("get_trust_score", {"p_user_id": user_id}).execute()
            return response.data[0] if isinstance(response.data, list) else response.data
        except TrustServiceError:
            raise
        except Exception as exc:
            raise TrustServiceError from exc