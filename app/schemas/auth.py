from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserRead


class AuthResponse(BaseModel):
    success: bool
    message: str
    data: TokenData


class UserResponse(BaseModel):
    success: bool
    message: str
    data: UserRead


class MessageResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, str] = Field(default_factory=dict)
