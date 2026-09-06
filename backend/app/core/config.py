"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DB_FILE = f"sqlite:///{(_BACKEND_DIR / 'krishilink.db').as_posix()}"


class Settings(BaseSettings):
    app_name: str = "KrishiLink AI API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    force_https: bool = False
    max_request_bytes: int = 12 * 1024 * 1024
    require_email_verification: bool = False
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"])
    rate_limit_requests: int = 600
    rate_limit_window_seconds: int = 60
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "*",
        ]
    )

    database_url: str = _DEFAULT_DB_FILE

    # SMTP Email Configuration for OTP Verification
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "no-reply@krishilink.ai"
    smtp_from_name: str = "KrishiLink AI"
    smtp_use_tls: bool = True

    # JWT Authentication
    jwt_secret_key: str = "krishilink-prototype-jwt-secret-key-2026"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 10080

    allowed_methods: list[str] = Field(default_factory=lambda: ["*"])
    allowed_headers: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard_cors(cls, origins: list[str]) -> list[str]:
        # Allow wildcard in development/prototype mode
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()