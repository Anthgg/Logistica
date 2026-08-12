from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientCreate(BaseModel):
    document_type: str = Field(min_length=1, max_length=20)
    document_number: str = Field(min_length=4, max_length=30)
    business_name: str = Field(min_length=2, max_length=200)
    contact_name: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str = Field(min_length=3, max_length=255)
    district: str = Field(min_length=2, max_length=100)
    province: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)


class ClientUpdate(BaseModel):
    document_type: str | None = Field(default=None, min_length=1, max_length=20)
    document_number: str | None = Field(default=None, min_length=4, max_length=30)
    business_name: str | None = Field(default=None, min_length=2, max_length=200)
    contact_name: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    province: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=2, max_length=100)
    is_active: bool | None = None


class ClientRead(ClientCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
