from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import DealStatus
from app.common.pagination import PageMeta


class DealCreate(BaseModel):
    client_id: int
    manager_id: int | None = None
    title: str = Field(min_length=2, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    status: DealStatus = DealStatus.NEW


class DealUpdate(BaseModel):
    client_id: int | None = None
    manager_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    status: DealStatus | None = None


class DealRead(BaseModel):
    id: int
    client_id: int
    manager_id: int
    title: str
    amount: Decimal
    status: DealStatus
    created_at: datetime
    closed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DealListResponse(BaseModel):
    items: list[DealRead]
    meta: PageMeta


class DealSummaryStats(BaseModel):
    total_deals: int
    total_amount: Decimal
    won_deals: int
    won_amount: Decimal
    lost_deals: int
    lost_amount: Decimal
    open_deals: int
    open_amount: Decimal


class DealConversionItem(BaseModel):
    status: DealStatus
    count: int
    percentage: float


class DealConversionResponse(BaseModel):
    items: list[DealConversionItem]


class TopManagerItem(BaseModel):
    manager_id: int
    manager_name: str
    manager_email: str
    deals_count: int
    total_amount: Decimal


class TopManagersResponse(BaseModel):
    items: list[TopManagerItem]