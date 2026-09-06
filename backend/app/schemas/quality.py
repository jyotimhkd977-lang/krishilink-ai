"""Quality inspection and dispute schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class QualityStatus(str, Enum):
    approved = "APPROVED"
    rejected = "REJECTED"
    issue_found = "ISSUE_FOUND"


class DisputeStatus(str, Enum):
    open = "OPEN"
    under_review = "UNDER_REVIEW"
    refund = "REFUND"
    replacement = "REPLACEMENT"
    resolved = "RESOLVED"


class QualityInspectionCreate(BaseModel):
    status: QualityStatus
    ai_quality_score: float | None = Field(default=None, ge=0, le=100)
    ai_quality_label: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)


class QualityInspectionResponse(QualityInspectionCreate):
    id: str
    order_id: str
    inspector_id: str
    buyer_confirmed: bool
    buyer_confirmed_by: str | None = None
    buyer_confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BuyerConfirmation(BaseModel):
    confirmed: bool = True


class DisputeCreate(BaseModel):
    order_id: str
    reason: str = Field(min_length=1, max_length=2000)


class DisputeDecision(BaseModel):
    status: DisputeStatus
    resolution_note: str | None = Field(default=None, max_length=2000)


class DisputeResolve(BaseModel):
    resolution_note: str | None = Field(default=None, max_length=2000)


class DisputeResponse(DisputeCreate):
    id: str
    order_id: str
    raised_by: str
    buyer_id: str
    farmer_id: str
    status: DisputeStatus
    resolution_note: str | None = None
    resolved_by: str | None = None
    created_at: datetime
    updated_at: datetime


class DisputeEvidenceResponse(BaseModel):
    id: str
    dispute_id: str
    uploaded_by: str
    storage_path: str
    content_type: str
    file_size: int
    created_at: datetime