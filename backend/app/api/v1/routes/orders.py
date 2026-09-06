"""Protected order management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.orders import OrderResponse, OrderStatusUpdate
from app.services.orders import OrderService, OrderServiceError

router = APIRouter(prefix="/orders")
bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> OrderService:
    return OrderService()


def order_failure() -> HTTPException:
    return HTTPException(status_code=409, detail="Order operation is invalid")


@router.post("/from-offer/{offer_id}", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    offer_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: OrderService = Depends(get_service),
) -> OrderResponse:
    try:
        return OrderResponse(**service.create_from_offer(credentials.credentials, offer_id))
    except OrderServiceError:
        raise order_failure()


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: OrderService = Depends(get_service),
) -> list[OrderResponse]:
    try:
        rows = service.list_orders(credentials.credentials, current_user.id, current_user.role.value)
        return [OrderResponse(**row) for row in rows]
    except OrderServiceError:
        raise HTTPException(status_code=404, detail="Orders unavailable")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: OrderService = Depends(get_service),
) -> OrderResponse:
    try:
        return OrderResponse(**service.get_order(credentials.credentials, order_id))
    except OrderServiceError:
        raise HTTPException(status_code=404, detail="Order not found")


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    payload: OrderStatusUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: OrderService = Depends(get_service),
) -> OrderResponse:
    try:
        return OrderResponse(**service.advance_status(credentials.credentials, order_id, payload.status.value, payload.note))
    except OrderServiceError:
        raise order_failure()