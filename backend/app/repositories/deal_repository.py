from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, Select, bindparam, case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import DealStatus
from app.models.deal import Deal


class DealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, deal_id: int) -> Deal | None:
        stmt = select(Deal).where(Deal.id == deal_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: DealStatus | None,
        client_id: int | None,
        manager_id: int | None,
        visible_manager_id: int | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Deal], int]:
        base_stmt = self._apply_filters(
            select(Deal),
            status=status,
            client_id=client_id,
            manager_id=manager_id,
            visible_manager_id=visible_manager_id,
        )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        list_stmt = (
            base_stmt
            .order_by(Deal.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        deals_result = await self.session.execute(list_stmt)
        deals = list(deals_result.scalars().all())

        return deals, total

    async def create(self, deal: Deal) -> Deal:
        self.session.add(deal)
        await self.session.flush()
        await self.session.refresh(deal)
        return deal

    async def delete(self, deal: Deal) -> None:
        await self.session.delete(deal)
        await self.session.flush()

    async def get_summary_stats(self) -> dict:
        """
        Raw SQL #1.
        Общая статистика по сделкам.
        """
        query = text(
            """
            SELECT
                COUNT(*) AS total_deals,
                COALESCE(SUM(amount), 0) AS total_amount,

                COUNT(*) FILTER (WHERE status = 'won') AS won_deals,
                COALESCE(SUM(amount) FILTER (WHERE status = 'won'), 0) AS won_amount,

                COUNT(*) FILTER (WHERE status = 'lost') AS lost_deals,
                COALESCE(SUM(amount) FILTER (WHERE status = 'lost'), 0) AS lost_amount,

                COUNT(*) FILTER (WHERE status IN ('new', 'in_progress')) AS open_deals,
                COALESCE(
                    SUM(amount) FILTER (WHERE status IN ('new', 'in_progress')),
                    0
                ) AS open_amount
            FROM deals
            """
        )

        result = await self.session.execute(query)
        row = result.mappings().one()

        return dict(row)

    async def get_conversion_stats(self) -> list[dict]:
        """
        ORM GROUP BY.
        Конверсия по статусам.
        """
        total_subquery = select(func.count(Deal.id)).scalar_subquery()

        stmt = (
            select(
                Deal.status.label("status"),
                func.count(Deal.id).label("count"),
                case(
                    (total_subquery == 0, 0),
                    else_=func.round(
                        (func.count(Deal.id) * 100.0) / total_subquery,
                        2,
                    ),
                ).label("percentage"),
            )
            .group_by(Deal.status)
            .order_by(Deal.status)
        )

        result = await self.session.execute(stmt)

        return [dict(row._mapping) for row in result.all()]

    async def get_top_managers(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        limit: int,
    ) -> list[dict]:
        """
        Raw SQL #2.
        JOIN clients + deals + users.
        Топ менеджеров по сумме выигранных сделок.
        """
        query = (
            text(
                """
                SELECT
                    u.id AS manager_id,
                    u.full_name AS manager_name,
                    u.email AS manager_email,
                    COUNT(d.id) AS deals_count,
                    COALESCE(SUM(d.amount), 0) AS total_amount
                FROM deals d
                JOIN users u ON u.id = d.manager_id
                JOIN clients c ON c.id = d.client_id
                WHERE d.status = 'won'
                AND c.deleted_at IS NULL
                AND (
                        CAST(:date_from AS DATE) IS NULL
                        OR d.closed_at::date >= CAST(:date_from AS DATE)
                    )
                AND (
                        CAST(:date_to AS DATE) IS NULL
                        OR d.closed_at::date <= CAST(:date_to AS DATE)
                    )
                GROUP BY u.id, u.full_name, u.email
                ORDER BY total_amount DESC
                LIMIT :limit
                """
            )
            .bindparams(
                bindparam("date_from", type_=Date),
                bindparam("date_to", type_=Date),
                bindparam("limit", type_=Integer),
            )
        )

        result = await self.session.execute(
            query,
            {
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
            },
        )

        return [dict(row) for row in result.mappings().all()]

    def _apply_filters(
        self,
        stmt: Select[tuple[Deal]],
        *,
        status: DealStatus | None,
        client_id: int | None,
        manager_id: int | None,
        visible_manager_id: int | None,
    ) -> Select[tuple[Deal]]:
        if status:
            stmt = stmt.where(Deal.status == status)

        if client_id:
            stmt = stmt.where(Deal.client_id == client_id)

        if manager_id:
            stmt = stmt.where(Deal.manager_id == manager_id)

        if visible_manager_id:
            stmt = stmt.where(Deal.manager_id == visible_manager_id)

        return stmt