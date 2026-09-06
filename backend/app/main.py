"""FastAPI application entry point for KrishiLink AI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.security import IPRateLimitMiddleware, RequestSizeLimitMiddleware, SecurityHeadersMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Secure backend foundation for the KrishiLink AI platform.",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
if settings.force_https:
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(IPRateLimitMiddleware, requests=settings.rate_limit_requests, window_seconds=settings.rate_limit_window_seconds)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")


from app.db.init_db import init_db


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("KrishiLink AI API started", extra={"environment": settings.environment})
    try:
        init_db()
        logger.info("SQLite database initialized and seeded successfully")
    except Exception as exc:
        logger.error(f"Failed to initialize SQLite database: {exc}")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("KrishiLink AI API stopped")