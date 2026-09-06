"""Profile persistence through Supabase PostgREST and admin client."""

from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings
from app.schemas.auth import Role
from app.schemas.profiles import ProfileResponse


class ProfileServiceError(Exception):
    """Raised when a profile operation cannot be completed."""


def _first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


class ProfileService:
    def __init__(self, client: Client | None = None) -> None:
        self.settings = get_settings()
        self.client = client

    def _client_for_token(self, access_token: str) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise ProfileServiceError
        client = create_client(self.settings.supabase_url, self.settings.supabase_anon_key)
        client.postgrest.auth(access_token)
        return client

    def _admin_client(self) -> Client:
        if not self.settings.supabase_url or not self.settings.supabase_service_role_key:
            raise ProfileServiceError
        return create_client(self.settings.supabase_url, self.settings.supabase_service_role_key)

    def get_my_profile(self, access_token: str, user_id: str) -> ProfileResponse:
        try:
            response = (
                self._client_for_token(access_token)
                .table("users")
                .select("id,email,role,farmer_profiles(*),buyer_profiles(*)")
                .eq("id", user_id)
                .single()
                .execute()
            )
            return self._to_profile(response.data)
        except Exception as exc:
            raise ProfileServiceError from exc

    def update_my_profile(
        self,
        access_token: str,
        user_id: str,
        role: Role,
        values: dict[str, Any],
    ) -> ProfileResponse:
        if role not in {Role.farmer, Role.buyer}:
            raise ProfileServiceError
        table = "farmer_profiles" if role == Role.farmer else "buyer_profiles"
        try:
            self._client_for_token(access_token).table(table).update(values).eq("user_id", user_id).execute()
            return self.get_my_profile(access_token, user_id)
        except Exception as exc:
            raise ProfileServiceError from exc

    def list_profiles(self, access_token: str) -> list[ProfileResponse]:
        try:
            response = (
                self._client_for_token(access_token)
                .table("users")
                .select("id,email,role,farmer_profiles(*),buyer_profiles(*)")
                .execute()
            )
            return [self._to_profile(row) for row in response.data or []]
        except Exception as exc:
            raise ProfileServiceError from exc

    @staticmethod
    def _to_profile(data: dict[str, Any]) -> ProfileResponse:
        return ProfileResponse(
            user_id=data["id"],
            email=data["email"],
            role=data["role"],
            farmer_profile=_first(data.get("farmer_profiles")),
            buyer_profile=_first(data.get("buyer_profiles")),
        )