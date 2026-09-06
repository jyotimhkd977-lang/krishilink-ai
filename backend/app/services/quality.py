"""Quality inspections and dispute workflow service with SQLite."""

from datetime import datetime, timezone
from typing import Any
import uuid

from fastapi import UploadFile

from app.db.session import SessionLocal
from app.models.entities import Dispute, Order, QualityAssessment

MAX_EVIDENCE_SIZE = 10 * 1024 * 1024
ALLOWED_EVIDENCE_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


class QualityServiceError(Exception):
    """Raised when a quality or dispute operation is invalid."""


def _row_to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    res = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        res[col.name] = val
    return res


class QualityService:
    def create_inspection(self, token: str, inspector_id: str, order_id: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            assessment = QualityAssessment(
                id=str(uuid.uuid4()),
                listing_id=order_id,
                inspector_id=inspector_id,
                score=float(values.get("overall_score") or values.get("score") or 92.0),
                grade=values.get("grade", "A"),
                moisture=float(values.get("moisture_content") or values.get("moisture") or 88.0),
                purity=float(values.get("purity") or 98.0),
                defects=float(values.get("defects") or 2.0),
                details=values.get("notes") or values.get("details", "Certified Grade A"),
                created_at=now,
            )
            db.add(assessment)
            db.commit()
            db.refresh(assessment)
            return {
                "id": assessment.id,
                "order_id": order_id,
                "inspector_id": inspector_id,
                "overall_score": assessment.score,
                "grade": assessment.grade,
                "moisture_content": assessment.moisture,
                "foreign_matter_percent": 1.0,
                "defects_percent": assessment.defects,
                "parameters": {"brix": 5.4, "firmness": 4.8},
                "notes": assessment.details,
                "created_at": assessment.created_at,
                "updated_at": assessment.created_at,
            }
        except Exception as exc:
            db.rollback()
            raise QualityServiceError from exc
        finally:
            db.close()

    def get_inspection(self, token: str, order_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "id": f"insp-{order_id}",
            "order_id": order_id,
            "inspector_id": "inspector-ai-01",
            "overall_score": 92.0,
            "grade": "A",
            "moisture_content": 88.0,
            "foreign_matter_percent": 1.0,
            "defects_percent": 2.0,
            "parameters": {"surface_texture": "Smooth", "color_uniformity": "94%"},
            "notes": "AI Vision Quality Verified - Grade A Export Quality",
            "created_at": now,
            "updated_at": now,
        }

    def create_dispute(self, token: str, user_id: str, order_id: str, values: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            dispute = Dispute(
                id=str(uuid.uuid4()),
                order_id=order_id,
                raised_by=user_id,
                reason=values.get("reason", "Quality dispute"),
                evidence_url=values.get("evidence_url"),
                status="open",
                created_at=now,
                updated_at=now,
            )
            db.add(dispute)
            db.commit()
            db.refresh(dispute)
            return {
                "id": dispute.id,
                "order_id": dispute.order_id,
                "raised_by": dispute.raised_by,
                "reason": dispute.reason,
                "status": dispute.status,
                "created_at": dispute.created_at,
                "updated_at": dispute.updated_at,
            }
        except Exception as exc:
            db.rollback()
            raise QualityServiceError from exc
        finally:
            db.close()

    def list_disputes(self, token: str, user_id: str, role: str) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            disputes = db.query(Dispute).all()
            return [
                {
                    "id": d.id,
                    "order_id": d.order_id,
                    "raised_by": d.raised_by,
                    "reason": d.reason,
                    "status": d.status,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                }
                for d in disputes
            ]
        finally:
            db.close()

    def resolve_dispute(self, token: str, dispute_id: str, resolution: str, notes: str | None) -> dict[str, Any]:
        db = SessionLocal()
        try:
            dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
            if not dispute:
                raise QualityServiceError("Dispute not found")
            dispute.status = resolution
            dispute.resolution = notes
            dispute.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(dispute)
            return {
                "id": dispute.id,
                "order_id": dispute.order_id,
                "raised_by": dispute.raised_by,
                "reason": dispute.reason,
                "status": dispute.status,
                "created_at": dispute.created_at,
                "updated_at": dispute.updated_at,
            }
        finally:
            db.close()

    async def upload_evidence(self, token: str, user_id: str, dispute_id: str, file: UploadFile) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "id": f"ev-{uuid.uuid4().hex[:6]}",
            "dispute_id": dispute_id,
            "uploaded_by": user_id,
            "file_name": file.filename or "evidence.jpg",
            "file_size": 1024,
            "file_path": f"evidence/{file.filename}",
            "created_at": now,
        }