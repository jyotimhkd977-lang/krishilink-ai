"""Protected delivery and vehicle tracking endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user, require_roles
from app.schemas.auth import Role, UserResponse
from app.schemas.logistics import (
    DeliveryAssignment, DeliveryCreate, DeliveryResponse, DeliveryStatusUpdate,
    LocationUpdate, VehicleCreate, VehicleLocationResponse, VehicleResponse,
)
from app.services.logistics import LogisticsService, LogisticsServiceError

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> LogisticsService:
    return LogisticsService()


def logistics_error() -> HTTPException:
    return HTTPException(status_code=409, detail="Logistics operation is invalid")


@router.post("/deliveries", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(payload: DeliveryCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.logistics, Role.admin)), service: LogisticsService = Depends(get_service)) -> DeliveryResponse:
    try:
        return DeliveryResponse(**service.create_delivery(credentials.credentials, payload.model_dump(mode="json")))
    except LogisticsServiceError:
        raise logistics_error()


@router.get("/deliveries", response_model=list[DeliveryResponse])
async def list_deliveries(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: LogisticsService = Depends(get_service)) -> list[DeliveryResponse]:
    try:
        return [DeliveryResponse(**row) for row in service.list_deliveries(credentials.credentials, current_user.id, current_user.role.value)]
    except LogisticsServiceError:
        raise HTTPException(status_code=404, detail="Deliveries unavailable")


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: LogisticsService = Depends(get_service)) -> DeliveryResponse:
    try:
        return DeliveryResponse(**service.get_delivery(credentials.credentials, delivery_id))
    except LogisticsServiceError:
        raise HTTPException(status_code=404, detail="Delivery not found")


@router.get("/deliveries/{delivery_id}/locations", response_model=list[VehicleLocationResponse])
async def list_locations(delivery_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: LogisticsService = Depends(get_service)) -> list[VehicleLocationResponse]:
    try:
        return [VehicleLocationResponse(**row) for row in service.list_locations(credentials.credentials, delivery_id)]
    except LogisticsServiceError:
        raise HTTPException(status_code=404, detail="Vehicle locations unavailable")


@router.patch("/deliveries/{delivery_id}/assignment", response_model=DeliveryResponse)
async def assign_delivery(delivery_id: str, payload: DeliveryAssignment, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.logistics, Role.admin)), service: LogisticsService = Depends(get_service)) -> DeliveryResponse:
    try:
        return DeliveryResponse(**service.assign(credentials.credentials, delivery_id, payload.model_dump(mode="json")))
    except LogisticsServiceError:
        raise logistics_error()


@router.patch("/deliveries/{delivery_id}/status", response_model=DeliveryResponse)
async def update_delivery_status(delivery_id: str, payload: DeliveryStatusUpdate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: LogisticsService = Depends(get_service)) -> DeliveryResponse:
    try:
        return DeliveryResponse(**service.update_status(credentials.credentials, delivery_id, payload.model_dump(mode="json")))
    except LogisticsServiceError:
        raise logistics_error()


@router.post("/deliveries/{delivery_id}/location", response_model=VehicleLocationResponse, status_code=status.HTTP_201_CREATED)
async def update_location(delivery_id: str, payload: LocationUpdate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.logistics)), service: LogisticsService = Depends(get_service)) -> VehicleLocationResponse:
    try:
        return VehicleLocationResponse(**service.update_location(credentials.credentials, current_user.id, delivery_id, payload.model_dump()))
    except LogisticsServiceError as exc:
        raise HTTPException(status_code=429 if "10 seconds" in str(exc) else 403, detail=str(exc) or "Location update not permitted")


@router.post("/deliveries/{delivery_id}/route", response_model=DeliveryResponse)
async def optimize_route(delivery_id: str, route: list[LocationUpdate], credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.logistics, Role.admin)), service: LogisticsService = Depends(get_service)) -> DeliveryResponse:
    try:
        points = [point.model_dump() for point in route]
        return DeliveryResponse(**service.optimize_route(credentials.credentials, delivery_id, points))
    except LogisticsServiceError:
        raise logistics_error()


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(payload: VehicleCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.logistics, Role.admin)), service: LogisticsService = Depends(get_service)) -> VehicleResponse:
    try:
        return VehicleResponse(**service.create_vehicle(credentials.credentials, payload.model_dump()))
    except LogisticsServiceError as exc:
        raise logistics_error() from exc


@router.get("/vehicles", response_model=list[VehicleResponse])
async def list_vehicles(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.logistics, Role.admin)), service: LogisticsService = Depends(get_service)) -> list[VehicleResponse]:
    try:
        return [VehicleResponse(**row) for row in service.list_vehicles(credentials.credentials)]
    except LogisticsServiceError:
        raise HTTPException(status_code=404, detail="Vehicles unavailable")