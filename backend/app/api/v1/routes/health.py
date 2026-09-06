"""Health check endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Check API health")
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="krishilink-ai-api",
        timestamp=datetime.now(timezone.utc),
    )