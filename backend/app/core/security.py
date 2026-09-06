"""JWT generation, validation, password hashing, and role authorization dependencies."""

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import hmac
import secrets
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.schemas.auth import Role, UserResponse

bearer_scheme = HTTPBearer(auto_error=False)
GENERIC_AUTH_ERROR = "Authentication failed"


def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with SHA-256 and cryptographic salt."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against salt:hash string."""
    try:
        if not hashed_password or ":" not in hashed_password:
            return False
        salt_hex, hash_hex = hashed_password.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generate a signed JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_expires_minutes)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT token."""
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
        if not claims.get("sub"):
            raise InvalidTokenError("JWT subject is missing")
        return claims
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)


class TokenValidator:
    """Token validator for checking JWT claims."""

    def decode(self, token: str) -> dict[str, Any]:
        return decode_access_token(token)


@lru_cache
def get_token_validator() -> TokenValidator:
    return TokenValidator()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    claims = get_token_validator().decode(credentials.credentials)
    role_value = claims.get("role") or (claims.get("app_metadata") or {}).get("role", Role.farmer.value)

    try:
        role = Role(role_value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    return UserResponse(
        id=str(claims["sub"]),
        email=claims.get("email"),
        role=role,
    )


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse | None:
    if credentials is None:
        return None
    return await get_current_user(credentials)


def require_roles(*allowed_roles: Role) -> Callable:
    """Return a dependency that permits only the supplied roles."""

    async def role_authorization(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_authorization