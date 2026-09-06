"""Quality inspections and dispute workflow service."""

import mimetypes
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from fastapi import UploadFile
from supabase import Client, create_client

from app.core.config import get_settings

MAX_EVIDENCE_SIZE = 10 * 1024 * 1024
ALLOWED_EVIDENCE_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


def _has_evidence_signature(content: bytes, content_type: str) -> bool:
    return (
        (content_type == "image/jpeg" and content.startswith(b"\xff\xd8\xff"))
        or (content_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
        or (content_type == "image/webp" and content.startswith(b"RIFF") and content[8:12] == b"WEBP")
        or (content_type == "application/pdf" and content.startswith(b"%PDF-"))
    )


class QualityServiceError(Exception):
    """Raised when a quality or dispute operation is invalid."""


class QualityService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self, token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise QualityServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(token)
        return client

    def _audit(self, client: Client, actor_id: str, entity_type: str, entity_id: str, action: str, metadata: dict[str, Any] | None = None) -> None:
        client.table("audit_logs").insert({"actor_id": actor_id, "entity_type": entity_type, "entity_id": entity_id, "action": action, "metadata": metadata or {}}).execute()

    def create_inspection(self, token: str, inspector_id: str, order_id: str, values: dict[str, Any]) -> dict[str, Any]:
        client = self._client(token)
        try:
            order = client.table("orders").select("id").eq("id", order_id).single().execute().data
            if not order:
                raise QualityServiceError
            response = client.table("quality_inspections").upsert({"order_id": order_id, "inspector_id": inspector_id, **values}, on_conflict="order_id").execute()
            inspection = response.data[0]
            self._audit(client, inspector_id, "quality_inspection", inspection["id"], "QUALITY_INSPECTION_CREATED", {"status": values["status"]})
            return inspection
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc

    def confirm_quality(self, token: str, buyer_id: str, inspection_id: str) -> dict[str, Any]:
        client = self._client(token)
        try:
            inspection = client.table("quality_inspections").select("id,order_id").eq("id", inspection_id).single().execute().data
            if not inspection:
                raise QualityServiceError
            order = client.table("orders").select("buyer_id").eq("id", inspection["order_id"]).single().execute().data
            if not order or order["buyer_id"] != buyer_id:
                raise QualityServiceError
            response = client.table("quality_inspections").update({"buyer_confirmed": True, "buyer_confirmed_by": buyer_id, "buyer_confirmed_at": datetime.now(timezone.utc).isoformat()}).eq("id", inspection_id).execute()
            result = response.data[0]
            self._audit(client, buyer_id, "quality_inspection", inspection_id, "QUALITY_CONFIRMED")
            return result
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc

    def create_dispute(self, token: str, user_id: str, order_id: str, reason: str) -> dict[str, Any]:
        client = self._client(token)
        try:
            order = client.table("orders").select("buyer_id,farmer_id").eq("id", order_id).single().execute().data
            if not order or user_id not in {order["buyer_id"], order["farmer_id"]}:
                raise QualityServiceError
            existing = client.table("disputes").select("id").eq("order_id", order_id).in_("status", ["OPEN", "UNDER_REVIEW", "REFUND", "REPLACEMENT"]).execute()
            if existing.data:
                raise QualityServiceError
            response = client.table("disputes").insert({"order_id": order_id, "raised_by": user_id, "buyer_id": order["buyer_id"], "farmer_id": order["farmer_id"], "reason": reason}).execute()
            dispute = response.data[0]
            self._audit(client, user_id, "dispute", dispute["id"], "DISPUTE_OPENED")
            return dispute
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc

    def list_disputes(self, token: str) -> list[dict[str, Any]]:
        try:
            return self._client(token).table("disputes").select("*").order("created_at", desc=True).execute().data or []
        except Exception as exc:
            raise QualityServiceError from exc

    def review_dispute(self, token: str, admin_id: str, dispute_id: str, values: dict[str, Any]) -> dict[str, Any]:
        client = self._client(token)
        try:
            current = client.table("disputes").select("status").eq("id", dispute_id).single().execute().data
            if not current or current["status"] != "OPEN" or values["status"] != "UNDER_REVIEW":
                raise QualityServiceError
            response = client.table("disputes").update(values).eq("id", dispute_id).execute()
            result = response.data[0]
            self._audit(client, admin_id, "dispute", dispute_id, "DISPUTE_UNDER_REVIEW")
            return result
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc

    def decide_dispute(self, token: str, admin_id: str, dispute_id: str, status: str, note: str | None) -> dict[str, Any]:
        client = self._client(token)
        try:
            current = client.table("disputes").select("status").eq("id", dispute_id).single().execute().data
            if not current or current["status"] != "UNDER_REVIEW" or status not in {"REFUND", "REPLACEMENT"}:
                raise QualityServiceError
            response = client.table("disputes").update({"status": status, "resolution_note": note}).eq("id", dispute_id).execute()
            result = response.data[0]
            self._audit(client, admin_id, "dispute", dispute_id, f"DISPUTE_{status}")
            return result
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc

    def resolve_dispute(self, token: str, admin_id: str, dispute_id: str, note: str | None) -> dict[str, Any]:
        client = self._client(token)
        try:
            current = client.table("disputes").select("status").eq("id", dispute_id).single().execute().data
            if not current or current["status"] not in {"REFUND", "REPLACEMENT"}:
                raise QualityServiceError
            response = client.table("disputes").update({"status": "RESOLVED", "resolution_note": note, "resolved_by": admin_id}).eq("id", dispute_id).execute()
            result = response.data[0]
            self._audit(client, admin_id, "dispute", dispute_id, "DISPUTE_RESOLVED")
            return result
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc

    async def add_evidence(self, token: str, user_id: str, dispute_id: str, file: UploadFile) -> dict[str, Any]:
        content_type = file.content_type or ""
        if content_type not in ALLOWED_EVIDENCE_TYPES:
            raise QualityServiceError("Only JPEG, PNG, WebP, and PDF files are allowed")
        content = await file.read(MAX_EVIDENCE_SIZE + 1)
        if not content or len(content) > MAX_EVIDENCE_SIZE:
            raise QualityServiceError("Evidence must be between 1 byte and 10 MB")
        if not _has_evidence_signature(content, content_type):
            raise QualityServiceError("Evidence content does not match its declared format")
        try:
            client = self._client(token)
            dispute = client.table("disputes").select("id").eq("id", dispute_id).single().execute().data
            if not dispute:
                raise QualityServiceError
            extension = mimetypes.guess_extension(content_type) or ".bin"
            storage_path = f"{user_id}/{dispute_id}/{uuid4()}{extension}"
            client.storage.from_("dispute-evidence").upload(storage_path, content, {"content-type": content_type, "upsert": "false"})
            response = client.table("dispute_evidence").insert({"dispute_id": dispute_id, "uploaded_by": user_id, "storage_path": storage_path, "content_type": content_type, "file_size": len(content)}).execute()
            evidence = response.data[0]
            self._audit(client, user_id, "dispute", dispute_id, "DISPUTE_EVIDENCE_ADDED", {"evidence_id": evidence["id"]})
            return evidence
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc

    def create_evidence_url(self, token: str, user_id: str, dispute_id: str, evidence_id: str) -> str:
        try:
            client = self._client(token)
            evidence = client.table("dispute_evidence").select("storage_path").eq("id", evidence_id).eq("dispute_id", dispute_id).single().execute().data
            if not evidence:
                raise QualityServiceError
            result = client.storage.from_("dispute-evidence").create_signed_url(evidence["storage_path"], 300)
            return result.get("signedURL") or result.get("signedUrl") or result["signed_url"]
        except QualityServiceError:
            raise
        except Exception as exc:
            raise QualityServiceError from exc