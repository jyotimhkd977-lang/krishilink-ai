"""Delivery assignment, tracking, and route operations."""

import math
import threading
import time
from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


class LogisticsServiceError(Exception):
    """Raised when a logistics operation is invalid or unavailable."""


class LocationRateLimiter:
    def __init__(self, interval_seconds: float = 10) -> None:
        self.interval_seconds = interval_seconds
        self.last_update: dict[str, float] = {}
        self.lock = threading.Lock()

    def allow(self, driver_id: str) -> bool:
        now = time.monotonic()
        with self.lock:
            previous = self.last_update.get(driver_id)
            if previous is not None and now - previous < self.interval_seconds:
                return False
            self.last_update[driver_id] = now
            return True


location_rate_limiter = LocationRateLimiter()


class LogisticsService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise LogisticsServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(token)
        return client

    def create_delivery(self, token: str, values: dict[str, Any]) -> dict[str, Any]:
        client = self._client(token)
        try:
            order = client.table("orders").select("id,buyer_id,farmer_id").eq("id", values["order_id"]).single().execute().data
            if not order:
                raise LogisticsServiceError
            response = client.table("deliveries").insert({**values, "farmer_id": order["farmer_id"], "buyer_id": order["buyer_id"]}).execute()
            return response.data[0]
        except LogisticsServiceError:
            raise
        except Exception as exc:
            raise LogisticsServiceError from exc

    def list_deliveries(self, token: str, user_id: str, role: str) -> list[dict[str, Any]]:
        try:
            client = self._client(token)
            query = client.table("deliveries").select("*")
            if role == "farmer": query = query.eq("farmer_id", user_id)
            elif role == "buyer": query = query.eq("buyer_id", user_id)
            elif role == "logistics": query = query.eq("driver_id", user_id)
            response = query.order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise LogisticsServiceError from exc

    def get_delivery(self, token: str, delivery_id: str) -> dict[str, Any]:
        try:
            response = self._client(token).table("deliveries").select("*").eq("id", delivery_id).single().execute()
            if not response.data:
                raise LogisticsServiceError
            return response.data
        except LogisticsServiceError:
            raise
        except Exception as exc:
            raise LogisticsServiceError from exc

    def assign(self, token: str, delivery_id: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            data = {**values, "status": "assigned"}
            response = self._client(token).table("deliveries").update(data).eq("id", delivery_id).execute()
            if not response.data:
                raise LogisticsServiceError
            return response.data[0]
        except LogisticsServiceError:
            raise
        except Exception as exc:
            raise LogisticsServiceError from exc

    def update_status(self, token: str, delivery_id: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client(token).table("deliveries").update(values).eq("id", delivery_id).execute()
            if not response.data:
                raise LogisticsServiceError
            return response.data[0]
        except Exception as exc:
            raise LogisticsServiceError from exc

    def update_location(self, token: str, driver_id: str, delivery_id: str, values: dict[str, Any]) -> dict[str, Any]:
        if not location_rate_limiter.allow(driver_id):
            raise LogisticsServiceError("Location updates must be at least 10 seconds apart")
        try:
            delivery = self.get_delivery(token, delivery_id)
            if delivery.get("driver_id") != driver_id or not delivery.get("vehicle_id"):
                raise LogisticsServiceError
            response = self._client(token).rpc("record_vehicle_location", {
                "p_delivery_id": delivery_id,
                "p_vehicle_id": delivery["vehicle_id"],
                "p_driver_id": driver_id,
                "p_latitude": values["latitude"],
                "p_longitude": values["longitude"],
                "p_speed_kph": values.get("speed_kph"),
                "p_heading": values.get("heading"),
            }).execute()
            return response.data[0] if isinstance(response.data, list) else response.data
        except LogisticsServiceError:
            raise
        except Exception as exc:
            raise LogisticsServiceError from exc

    def optimize_route(self, token: str, delivery_id: str, route: list[dict[str, float]]) -> dict[str, Any]:
        if not route:
            raise LogisticsServiceError
        # Prototype route ordering: nearest-neighbor over supplied coordinates.
        remaining = route[1:].copy()
        optimized = [route[0]]
        while remaining:
            current = optimized[-1]
            next_stop = min(remaining, key=lambda stop: math.hypot(stop["latitude"] - current["latitude"], stop["longitude"] - current["longitude"]))
            remaining.remove(next_stop)
            optimized.append(next_stop)
        try:
            response = self._client(token).table("deliveries").update({"route": optimized}).eq("id", delivery_id).execute()
            if not response.data:
                raise LogisticsServiceError
            return response.data[0]
        except LogisticsServiceError:
            raise
        except Exception as exc:
            raise LogisticsServiceError from exc

    def list_locations(self, token: str, delivery_id: str) -> list[dict[str, Any]]:
        try:
            response = self._client(token).table("vehicle_locations").select("*").eq("delivery_id", delivery_id).order("recorded_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise LogisticsServiceError from exc

    def create_vehicle(self, token: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client(token).table("vehicles").insert(values).execute()
            return response.data[0]
        except Exception as exc:
            raise LogisticsServiceError from exc

    def list_vehicles(self, token: str) -> list[dict[str, Any]]:
        try:
            response = self._client(token).table("vehicles").select("*").order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise LogisticsServiceError from exc