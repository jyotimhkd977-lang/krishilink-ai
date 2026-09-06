"""API version one router."""

from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.produce import router as produce_router
from app.api.v1.routes.marketplace import router as marketplace_router
from app.api.v1.routes.ai import router as ai_router
from app.api.v1.routes.orders import router as orders_router
from app.api.v1.routes.logistics import router as logistics_router
from app.api.v1.routes.quality import router as quality_router
from app.api.v1.routes.payments import router as payments_router
from app.api.v1.routes.trust import router as trust_router
from app.api.v1.routes.notifications import router as notifications_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(produce_router, tags=["farms", "listings"])
api_router.include_router(marketplace_router, tags=["marketplace"])
api_router.include_router(ai_router, tags=["ai"])
api_router.include_router(orders_router, tags=["orders"])
api_router.include_router(logistics_router, tags=["logistics"])
api_router.include_router(quality_router, tags=["quality", "disputes"])
api_router.include_router(payments_router, tags=["payments", "settlements"])
api_router.include_router(trust_router, tags=["reviews", "trust"])
api_router.include_router(notifications_router, tags=["notifications"])