from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import TaskStatus
from app.common.pagination import PageMeta


class TaskCreate(BaseModel):
    deal_id: int
    assigned_to: int | None = None
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    deadline: datetime
    status: TaskStatus = TaskStatus.TODO


class TaskUpdate(BaseModel):
    deal_id: int | None = None
    assigned_to: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    deadline: datetime | None = None
    status: TaskStatus | None = None


class TaskRead(BaseModel):
    id: int
    deal_id: int
    assigned_to: int
    title: str
    description: str | None
    deadline: datetime
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: list[TaskRead]
    meta: PageMeta