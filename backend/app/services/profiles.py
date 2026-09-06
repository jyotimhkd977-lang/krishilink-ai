"""Profile persistence through local SQLite database."""

from typing import Any

from app.db.session import SessionLocal
from app.models.entities import BuyerProfile, FarmerProfile, User
from app.schemas.auth import Role
from app.schemas.profiles import BuyerProfileResponse, FarmerProfileResponse, ProfileResponse


class ProfileServiceError(Exception):
    """Raised when a profile operation cannot be completed."""


class ProfileService:
    def get_my_profile(self, access_token: str, user_id: str) -> ProfileResponse:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ProfileServiceError("User not found")
            return self._to_profile(user)
        except ProfileServiceError:
            raise
        except Exception as exc:
            raise ProfileServiceError from exc
        finally:
            db.close()

    def update_my_profile(
        self,
        access_token: str,
        user_id: str,
        role: Role,
        values: dict[str, Any],
    ) -> ProfileResponse:
        if role not in {Role.farmer, Role.buyer}:
            raise ProfileServiceError("Invalid role for profile update")

        db = SessionLocal()
        try:
            if role == Role.farmer:
                prof = db.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
                if not prof:
                    prof = FarmerProfile(user_id=user_id)
                    db.add(prof)
                for k, v in values.items():
                    if hasattr(prof, k):
                        if k == "primary_crops" and isinstance(v, list):
                            setattr(prof, k, ",".join(v))
                        else:
                            setattr(prof, k, v)
            else:
                prof = db.query(BuyerProfile).filter(BuyerProfile.user_id == user_id).first()
                if not prof:
                    prof = BuyerProfile(user_id=user_id)
                    db.add(prof)
                for k, v in values.items():
                    if hasattr(prof, k):
                        setattr(prof, k, v)

            db.commit()
            user = db.query(User).filter(User.id == user_id).first()
            return self._to_profile(user)
        except Exception as exc:
            db.rollback()
            raise ProfileServiceError from exc
        finally:
            db.close()

    def list_profiles(self, access_token: str) -> list[ProfileResponse]:
        db = SessionLocal()
        try:
            users = db.query(User).all()
            return [self._to_profile(u) for u in users]
        except Exception as exc:
            raise ProfileServiceError from exc
        finally:
            db.close()

    @staticmethod
    def _to_profile(user: User) -> ProfileResponse:
        farmer_p = None
        if user.farmer_profile:
            fp = user.farmer_profile
            crops = [c.strip() for c in (fp.primary_crops or "").split(",") if c.strip()]
            farmer_p = FarmerProfileResponse(
                user_id=fp.user_id,
                full_name=fp.full_name,
                phone=fp.phone,
                village=fp.village,
                district=fp.district,
                state=fp.state,
                block_tehsil=fp.block_tehsil,
                farm_name=fp.farm_name,
                farm_size=fp.farm_size,
                farm_unit=fp.farm_unit,
                primary_crops=crops,
                preferred_language=fp.preferred_language,
                trust_score=fp.trust_score,
                verified=fp.verified,
                created_at=fp.created_at,
                updated_at=fp.updated_at,
            )

        buyer_p = None
        if user.buyer_profile:
            bp = user.buyer_profile
            buyer_p = BuyerProfileResponse(
                user_id=bp.user_id,
                business_name=bp.business_name,
                full_name=bp.business_name,
                phone=bp.phone,
                buyer_type=bp.buyer_type,
                location=bp.location,
                district=bp.location,
                state="Odisha",
                trust_score=bp.trust_score,
                verified=bp.verified,
                created_at=bp.created_at,
                updated_at=bp.updated_at,
            )

        return ProfileResponse(
            user_id=user.id,
            email=user.email or f"{user.role}_{user.id[:6]}@krishilink.ai",
            role=user.role,
            farmer_profile=farmer_p,
            buyer_profile=buyer_p,
        )