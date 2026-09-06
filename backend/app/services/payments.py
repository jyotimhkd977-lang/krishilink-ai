"""Prototype payment and settlement operations backed by database RPCs."""

from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


class PaymentServiceError(Exception):
    """Raised when a payment or settlement operation is invalid."""


class PaymentService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise PaymentServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(token)
        return client

    def create(self, token: str, order_id: str, idempotency_key: str) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("create_payment_for_order", {"p_order_id": order_id, "p_idempotency_key": idempotency_key}).execute()
            return response.data[0] if isinstance(response.data, list) else response.data
        except Exception as exc:
            raise PaymentServiceError from exc

    def simulate(self, token: str, payment_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("simulate_payment", {"p_payment_id": payment_id}).execute()
            return response.data[0] if isinstance(response.data, list) else response.data
        except Exception as exc:
            raise PaymentServiceError from exc

    def confirm_delivery(self, token: str, payment_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("confirm_payment_delivery", {"p_payment_id": payment_id}).execute()
            return response.data[0] if isinstance(response.data, list) else response.data
        except Exception as exc:
            raise PaymentServiceError from exc

    def release(self, token: str, payment_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).rpc("release_payment_settlement", {"p_payment_id": payment_id}).execute()
            return response.data[0] if isinstance(response.data, list) else response.data
        except Exception as exc:
            raise PaymentServiceError from exc

    def list_payments(self, token: str) -> list[dict[str, Any]]:
        try:
            response = self._client(token).table("payments").select("*").order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise PaymentServiceError from exc

    def list_settlements(self, token: str) -> list[dict[str, Any]]:
        try:
            response = self._client(token).table("settlements").select("*").order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise PaymentServiceError from exc