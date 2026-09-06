"""Persistence adapter for AI outputs."""

from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


class AIRepositoryError(Exception):
    """Raised when prediction persistence is unavailable."""


class AIRepository:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise AIRepositoryError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(token)
        return client

    def _admin_client(self) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_service_role_key:
            raise AIRepositoryError
        return create_client(self.settings.supabase_url, self.settings.supabase_service_role_key)

    def save_price(self, token: str, requester_id: str, inputs: dict[str, Any], output: dict[str, Any]) -> None:
        self._client(token).table("price_predictions").insert({
            "requester_id": requester_id,
            "crop": inputs["crop"],
            "location": inputs["location"],
            "input_data": inputs,
            **output,
        }).execute()

    def save_demand(self, token: str, requester_id: str, inputs: dict[str, Any], output: dict[str, Any]) -> None:
        self._client(token).table("demand_forecasts").insert({
            "requester_id": requester_id,
            "crop": inputs["crop"],
            "location": inputs["location"],
            "input_data": inputs,
            **output,
        }).execute()

    def get_listing_and_buyers(self, token: str, listing_id: str, farmer_id: str) -> tuple[dict, list[dict]]:
        try:
            client = self._client(token)
            listing = client.table("produce_listings").select("*").eq("id", listing_id).eq("farmer_id", farmer_id).single().execute().data
            if not listing:
                raise AIRepositoryError
            admin_client = self._admin_client()
            buyers = admin_client.table("buyer_profiles").select("user_id,business_name,location,trust_score,payment_reliability,pickup_available").execute().data or []
            demands = admin_client.table("buyer_demands").select("buyer_id,crop,quantity,target_price,location").eq("status", "open").ilike("crop", listing["crop"]).execute().data or []
            demand_by_buyer = {demand["buyer_id"]: demand for demand in demands}
            for buyer in buyers:
                demand = demand_by_buyer.get(buyer["user_id"])
                buyer["buyer_id"] = buyer.pop("user_id")
                buyer["required_quantity"] = demand["quantity"] if demand else listing["quantity"]
                buyer["offer_price"] = demand["target_price"] if demand else listing["asking_price"]
                buyer["distance_km"] = 0 if demand and demand["location"].lower() == listing["location"].lower() else 50
            return listing, buyers
        except AIRepositoryError:
            raise
        except Exception as exc:
            raise AIRepositoryError from exc

    def save_matches(self, token: str, farmer_id: str, listing_id: str, matches: list[dict]) -> None:
        rows = [{"listing_id": listing_id, "farmer_id": farmer_id, "buyer_id": item["buyer_id"], "match_score": item["match_score"], "explanation": item["explanation"]} for item in matches]
        if rows:
            self._client(token).table("buyer_matches").upsert(rows, on_conflict="listing_id,buyer_id").execute()