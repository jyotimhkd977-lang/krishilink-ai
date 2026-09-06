"""Farm and produce listing endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user, get_optional_current_user, require_roles
from app.schemas.auth import Role, UserResponse
from app.schemas.produce import (
    FarmCreate,
    FarmResponse,
    ProduceListingCreate,
    ProduceListingResponse,
    ProduceListingUpdate,
)
from app.services.produce import ProduceService, ProduceServiceError

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> ProduceService:
    return ProduceService()


def _service_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")


@router.post("/farms", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    payload: FarmCreate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(require_roles(Role.farmer)),
    service: ProduceService = Depends(get_service),
) -> FarmResponse:
    try:
        return FarmResponse(**service.create_farm(credentials.credentials, current_user.id, payload.model_dump()))
    except ProduceServiceError:
        raise HTTPException(status_code=403, detail="Farm creation not permitted")


@router.get("/farms", response_model=list[FarmResponse])
async def list_farms(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(require_roles(Role.farmer)),
    service: ProduceService = Depends(get_service),
) -> list[FarmResponse]:
    try:
        return [FarmResponse(**farm) for farm in service.list_farms(credentials.credentials, current_user.id)]
    except ProduceServiceError:
        raise _service_error()


@router.post("/listings", response_model=ProduceListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ProduceListingCreate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(require_roles(Role.farmer)),
    service: ProduceService = Depends(get_service),
) -> ProduceListingResponse:
    try:
        data = service.create_listing(credentials.credentials, current_user.id, payload.model_dump(mode="json"))
        return ProduceListingResponse(**data, images=[])
    except ProduceServiceError:
        raise HTTPException(status_code=403, detail="Listing creation not permitted")


@router.get("/listings", response_model=list[ProduceListingResponse])
async def list_listings(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: UserResponse | None = Depends(get_optional_current_user),
    service: ProduceService = Depends(get_service),
) -> list[ProduceListingResponse]:
    token = credentials.credentials if credentials else None
    role = current_user.role.value if current_user else None
    farmer_id = current_user.id if current_user and current_user.role == Role.farmer else None
    try:
        return [ProduceListingResponse(**listing) for listing in service.list_listings(token, farmer_id, role)]
    except ProduceServiceError:
        raise _service_error()


@router.get("/listings/{listing_id}", response_model=ProduceListingResponse)
async def get_listing(
    listing_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: UserResponse | None = Depends(get_optional_current_user),
    service: ProduceService = Depends(get_service),
) -> ProduceListingResponse:
    token = credentials.credentials if credentials else None
    role = current_user.role.value if current_user else None
    farmer_id = current_user.id if current_user and current_user.role == Role.farmer else None
    try:
        return ProduceListingResponse(**service.get_listing(token, listing_id, farmer_id, role))
    except ProduceServiceError:
        raise _service_error()


@router.put("/listings/{listing_id}", response_model=ProduceListingResponse)
async def update_listing(
    listing_id: str,
    payload: ProduceListingUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(require_roles(Role.farmer)),
    service: ProduceService = Depends(get_service),
) -> ProduceListingResponse:
    try:
        data = service.update_listing(credentials.credentials, listing_id, current_user.id, payload.model_dump(exclude_none=True, mode="json"))
        return ProduceListingResponse(**data, images=[])
    except ProduceServiceError:
        raise _service_error()


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(require_roles(Role.farmer)),
    service: ProduceService = Depends(get_service),
) -> None:
    try:
        service.delete_listing(credentials.credentials, listing_id, current_user.id)
    except ProduceServiceError:
        raise _service_error()


@router.post("/listings/{listing_id}/images", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_listing_image(
    listing_id: str,
    image: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(require_roles(Role.farmer)),
    service: ProduceService = Depends(get_service),
) -> dict:
    try:
        return await service.upload_image(credentials.credentials, current_user.id, listing_id, image)
    except ProduceServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc) or "Image upload failed")


@router.get("/listings/{listing_id}/images/{image_id}/url", response_model=dict)
async def get_listing_image_url(
    listing_id: str,
    image_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: ProduceService = Depends(get_service),
) -> dict:
    try:
        url = service.create_image_url(credentials.credentials, current_user.id, current_user.role.value, listing_id, image_id)
        return {"url": url, "expires_in": 300}
    except ProduceServiceError:
        raise HTTPException(status_code=404, detail="Image not found")