from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    role: str = Field(default="user", min_length=1, max_length=50)
    is_active: bool = True


class UserCreateInternal(BaseModel):
    email: EmailStr
    password_hash: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=150)
    role: str = Field(default="user", min_length=1, max_length=50)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_verified: bool
    created_at: datetime
    updated_at: datetime
