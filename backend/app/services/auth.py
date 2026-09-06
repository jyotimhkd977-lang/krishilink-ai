"""Supabase Auth integration."""

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any

import httpx
from supabase import Client, create_client

from app.core.config import get_settings
from app.schemas.auth import Role, UserResponse

logger = logging.getLogger(__name__)


class AuthServiceError(Exception):
    """Raised when an authentication provider operation cannot be completed."""


class LoginRateLimiter:
    def __init__(self, max_attempts: int = 10, window_seconds: int = 60) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            attempts = self.attempts[key]
            while attempts and now - attempts[0] >= self.window_seconds:
                attempts.popleft()
            if len(attempts) >= self.max_attempts:
                return False
            attempts.append(now)
            return True


login_rate_limiter = LoginRateLimiter()


def _value(data: Any, name: str, default: Any = None) -> Any:
    if isinstance(data, dict):
        return data.get(name, default)
    return getattr(data, name, default)


def _user_response(user: Any, role: Role) -> UserResponse | None:
    if user is None:
        return None
    return UserResponse(id=_value(user, "id"), email=_value(user, "email"), role=role)


class AuthService:
    def __init__(self, client: Client | None = None) -> None:
        self.settings = get_settings()
        self.client = client

    def _create_client(self) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise AuthServiceError("Supabase Auth is not configured")
        return create_client(self.settings.supabase_url, self.settings.supabase_anon_key)

    def _get_client(self) -> Client:
        if self.client is None:
            self.client = self._create_client()
        return self.client

    def _set_server_role(self, user_id: str, role: Role) -> None:
        try:
            if self.settings.supabase_service_role_key:
                admin_client = create_client(self.settings.supabase_url, self.settings.supabase_service_role_key)
                admin_client.auth.admin.update_user_by_id(
                    user_id,
                    {"app_metadata": {"role": role.value}},
                )
                return
        except Exception as exc:
            logger.warning("admin_client_role_update_failed", extra={"reason": type(exc).__name__})

        if self.settings.database_url:
            try:
                import json
                import psycopg
                with psycopg.connect(self.settings.database_url) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE auth.users SET raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb) || %s::jsonb WHERE id = %s",
                            [json.dumps({"role": role.value}), user_id],
                        )
                    conn.commit()
                return
            except Exception as db_exc:
                logger.warning("direct_db_role_update_failed", extra={"reason": str(db_exc)})

        if role != Role.farmer:
            raise AuthServiceError("Server role assignment is not configured")

    def register(
        self,
        email: str,
        password: str,
        role: Role,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if role.value in {"admin", "logistics"}:
            raise AuthServiceError("Privileged roles require administrator provisioning")
        try:
            response = self._get_client().auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"role": role.value, "profile": profile or {}}},
                }
            )
            session = _value(response, "session")
            user = _value(response, "user")
            user_id = _value(user, "id") if user else None
            if user_id:
                self._set_server_role(user_id, role)
                if not self.settings.require_email_verification and self.settings.database_url:
                    try:
                        import psycopg
                        with psycopg.connect(self.settings.database_url) as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "UPDATE auth.users SET email_confirmed_at = timezone('utc', now()), confirmed_at = timezone('utc', now()) WHERE id = %s",
                                    [user_id],
                                )
                            conn.commit()
                    except Exception as db_err:
                        logger.warning("auto_confirm_email_failed", extra={"reason": str(db_err)})

            if session is None and not self.settings.require_email_verification:
                try:
                    login_res = self._get_client().auth.sign_in_with_password({"email": email, "password": password})
                    session = _value(login_res, "session")
                    user = _value(login_res, "user") or user
                except Exception:
                    pass

            return {
                "access_token": _value(session, "access_token"),
                "expires_in": _value(session, "expires_in"),
                "user": _user_response(user, role),
            }
        except Exception as exc:
            logger.warning("Registration failed", extra={"reason": type(exc).__name__})
            raise AuthServiceError from exc

    def login(self, email: str, password: str, client_ip: str) -> dict[str, Any]:
        email_key = email.casefold()
        if not login_rate_limiter.allow(client_ip) or not login_rate_limiter.allow(email_key):
            logger.warning("authentication_rate_limited", extra={"client_ip": client_ip})
            raise AuthServiceError

        try:
            response = self._get_client().auth.sign_in_with_password({"email": email, "password": password})
            session = _value(response, "session")
            user = _value(response, "user")
            if self.settings.require_email_verification and not (_value(user, "email_confirmed_at") or _value(user, "confirmed_at")):
                raise AuthServiceError
            metadata = _value(user, "app_metadata", {}) or {}
            role = Role(metadata.get("role", Role.farmer.value))
            return {
                "access_token": _value(session, "access_token"),
                "expires_in": _value(session, "expires_in"),
                "user": _user_response(user, role),
            }
        except Exception as exc:
            logger.warning("authentication_failed", extra={"client_ip": client_ip, "reason": type(exc).__name__})
            raise AuthServiceError from exc

    async def logout(self, access_token: str) -> None:
        await self._auth_request("/logout", access_token, method="POST")

    def forgot_password(self, email: str) -> None:
        try:
            self._get_client().auth.reset_password_email(email)
        except Exception as exc:
            logger.warning("Password reset request failed", extra={"reason": type(exc).__name__})
            raise AuthServiceError from exc

    async def reset_password(self, access_token: str, new_password: str) -> None:
        await self._auth_request("/user", access_token, method="PUT", json={"password": new_password})

    async def _auth_request(
        self,
        path: str,
        access_token: str,
        method: str,
        json: dict[str, Any] | None = None,
    ) -> None:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise AuthServiceError

        headers = {
            "apikey": self.settings.supabase_anon_key,
            "Authorization": f"Bearer {access_token}",
        }
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.request(
                    method,
                    f"{self.settings.supabase_url.rstrip('/')}/auth/v1{path}",
                    headers=headers,
                    json=json,
                )
            if response.status_code >= 400:
                raise AuthServiceError
        except (httpx.HTTPError, AuthServiceError) as exc:
            logger.warning("Supabase Auth request failed", extra={"operation": path})
            raise AuthServiceError from exc

    def send_phone_otp(self, phone: str) -> None:
        try:
            self._get_client().auth.sign_in_with_otp({
                "phone": phone,
                "options": {"data": {"role": Role.farmer.value}},
            })
        except Exception as exc:
            logger.warning("phone_otp_send_failed", extra={"reason": type(exc).__name__})
            raise AuthServiceError from exc

    def verify_phone_otp(self, phone: str, token: str) -> dict[str, Any]:
        try:
            response = self._get_client().auth.verify_otp({"phone": phone, "token": token, "type": "sms"})
            session = _value(response, "session")
            user = _value(response, "user")
            if user is None or session is None:
                raise AuthServiceError
            self._set_server_role(_value(user, "id"), Role.farmer)
            return {
                "access_token": _value(session, "access_token"),
                "expires_in": _value(session, "expires_in"),
                "user": _user_response(user, Role.farmer),
            }
        except Exception as exc:
            logger.warning("phone_otp_verification_failed", extra={"reason": type(exc).__name__})
            raise AuthServiceError from exc