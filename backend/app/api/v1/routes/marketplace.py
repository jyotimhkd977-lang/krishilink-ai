"""Marketplace search, demand, offer, and negotiation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user, require_roles
from app.schemas.auth import Role, UserResponse
from app.schemas.marketplace import (
    DemandCreate, DemandResponse, NegotiationCreate, NegotiationMessageCreate,
    NegotiationMessageResponse, NegotiationResponse, OfferCreate, OfferDecision,
    OfferResponse,
)
from app.schemas.produce import ProduceListingResponse
from app.services.marketplace import MarketplaceService, MarketplaceServiceError
from app.services.produce import ProduceService, ProduceServiceError

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_marketplace_service() -> MarketplaceService:
    return MarketplaceService()


def get_produce_service() -> ProduceService:
    return ProduceService()


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Marketplace resource not found")


@router.get("/marketplace/listings", response_model=list[ProduceListingResponse])
async def search_listings(
    crop: str | None = None,
    location: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    min_quantity: float | None = Query(default=None, gt=0),
    quality_score: float | None = Query(default=None, ge=0, le=100),
    quality_grade: str | None = None,
    verified_farmer: bool | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: ProduceService = Depends(get_produce_service),
) -> list[ProduceListingResponse]:
    try:
        client = service._client(credentials.credentials)
        query = client.table("produce_listings").select("*,produce_images(*),users!inner(farmer_profiles!inner(verified))").eq("status", "active")
        if crop: query = query.ilike("crop", f"%{crop}%")
        if location: query = query.ilike("location", f"%{location}%")
        if min_price is not None: query = query.gte("asking_price", min_price)
        if max_price is not None: query = query.lte("asking_price", max_price)
        if min_quantity is not None: query = query.gte("quantity", min_quantity)
        if quality_score is not None: query = query.gte("quality_score", quality_score)
        if quality_grade: query = query.ilike("quality_grade", f"%{quality_grade}%")
        if verified_farmer is not None:
            query = query.eq("users.farmer_profiles.verified", verified_farmer)
        response = query.order("created_at", desc=True).execute()
        return [ProduceListingResponse(**item) for item in (response.data or [])]
    except Exception as exc:
        raise not_found() from exc


@router.post("/demands", response_model=DemandResponse, status_code=status.HTTP_201_CREATED)
async def create_demand(payload: DemandCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer)), service: MarketplaceService = Depends(get_marketplace_service)) -> DemandResponse:
    try:
        return DemandResponse(**service.create_demand(credentials.credentials, current_user.id, payload.model_dump(mode="json")))
    except MarketplaceServiceError:
        raise HTTPException(status_code=403, detail="Demand creation not permitted")


@router.get("/demands", response_model=list[DemandResponse])
async def list_demands(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: MarketplaceService = Depends(get_marketplace_service)) -> list[DemandResponse]:
    try:
        return [DemandResponse(**item) for item in service.list_demands(credentials.credentials)]
    except MarketplaceServiceError:
        raise not_found()


@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(payload: OfferCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer)), service: MarketplaceService = Depends(get_marketplace_service)) -> OfferResponse:
    try:
        return OfferResponse(**service.create_offer(credentials.credentials, current_user.id, payload.model_dump(mode="json")))
    except MarketplaceServiceError:
        raise HTTPException(status_code=409, detail="Offer is invalid or already active")


@router.get("/offers", response_model=list[OfferResponse])
async def list_offers(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: MarketplaceService = Depends(get_marketplace_service)) -> list[OfferResponse]:
    try:
        return [OfferResponse(**item) for item in service.list_offers(credentials.credentials, current_user.id, current_user.role.value)]
    except MarketplaceServiceError:
        raise not_found()


@router.patch("/offers/{offer_id}", response_model=OfferResponse)
async def decide_offer(offer_id: str, payload: OfferDecision, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.farmer)), service: MarketplaceService = Depends(get_marketplace_service)) -> OfferResponse:
    if payload.status not in {"accepted", "rejected"}:
        raise HTTPException(status_code=422, detail="Offer status must be accepted or rejected")
    try:
        return OfferResponse(**service.decide_offer(credentials.credentials, current_user.id, offer_id, payload.status.value))
    except MarketplaceServiceError:
        raise not_found()


@router.post("/negotiations", response_model=NegotiationResponse, status_code=status.HTTP_201_CREATED)
async def create_negotiation(payload: NegotiationCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: MarketplaceService = Depends(get_marketplace_service)) -> NegotiationResponse:
    try:
        return NegotiationResponse(**service.create_negotiation(credentials.credentials, current_user.id, current_user.role.value, payload.offer_id))
    except MarketplaceServiceError:
        raise not_found()


@router.post("/negotiations/{negotiation_id}/messages", response_model=NegotiationMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(negotiation_id: str, payload: NegotiationMessageCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: MarketplaceService = Depends(get_marketplace_service)) -> NegotiationMessageResponse:
    try:
        return NegotiationMessageResponse(**service.send_message(credentials.credentials, current_user.id, negotiation_id, payload.message))
    except MarketplaceServiceError:
        raise not_found()


@router.get("/negotiations/{negotiation_id}/messages", response_model=list[NegotiationMessageResponse])
async def list_messages(negotiation_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: MarketplaceService = Depends(get_marketplace_service)) -> list[NegotiationMessageResponse]:
    try:
        return [NegotiationMessageResponse(**item) for item in service.list_messages(credentials.credentials, current_user.id, negotiation_id)]
    except MarketplaceServiceError:
        raise not_found()