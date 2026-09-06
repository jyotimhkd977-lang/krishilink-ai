"""Protected AI prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import require_roles
from app.schemas.ai import BuyerMatchListResponse, DemandForecastInput, DemandForecastOutput, PricePredictionInput, PricePredictionOutput
from app.schemas.auth import Role, UserResponse
from app.services.ai_repository import AIRepository, AIRepositoryError
from app.services.demand_ai import DemandAIService
from app.services.matching_ai import MatchingAIService
from app.services.price_ai import PriceAIService

router = APIRouter(prefix="/ai")
bearer_scheme = HTTPBearer(auto_error=False)


def repository() -> AIRepository:
    return AIRepository()


@router.post("/price", response_model=PricePredictionOutput)
async def predict_price(payload: PricePredictionInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.farmer, Role.buyer)), repo: AIRepository = Depends(repository)) -> PricePredictionOutput:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    output = PriceAIService().predict(payload)
    try:
        repo.save_price(credentials.credentials, current_user.id, payload.model_dump(), output.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Prediction storage unavailable") from exc
    return output


@router.post("/demand", response_model=DemandForecastOutput)
async def forecast_demand(payload: DemandForecastInput, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.farmer, Role.buyer)), repo: AIRepository = Depends(repository)) -> DemandForecastOutput:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    output = DemandAIService().predict(payload)
    try:
        repo.save_demand(credentials.credentials, current_user.id, payload.model_dump(), output.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Forecast storage unavailable") from exc
    return output


@router.post("/matching/{listing_id}", response_model=BuyerMatchListResponse)
async def match_buyers(listing_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.farmer)), repo: AIRepository = Depends(repository)) -> BuyerMatchListResponse:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    try:
        listing, buyers = repo.get_listing_and_buyers(credentials.credentials, listing_id, current_user.id)
        ranked = MatchingAIService().rank(listing, buyers)
        repo.save_matches(credentials.credentials, current_user.id, listing_id, ranked)
        return BuyerMatchListResponse(listing_id=listing_id, ranked_buyers=ranked)
    except AIRepositoryError as exc:
        raise HTTPException(status_code=404, detail="Listing or matching data unavailable") from exc