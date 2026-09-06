"""JWT validation and role authorization dependencies."""

from functools import lru_cache
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.schemas.auth import Role, UserResponse

bearer_scheme = HTTPBearer(auto_error=False)
GENERIC_AUTH_ERROR = "Authentication failed"


class TokenValidator:
    def __init__(self) -> None:
        settings = get_settings()
        self.issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else ""
        self.audience = settings.supabase_jwt_audience
        self.jwt_secret = settings.supabase_jwt_secret
        self.jwks_url = settings.supabase_jwks_url or (
            f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            if settings.supabase_url
            else ""
        )
        self.jwks_client = jwt.PyJWKClient(self.jwks_url) if self.jwks_url else None

    def decode(self, token: str) -> dict[str, Any]:
        try:
            unverified_header = jwt.get_unverified_header(token)
            algorithm = unverified_header.get("alg")

            if algorithm == "HS256" and self.jwt_secret:
                key = self.jwt_secret
            elif self.jwks_client:
                key = self.jwks_client.get_signing_key_from_jwt(token).key
            else:
                raise InvalidTokenError("JWT validation is not configured")

            options = {"verify_exp": True, "verify_aud": bool(self.audience)}
            claims = jwt.decode(
                token,
                key,
                algorithms=[algorithm] if algorithm in {"HS256", "RS256", "ES256"} else [],
                audience=self.audience or None,
                issuer=self.issuer or None,
                options=options,
            )
            if not claims.get("sub"):
                raise InvalidTokenError("JWT subject is missing")
            return claims
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)


@lru_cache
def get_token_validator() -> TokenValidator:
    return TokenValidator()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    claims = get_token_validator().decode(credentials.credentials)
    app_metadata = claims.get("app_metadata") or {}
    role_value = app_metadata.get("role")

    try:
        role = Role(role_value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    return UserResponse(
        id=claims["sub"],
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