"""Transactional order creation and validated lifecycle transitions."""

from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


class OrderServiceError(Exception):
    """Raised when an order operation is invalid or unavailable."""


class OrderService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise OrderServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(token)
        return client

    @staticmethod
    def _order_query(client: Client):
        return client.table("orders").select("*,order_items(*),order_status_history(*)")

    @staticmethod
    def _normalize_order(row: dict[str, Any]) -> dict[str, Any]:
        row["items"] = row.pop("order_items", []) or []
        row["status_history"] = row.pop("order_status_history", []) or []
        return row

    def create_from_offer(self, token: str, offer_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("create_order_from_offer", {"p_offer_id": offer_id}).execute()
            return self.get_order(token, response.data[0]["id"] if isinstance(response.data, list) else response.data["id"])
        except Exception as exc:
            raise OrderServiceError from exc

    def list_orders(self, token: str, user_id: str, role: str) -> list[dict[str, Any]]:
        try:
            query = self._order_query(self._client(token))
            if role == "buyer":
                query = query.eq("buyer_id", user_id)
            elif role == "farmer":
                query = query.eq("farmer_id", user_id)
            response = query.order("created_at", desc=True).execute()
            return [self._normalize_order(row) for row in (response.data or [])]
        except Exception as exc:
            raise OrderServiceError from exc

    def get_order(self, token: str, order_id: str) -> dict[str, Any]:
        try:
            response = self._order_query(self._client(token)).eq("id", order_id).single().execute()
            if not response.data:
                raise OrderServiceError
            return self._normalize_order(response.data)
        except OrderServiceError:
            raise
        except Exception as exc:
            raise OrderServiceError from exc

    def advance_status(self, token: str, order_id: str, status: str, note: str | None) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("advance_order_status", {"p_order_id": order_id, "p_next_status": status}).execute()
            order = self.get_order(token, response.data[0]["id"] if isinstance(response.data, list) else response.data["id"])
            return order
        except Exception as exc:
            raise OrderServiceError from exc