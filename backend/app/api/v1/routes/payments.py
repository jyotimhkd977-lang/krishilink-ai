"""Protected prototype payment and settlement endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user, require_roles
from app.schemas.auth import Role, UserResponse
from app.schemas.payments import PaymentCreate, PaymentResponse, SettlementResponse
from app.services.payments import PaymentService, PaymentServiceError

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> PaymentService:
    return PaymentService()


def payment_error() -> HTTPException:
    return HTTPException(status_code=409, detail="Payment operation is invalid")


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payload: PaymentCreate, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer)), service: PaymentService = Depends(get_service)) -> PaymentResponse:
    try:
        return PaymentResponse(**service.create(credentials.credentials, payload.order_id, payload.idempotency_key))
    except PaymentServiceError:
        raise payment_error()


@router.post("/payments/{payment_id}/simulate", response_model=PaymentResponse)
async def simulate_payment(payment_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.buyer)), service: PaymentService = Depends(get_service)) -> PaymentResponse:
    try:
        return PaymentResponse(**service.simulate(credentials.credentials, payment_id))
    except PaymentServiceError:
        raise payment_error()


@router.post("/payments/{payment_id}/delivery-confirmed", response_model=PaymentResponse)
async def confirm_delivery(payment_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: PaymentService = Depends(get_service)) -> PaymentResponse:
    try:
        return PaymentResponse(**service.confirm_delivery(credentials.credentials, payment_id))
    except PaymentServiceError:
        raise payment_error()


@router.post("/payments/{payment_id}/release", response_model=SettlementResponse)
async def release_settlement(payment_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(require_roles(Role.admin, Role.logistics)), service: PaymentService = Depends(get_service)) -> SettlementResponse:
    try:
        return SettlementResponse(**service.release(credentials.credentials, payment_id))
    except PaymentServiceError:
        raise payment_error()


@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: PaymentService = Depends(get_service)) -> list[PaymentResponse]:
    try:
        return [PaymentResponse(**row) for row in service.list_payments(credentials.credentials)]
    except PaymentServiceError:
        raise HTTPException(status_code=404, detail="Payments unavailable")


@router.get("/settlements", response_model=list[SettlementResponse])
async def list_settlements(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: PaymentService = Depends(get_service)) -> list[SettlementResponse]:
    try:
        return [SettlementResponse(**row) for row in service.list_settlements(credentials.credentials)]
    except PaymentServiceError:
        raise HTTPException(status_code=404, detail="Settlements unavailable")