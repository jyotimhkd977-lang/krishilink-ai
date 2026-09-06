"""Quality inspection and dispute management endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user, require_roles
from app.schemas.auth import Role, UserResponse
from app.schemas.quality import (
    BuyerConfirmation, DisputeCreate, DisputeDecision, DisputeEvidenceResponse,
    DisputeResponse, QualityInspectionCreate, QualityInspectionResponse,
    DisputeResolve,
)
from app.services.quality import QualityService, QualityServiceError

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> QualityService:
    return QualityService()


@router.post("/orders/{order_id}/quality-inspections", response_model=QualityInspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(order_id: str, payload: QualityInspectionCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.logistics, Role.admin)), service: QualityService = Depends(get_service)) -> QualityInspectionResponse:
    try:
        return QualityInspectionResponse(**service.create_inspection(credentials.credentials, current_user.id, order_id, payload.model_dump()))
    except QualityServiceError:
        raise HTTPException(status_code=409, detail="Quality inspection could not be created")


@router.patch("/quality-inspections/{inspection_id}/confirm", response_model=QualityInspectionResponse)
async def confirm_inspection(inspection_id: str, payload: BuyerConfirmation, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer)), service: QualityService = Depends(get_service)) -> QualityInspectionResponse:
    if not payload.confirmed:
        raise HTTPException(status_code=422, detail="Buyer confirmation must be true")
    try:
        return QualityInspectionResponse(**service.confirm_quality(credentials.credentials, current_user.id, inspection_id))
    except QualityServiceError:
        raise HTTPException(status_code=403, detail="Quality confirmation not permitted")


@router.post("/disputes", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(payload: DisputeCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer, Role.farmer)), service: QualityService = Depends(get_service)) -> DisputeResponse:
    try:
        return DisputeResponse(**service.create_dispute(credentials.credentials, current_user.id, payload.order_id, payload.reason))
    except QualityServiceError:
        raise HTTPException(status_code=403, detail="Dispute could not be created")


@router.get("/disputes", response_model=list[DisputeResponse])
async def list_disputes(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: QualityService = Depends(get_service)) -> list[DisputeResponse]:
    try:
        return [DisputeResponse(**row) for row in service.list_disputes(credentials.credentials)]
    except QualityServiceError:
        raise HTTPException(status_code=404, detail="Disputes unavailable")


@router.post("/disputes/{dispute_id}/evidence", response_model=DisputeEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def add_evidence(dispute_id: str, file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer, Role.farmer)), service: QualityService = Depends(get_service)) -> DisputeEvidenceResponse:
    try:
        return DisputeEvidenceResponse(**await service.add_evidence(credentials.credentials, current_user.id, dispute_id, file))
    except QualityServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc) or "Evidence upload failed")


@router.get("/disputes/{dispute_id}/evidence/{evidence_id}/url", response_model=dict)
async def get_evidence_url(dispute_id: str, evidence_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer, Role.farmer, Role.admin)), service: QualityService = Depends(get_service)) -> dict:
    try:
        url = service.create_evidence_url(credentials.credentials, current_user.id, dispute_id, evidence_id)
        return {"url": url, "expires_in": 300}
    except QualityServiceError:
        raise HTTPException(status_code=404, detail="Evidence not found")


@router.patch("/disputes/{dispute_id}/review", response_model=DisputeResponse)
async def review_dispute(dispute_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.admin)), service: QualityService = Depends(get_service)) -> DisputeResponse:
    try:
        return DisputeResponse(**service.review_dispute(credentials.credentials, current_user.id, dispute_id, {"status": "UNDER_REVIEW"}))
    except QualityServiceError:
        raise HTTPException(status_code=409, detail="Dispute cannot enter review")


@router.patch("/disputes/{dispute_id}/decision", response_model=DisputeResponse)
async def decide_dispute(dispute_id: str, payload: DisputeDecision, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.admin)), service: QualityService = Depends(get_service)) -> DisputeResponse:
    if payload.status.value not in {"REFUND", "REPLACEMENT"}:
        raise HTTPException(status_code=422, detail="Decision must be REFUND or REPLACEMENT")
    try:
        return DisputeResponse(**service.decide_dispute(credentials.credentials, current_user.id, dispute_id, payload.status.value, payload.resolution_note))
    except QualityServiceError:
        raise HTTPException(status_code=409, detail="Dispute decision is invalid")


@router.patch("/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(dispute_id: str, payload: DisputeResolve, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.admin)), service: QualityService = Depends(get_service)) -> DisputeResponse:
    try:
        return DisputeResponse(**service.resolve_dispute(credentials.credentials, current_user.id, dispute_id, payload.resolution_note))
    except QualityServiceError:
        raise HTTPException(status_code=409, detail="Dispute cannot be resolved")