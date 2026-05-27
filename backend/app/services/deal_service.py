from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import DealStatus, UserRole
from app.common.pagination import build_page_meta
from app.models.deal import Deal
from app.models.user import User
from app.repositories.client_repository import ClientRepository
from app.repositories.deal_repository import DealRepository
from app.repositories.user_repository import UserRepository
from app.schemas.deal import (
    DealConversionItem,
    DealConversionResponse,
    DealCreate,
    DealListResponse,
    DealRead,
    DealSummaryStats,
    DealUpdate,
    TopManagerItem,
    TopManagersResponse,
)


class DealService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.deal_repository = DealRepository(session)
        self.client_repository = ClientRepository(session)
        self.user_repository = UserRepository(session)

    async def list_deals(
        self,
        *,
        current_user: User,
        deal_status: DealStatus | None,
        client_id: int | None,
        manager_id: int | None,
        page: int,
        size: int,
    ) -> DealListResponse:
        offset = (page - 1) * size

        visible_manager_id = None

        if current_user.role == UserRole.MANAGER:
            visible_manager_id = current_user.id

        deals, total = await self.deal_repository.list(
            status=deal_status,
            client_id=client_id,
            manager_id=manager_id,
            visible_manager_id=visible_manager_id,
            offset=offset,
            limit=size,
        )

        return DealListResponse(
            items=[DealRead.model_validate(deal) for deal in deals],
            meta=build_page_meta(page=page, size=size, total=total),
        )

    async def get_deal(self, deal_id: int, current_user: User) -> Deal:
        deal = await self.deal_repository.get_by_id(deal_id)

        if deal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found",
            )

        self._check_can_view_deal(deal, current_user)

        return deal

    async def create_deal(self, data: DealCreate, current_user: User) -> Deal:
        await self._ensure_client_exists(data.client_id)

        manager_id = await self._resolve_manager_id_for_create(data, current_user)

        deal = Deal(
            client_id=data.client_id,
            manager_id=manager_id,
            title=data.title,
            amount=data.amount,
            status=data.status,
        )

        self._apply_closed_at_rule(deal, data.status)

        deal = await self.deal_repository.create(deal)

        await self.session.commit()
        await self.session.refresh(deal)

        return deal

    async def update_deal(
        self,
        deal_id: int,
        data: DealUpdate,
        current_user: User,
    ) -> Deal:
        deal = await self.get_deal(deal_id, current_user)

        if current_user.role == UserRole.MANAGER and data.manager_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager cannot reassign deals",
            )

        update_data = data.model_dump(exclude_unset=True)

        if "client_id" in update_data:
            await self._ensure_client_exists(update_data["client_id"])

        if "manager_id" in update_data:
            await self._ensure_manager_exists(update_data["manager_id"])

        for field, value in update_data.items():
            setattr(deal, field, value)

        if data.status is not None:
            self._apply_closed_at_rule(deal, data.status)

        await self.session.commit()
        await self.session.refresh(deal)

        return deal

    async def delete_deal(self, deal_id: int, current_user: User) -> None:
        deal = await self.get_deal(deal_id, current_user)

        await self.deal_repository.delete(deal)
        await self.session.commit()

    async def get_summary_stats(self) -> DealSummaryStats:
        data = await self.deal_repository.get_summary_stats()

        return DealSummaryStats(
            total_deals=data["total_deals"],
            total_amount=Decimal(data["total_amount"]),
            won_deals=data["won_deals"],
            won_amount=Decimal(data["won_amount"]),
            lost_deals=data["lost_deals"],
            lost_amount=Decimal(data["lost_amount"]),
            open_deals=data["open_deals"],
            open_amount=Decimal(data["open_amount"]),
        )

    async def get_conversion_stats(self) -> DealConversionResponse:
        rows = await self.deal_repository.get_conversion_stats()

        return DealConversionResponse(
            items=[
                DealConversionItem(
                    status=row["status"],
                    count=row["count"],
                    percentage=float(row["percentage"]),
                )
                for row in rows
            ]
        )

    async def get_top_managers(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        limit: int,
    ) -> TopManagersResponse:
        rows = await self.deal_repository.get_top_managers(
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        return TopManagersResponse(
            items=[
                TopManagerItem(
                    manager_id=row["manager_id"],
                    manager_name=row["manager_name"],
                    manager_email=row["manager_email"],
                    deals_count=row["deals_count"],
                    total_amount=Decimal(row["total_amount"]),
                )
                for row in rows
            ]
        )

    async def _ensure_client_exists(self, client_id: int) -> None:
        client = await self.client_repository.get_by_id(client_id)

        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

    async def _ensure_manager_exists(self, manager_id: int) -> None:
        manager = await self.user_repository.get_by_id(manager_id)

        if manager is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found",
            )

        if not manager.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manager is inactive",
            )

        if manager.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User cannot be assigned as manager",
            )

    async def _resolve_manager_id_for_create(
        self,
        data: DealCreate,
        current_user: User,
    ) -> int:
        if current_user.role == UserRole.ADMIN:
            manager_id = data.manager_id or current_user.id
            await self._ensure_manager_exists(manager_id)
            return manager_id

        if current_user.role == UserRole.MANAGER:
            if data.manager_id is not None and data.manager_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Manager can create deals only for himself",
                )

            return current_user.id

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    def _check_can_view_deal(self, deal: Deal, current_user: User) -> None:
        if current_user.role == UserRole.ADMIN:
            return

        if current_user.role == UserRole.VIEWER:
            return

        if current_user.role == UserRole.MANAGER and deal.manager_id == current_user.id:
            return

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    def _apply_closed_at_rule(self, deal: Deal, deal_status: DealStatus) -> None:
        if deal_status in (DealStatus.WON, DealStatus.LOST):
            deal.closed_at = datetime.now(UTC)
            return

        if deal_status in (DealStatus.NEW, DealStatus.IN_PROGRESS):
            deal.closed_at = None