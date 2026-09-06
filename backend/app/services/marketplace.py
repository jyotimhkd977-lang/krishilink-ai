"""Marketplace demand, offer, and negotiation operations."""

from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


class MarketplaceServiceError(Exception):
    """Raised when a marketplace operation is invalid or unavailable."""


class MarketplaceService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, access_token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise MarketplaceServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(access_token)
        return client

    def create_demand(self, token: str, buyer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client(token).table("buyer_demands").insert({**values, "buyer_id": buyer_id}).execute()
            return response.data[0]
        except Exception as exc:
            raise MarketplaceServiceError from exc

    def list_demands(self, token: str) -> list[dict[str, Any]]:
        try:
            response = self._client(token).table("buyer_demands").select("*").order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise MarketplaceServiceError from exc

    def create_offer(self, token: str, buyer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        client = self._client(token)
        try:
            listing = client.table("produce_listings").select("id,farmer_id,quantity,unit,status").eq("id", values["listing_id"]).single().execute().data
            if not listing or listing["status"] != "active":
                raise MarketplaceServiceError
            if listing["unit"] != values["unit"] or values["quantity"] > listing["quantity"]:
                raise MarketplaceServiceError
            existing = client.table("offers").select("id").eq("listing_id", values["listing_id"]).eq("buyer_id", buyer_id).in_("status", ["pending", "accepted"]).execute()
            if existing.data:
                raise MarketplaceServiceError
            response = client.table("offers").insert({**values, "buyer_id": buyer_id}).execute()
            return response.data[0]
        except MarketplaceServiceError:
            raise
        except Exception as exc:
            raise MarketplaceServiceError from exc

    def list_offers(self, token: str, user_id: str, role: str) -> list[dict[str, Any]]:
        client = self._client(token)
        try:
            if role == "buyer":
                query = client.table("offers").select("*").eq("buyer_id", user_id)
            else:
                query = client.table("offers").select("*,produce_listings!inner(farmer_id)").eq("produce_listings.farmer_id", user_id)
            response = query.order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise MarketplaceServiceError from exc

    def decide_offer(self, token: str, farmer_id: str, offer_id: str, status: str) -> dict[str, Any]:
        client = self._client(token)
        try:
            offer = client.table("offers").select("id,listing_id,status,produce_listings!inner(farmer_id)").eq("id", offer_id).single().execute().data
            if not offer or offer["produce_listings"]["farmer_id"] != farmer_id or offer["status"] != "pending":
                raise MarketplaceServiceError
            response = client.table("offers").update({"status": status}).eq("id", offer_id).execute()
            return response.data[0]
        except MarketplaceServiceError:
            raise
        except Exception as exc:
            raise MarketplaceServiceError from exc

    def create_negotiation(self, token: str, user_id: str, role: str, offer_id: str) -> dict[str, Any]:
        client = self._client(token)
        try:
            offer = client.table("offers").select("id,buyer_id,listing_id,produce_listings!inner(farmer_id)").eq("id", offer_id).single().execute().data
            if not offer or (role == "buyer" and offer["buyer_id"] != user_id) or (role == "farmer" and offer["produce_listings"]["farmer_id"] != user_id):
                raise MarketplaceServiceError
            values = {
                "offer_id": offer_id,
                "listing_id": offer["listing_id"],
                "buyer_id": offer["buyer_id"],
                "farmer_id": offer["produce_listings"]["farmer_id"],
            }
            response = client.table("negotiations").upsert(values, on_conflict="offer_id").execute()
            return response.data[0]
        except MarketplaceServiceError:
            raise
        except Exception as exc:
            raise MarketplaceServiceError from exc

    def send_message(self, token: str, user_id: str, negotiation_id: str, message: str) -> dict[str, Any]:
        client = self._client(token)
        try:
            participant = client.table("negotiations").select("id").eq("id", negotiation_id).or_(f"buyer_id.eq.{user_id},farmer_id.eq.{user_id}").single().execute().data
            if not participant:
                raise MarketplaceServiceError
            response = client.table("negotiation_messages").insert({"negotiation_id": negotiation_id, "sender_id": user_id, "message": message}).execute()
            return response.data[0]
        except MarketplaceServiceError:
            raise
        except Exception as exc:
            raise MarketplaceServiceError from exc

    def list_messages(self, token: str, user_id: str, negotiation_id: str) -> list[dict[str, Any]]:
        try:
            response = self._client(token).table("negotiation_messages").select("*").eq("negotiation_id", negotiation_id).order("created_at").execute()
            return response.data or []
        except Exception as exc:
            raise MarketplaceServiceError from exc