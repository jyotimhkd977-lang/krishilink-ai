"""Protected review and trust score endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.trust import ReviewCreate, ReviewResponse, TrustScoreResponse
from app.services.trust import TrustService, TrustServiceError

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> TrustService:
    return TrustService()


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(payload: ReviewCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: TrustService = Depends(get_service)) -> ReviewResponse:
    try:
        return ReviewResponse(**service.create_review(credentials.credentials, payload.model_dump()))
    except TrustServiceError:
        raise HTTPException(status_code=409, detail="Review is not allowed or already exists")


@router.get("/users/{user_id}/reviews", response_model=list[ReviewResponse])
async def list_reviews(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: TrustService = Depends(get_service)) -> list[ReviewResponse]:
    try:
        return [ReviewResponse(**row) for row in service.list_reviews(credentials.credentials, user_id)]
    except TrustServiceError:
        raise HTTPException(status_code=404, detail="Reviews unavailable")


@router.get("/trust-scores/me", response_model=TrustScoreResponse)
async def my_trust_score(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: TrustService = Depends(get_service)) -> TrustScoreResponse:
    try:
        return TrustScoreResponse(**service.get_score(credentials.credentials, current_user.id))
    except TrustServiceError:
        raise HTTPException(status_code=404, detail="Trust score unavailable")


@router.get("/trust-scores/{user_id}", response_model=TrustScoreResponse)
async def get_trust_score(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: TrustService = Depends(get_service)) -> TrustScoreResponse:
    try:
        return TrustScoreResponse(**service.get_score(credentials.credentials, user_id))
    except TrustServiceError:
        raise HTTPException(status_code=404, detail="Trust score unavailable")