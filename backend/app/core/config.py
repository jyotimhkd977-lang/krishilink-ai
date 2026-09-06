"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KrishiLink AI API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    force_https: bool = False
    max_request_bytes: int = 12 * 1024 * 1024
    require_email_verification: bool = True
    trusted_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "testserver"])
    rate_limit_requests: int = 300
    rate_limit_window_seconds: int = 60
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_jwt_audience: str = "authenticated"
    supabase_jwks_url: str = ""
    database_url: str = ""
    allowed_methods: list[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    allowed_headers: list[str] = Field(default_factory=lambda: ["Authorization", "Content-Type", "Accept", "Idempotency-Key"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard_cors(cls, origins: list[str]) -> list[str]:
        if "*" in origins:
            raise ValueError("Wildcard CORS is not allowed")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()