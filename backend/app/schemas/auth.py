from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(max_length=128)
    password_confirmation: str = Field(max_length=128)
    accept_terms: bool



class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class CurrentSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    authentication_level: str
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    device_id: UUID | None


class AuthResponse(BaseModel):
    success: bool = True
    message: str
    user: AuthenticatedUser
    session: CurrentSession | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(max_length=128)
    new_password_confirmation: str = Field(max_length=128)
    logout_other_sessions: bool = True



class LogoutResponse(BaseModel):
    success: bool = True
    message: str
    revoked_sessions: int | None = None


class SessionSummary(BaseModel):
    id: UUID
    device_name: str | None
    browser: str | None
    operating_system: str | None
    device_type: str | None
    ip_address: str | None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_current: bool


class SessionsResponse(BaseModel):
    success: bool = True
    sessions: list[SessionSummary]


class CsrfResponse(BaseModel):
    success: bool = True
    csrf_token: str
