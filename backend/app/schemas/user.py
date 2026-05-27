from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.common.enums import UserRole


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)