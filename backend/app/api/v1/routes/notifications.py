"""Protected notification endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.notifications import NotificationPreferences, NotificationResponse, UnreadCountResponse
from app.services.notifications import NotificationService, NotificationServiceError

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> NotificationService:
    return NotificationService()


def service_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="Notification service unavailable")


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(unread_only: bool = False, limit: int = Query(default=50, ge=1, le=100), credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: NotificationService = Depends(get_service)) -> list[NotificationResponse]:
    try:
        return [NotificationResponse(**row) for row in service.list_notifications(credentials.credentials, unread_only, limit)]
    except NotificationServiceError:
        raise service_unavailable()


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def unread_count(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: NotificationService = Depends(get_service)) -> UnreadCountResponse:
    try:
        return UnreadCountResponse(unread_count=service.unread_count(credentials.credentials))
    except NotificationServiceError:
        raise service_unavailable()


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(notification_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: NotificationService = Depends(get_service)) -> NotificationResponse:
    try:
        return NotificationResponse(**service.mark_read(credentials.credentials, notification_id))
    except NotificationServiceError:
        raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: NotificationService = Depends(get_service)) -> None:
    try:
        service.mark_all_read(credentials.credentials)
    except NotificationServiceError:
        raise service_unavailable()


@router.get("/notification-preferences", response_model=NotificationPreferences)
async def get_preferences(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: NotificationService = Depends(get_service)) -> NotificationPreferences:
    try:
        return NotificationPreferences(**service.get_preferences(credentials.credentials, current_user.id))
    except NotificationServiceError:
        raise service_unavailable()


@router.put("/notification-preferences", response_model=NotificationPreferences)
async def update_preferences(payload: NotificationPreferences, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), current_user: UserResponse = Depends(get_current_user), service: NotificationService = Depends(get_service)) -> NotificationPreferences:
    try:
        values = {key.value: value for key, value in payload.preferences.items()}
        return NotificationPreferences(**service.update_preferences(credentials.credentials, current_user.id, values))
    except NotificationServiceError:
        raise service_unavailable()