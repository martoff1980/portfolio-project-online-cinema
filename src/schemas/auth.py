import re
from datetime import datetime, date
from typing import Optional
from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    Field,
    field_validator
)
from src.models.auth import GenderEnum


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        description="The password must be at least 8 characters long."
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        """
        Password complexity check:
        1. Minimum length of 8 characters
            (min_length is also handled,
            but we duplicate this for reliability)
        2. At least one uppercase letter (A-Z)
        3. At least one lowercase letter (a-z)
        4. At least one digit (0-9)
        """
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )
        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")

        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        description="The password must be at least 8 characters long."
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    group_id: int
    created_at: datetime
