from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.enums import ClientStatus
from app.common.pagination import PageMeta


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    source: str | None = Field(default=None, max_length=100)
    status: ClientStatus = ClientStatus.LEAD


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    source: str | None = Field(default=None, max_length=100)
    status: ClientStatus | None = None


class ClientRead(BaseModel):
    id: int
    name: str
    phone: str | None
    email: EmailStr | None
    source: str | None
    status: ClientStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ClientListResponse(BaseModel):
    items: list[ClientRead]
    meta: PageMeta