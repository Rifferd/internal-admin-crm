from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.common.enums import DealStatus, UserRole
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.deal import (
    DealConversionResponse,
    DealCreate,
    DealListResponse,
    DealRead,
    DealSummaryStats,
    DealUpdate,
    TopManagersResponse,
)
from app.services.deal_service import DealService

router = APIRouter(prefix="/deals", tags=["Deals"])


@router.get("/stats/summary", response_model=DealSummaryStats)
async def get_deals_summary_stats(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.VIEWER)),
) -> DealSummaryStats:
    service = DealService(session)
    return await service.get_summary_stats()


@router.get("/stats/conversion", response_model=DealConversionResponse)
async def get_deals_conversion_stats(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.VIEWER)),
) -> DealConversionResponse:
    service = DealService(session)
    return await service.get_conversion_stats()


@router.get("/stats/top-managers", response_model=TopManagersResponse)
async def get_top_managers_stats(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.VIEWER)),
) -> TopManagersResponse:
    service = DealService(session)

    return await service.get_top_managers(
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get("", response_model=DealListResponse)
async def list_deals(
    status: DealStatus | None = Query(default=None),
    client_id: int | None = Query(default=None),
    manager_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> DealListResponse:
    service = DealService(session)

    return await service.list_deals(
        current_user=current_user,
        deal_status=status,
        client_id=client_id,
        manager_id=manager_id,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=DealRead,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_deal(
    data: DealCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> DealRead:
    service = DealService(session)
    deal = await service.create_deal(data, current_user)

    return DealRead.model_validate(deal)


@router.get("/{deal_id}", response_model=DealRead)
async def get_deal(
    deal_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> DealRead:
    service = DealService(session)
    deal = await service.get_deal(deal_id, current_user)

    return DealRead.model_validate(deal)


@router.patch("/{deal_id}", response_model=DealRead)
async def update_deal(
    deal_id: int,
    data: DealUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> DealRead:
    service = DealService(session)
    deal = await service.update_deal(deal_id, data, current_user)

    return DealRead.model_validate(deal)


@router.delete(
    "/{deal_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_deal(
    deal_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    service = DealService(session)
    await service.delete_deal(deal_id, current_user)

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)