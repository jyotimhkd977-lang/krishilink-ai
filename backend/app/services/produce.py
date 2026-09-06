"""Farm, listing, and produce image persistence."""

import mimetypes
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from supabase import Client, create_client

from app.core.config import get_settings
from app.schemas.produce import ListingStatus

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _has_image_signature(content: bytes, content_type: str) -> bool:
    return (
        (content_type == "image/jpeg" and content.startswith(b"\xff\xd8\xff"))
        or (content_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
        or (content_type == "image/webp" and content.startswith(b"RIFF") and content[8:12] == b"WEBP")
    )


class ProduceServiceError(Exception):
    """Raised when farm or listing persistence fails."""


class ProduceService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, access_token: str | None = None) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise ProduceServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        if access_token:
            client.postgrest.auth(access_token)
        return client

    def create_farm(self, access_token: str, farmer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client(access_token).table("farms").insert({**values, "farmer_id": farmer_id}).execute()
            return response.data[0]
        except Exception as exc:
            raise ProduceServiceError from exc

    def list_farms(self, access_token: str, farmer_id: str) -> list[dict[str, Any]]:
        try:
            response = self._client(access_token).table("farms").select("*").eq("farmer_id", farmer_id).execute()
            return response.data or []
        except Exception as exc:
            raise ProduceServiceError from exc

    def create_listing(self, access_token: str, farmer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client(access_token).table("produce_listings").insert({**values, "farmer_id": farmer_id}).execute()
            return response.data[0]
        except Exception as exc:
            raise ProduceServiceError from exc

    def list_listings(self, access_token: str | None, farmer_id: str | None, role: str | None) -> list[dict[str, Any]]:
        try:
            query = self._client(access_token).table("produce_listings").select("*,produce_images(*)")
            if role == "farmer" and farmer_id:
                query = query.eq("farmer_id", farmer_id)
            else:
                query = query.eq("status", ListingStatus.active.value)
            response = query.order("created_at", desc=True).execute()
            return response.data or []
        except Exception as exc:
            raise ProduceServiceError from exc

    def get_listing(self, access_token: str | None, listing_id: str, farmer_id: str | None, role: str | None) -> dict[str, Any]:
        listings = self.list_listings(access_token, farmer_id if role == "farmer" else None, role)
        listing = next((item for item in listings if item.get("id") == listing_id), None)
        if not listing:
            raise ProduceServiceError
        return listing

    def update_listing(self, access_token: str, listing_id: str, farmer_id: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client(access_token).table("produce_listings").update(values).eq("id", listing_id).eq("farmer_id", farmer_id).execute()
            if not response.data:
                raise ProduceServiceError
            return response.data[0]
        except Exception as exc:
            raise ProduceServiceError from exc

    def delete_listing(self, access_token: str, listing_id: str, farmer_id: str) -> None:
        try:
            self._client(access_token).table("produce_listings").delete().eq("id", listing_id).eq("farmer_id", farmer_id).execute()
        except Exception as exc:
            raise ProduceServiceError from exc

    async def upload_image(self, access_token: str, farmer_id: str, listing_id: str, image: UploadFile) -> dict[str, Any]:
        content_type = image.content_type or ""
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise ProduceServiceError("Only JPEG, PNG, and WebP images are allowed")
        content = await image.read(MAX_IMAGE_SIZE + 1)
        if len(content) > MAX_IMAGE_SIZE or not content:
            raise ProduceServiceError("Image must be between 1 byte and 5 MB")
        if not _has_image_signature(content, content_type):
            raise ProduceServiceError("Image content does not match its declared format")

        extension = mimetypes.guess_extension(content_type) or ".img"
        storage_path = f"{farmer_id}/{listing_id}/{uuid4()}{extension}"
        try:
            client = self._client(access_token)
            client.storage.from_("produce-images").upload(
                storage_path,
                content,
                {"content-type": content_type, "upsert": "false"},
            )
            response = client.table("produce_images").insert({
                "listing_id": listing_id,
                "farmer_id": farmer_id,
                "storage_path": storage_path,
                "content_type": content_type,
                "file_size": len(content),
            }).execute()
            return response.data[0]
        except Exception as exc:
            raise ProduceServiceError from exc

    def create_image_url(self, access_token: str, user_id: str, role: str, listing_id: str, image_id: str) -> str:
        try:
            client = self._client(access_token)
            image = client.table("produce_images").select("storage_path,produce_listings!inner(farmer_id,status)").eq("id", image_id).eq("listing_id", listing_id).single().execute().data
            if not image:
                raise ProduceServiceError
            listing = image["produce_listings"]
            if not (role == "farmer" and listing["farmer_id"] == user_id) and not (role != "farmer" and listing["status"] == "active"):
                raise ProduceServiceError
            result = client.storage.from_("produce-images").create_signed_url(image["storage_path"], 300)
            return result.get("signedURL") or result.get("signedUrl") or result["signed_url"]
        except ProduceServiceError:
            raise
        except Exception as exc:
            raise ProduceServiceError from exc