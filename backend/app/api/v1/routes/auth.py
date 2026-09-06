"""Supabase Auth endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import GENERIC_AUTH_ERROR, get_current_user
from app.core.security import require_roles
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    Role,
    UserResponse,
)
from app.schemas.profiles import (
    BuyerProfileUpdate,
    FarmerProfileUpdate,
    ProfileListResponse,
    ProfileResponse,
)
from app.services.auth import AuthService, AuthServiceError
from app.services.profiles import ProfileService, ProfileServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")
bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    return AuthService()


def get_profile_service() -> ProfileService:
    return ProfileService()


def _auth_failure() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    if payload.role.value in {"admin", "logistics"}:
        raise HTTPException(status_code=403, detail="Privileged roles require administrator provisioning")
    try:
        profile = payload.farmer_profile if payload.role.value == "farmer" else payload.buyer_profile
        return AuthResponse(**service.register(payload.email, payload.password, payload.role, profile.model_dump() if profile else None))
    except AuthServiceError:
        raise _auth_failure()


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    client_ip = request.client.host if request.client else "unknown"
    try:
        return AuthResponse(**service.login(payload.email, payload.password, client_ip))
    except AuthServiceError:
        raise _auth_failure()


@router.get("/me", response_model=UserResponse)
async def current_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_failure()
    try:
        await service.logout(credentials.credentials)
        return MessageResponse(message="Logged out successfully")
    except AuthServiceError:
        raise _auth_failure()


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        service.forgot_password(payload.email)
    except AuthServiceError:
        logger.warning("Forgot password operation failed")
    return MessageResponse(message="If the account exists, password reset instructions have been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_failure()
    try:
        await service.reset_password(credentials.credentials, payload.new_password)
        return MessageResponse(message="Password updated successfully")
    except AuthServiceError:
        raise _auth_failure()


profile_bearer_scheme = HTTPBearer(auto_error=False)


@router.get("/profiles/me", response_model=ProfileResponse)
async def my_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(profile_bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    if credentials is None:
        raise _auth_failure()
    try:
        return service.get_my_profile(credentials.credentials, current_user.id)
    except ProfileServiceError:
        raise HTTPException(status_code=500, detail="Profile service unavailable")


@router.patch("/profiles/me", response_model=ProfileResponse)
async def update_my_profile(
    payload: FarmerProfileUpdate | BuyerProfileUpdate,
    credentials: HTTPAuthorizationCredentials | None = Depends(profile_bearer_scheme),
    current_user: UserResponse = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    if credentials is None:
        raise _auth_failure()
    try:
        return service.update_my_profile(
            credentials.credentials,
            current_user.id,
            current_user.role,
            payload.model_dump(exclude_none=True),
        )
    except ProfileServiceError:
        raise HTTPException(status_code=403, detail="Profile update not permitted")


@router.get(
    "/profiles",
    response_model=ProfileListResponse,
    dependencies=[Depends(require_roles(Role.admin))],
)
async def list_profiles(
    credentials: HTTPAuthorizationCredentials | None = Depends(profile_bearer_scheme),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileListResponse:
    if credentials is None:
        raise _auth_failure()
    try:
        return ProfileListResponse(profiles=service.list_profiles(credentials.credentials))
    except ProfileServiceError:
        raise HTTPException(status_code=500, detail="Profile service unavailable")