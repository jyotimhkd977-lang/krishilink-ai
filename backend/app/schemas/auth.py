"""Authentication request and response schemas."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.profiles import BuyerProfileCreate, FarmerProfileCreate


class Role(str, Enum):
    farmer = "farmer"
    buyer = "buyer"
    fpo = "fpo"
    logistics = "logistics"
    admin = "admin"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.farmer
    farmer_profile: FarmerProfileCreate | None = None
    buyer_profile: BuyerProfileCreate | None = None

    @model_validator(mode="after")
    def validate_role_profile(self) -> "RegisterRequest":
        if self.role == Role.farmer and self.buyer_profile is not None:
            raise ValueError("Farmer registrations cannot include a buyer profile")
        if self.role == Role.buyer and self.farmer_profile is not None:
            raise ValueError("Buyer registrations cannot include a farmer profile")
        if self.role not in {Role.farmer, Role.buyer} and (self.farmer_profile or self.buyer_profile):
            raise ValueError("This role does not support a role-specific profile")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr | None = None
    role: Role


class AuthResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    user: UserResponse | None = None


class MessageResponse(BaseModel):
    message: str