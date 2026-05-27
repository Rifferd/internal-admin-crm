from datetime import UTC, datetime
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dashboard import DashboardStatsResponse


class DashboardService:
    CACHE_KEY = "dashboard:stats"
    CACHE_TTL_SECONDS = 60

    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis

    async def get_stats(self) -> DashboardStatsResponse:
        cached_stats = await self.redis.get(self.CACHE_KEY)

        if cached_stats is not None:
            return DashboardStatsResponse.model_validate_json(cached_stats)

        stats = await self._load_stats_from_db()

        await self.redis.setex(
            self.CACHE_KEY,
            self.CACHE_TTL_SECONDS,
            stats.model_dump_json(),
        )

        return stats

    async def _load_stats_from_db(self) -> DashboardStatsResponse:
        query = text(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM clients
                    WHERE deleted_at IS NULL
                ) AS clients_total,

                (
                    SELECT COUNT(*)
                    FROM clients
                    WHERE deleted_at IS NULL
                      AND status = 'active'
                ) AS clients_active,

                (
                    SELECT COUNT(*)
                    FROM deals
                ) AS deals_total,

                (
                    SELECT COUNT(*)
                    FROM deals
                    WHERE status = 'won'
                ) AS deals_won,

                (
                    SELECT COUNT(*)
                    FROM deals
                    WHERE status = 'lost'
                ) AS deals_lost,

                (
                    SELECT COUNT(*)
                    FROM deals
                    WHERE status IN ('new', 'in_progress')
                ) AS deals_open,

                (
                    SELECT COALESCE(SUM(amount), 0)
                    FROM deals
                ) AS deals_total_amount,

                (
                    SELECT COALESCE(SUM(amount), 0)
                    FROM deals
                    WHERE status = 'won'
                ) AS deals_won_amount,

                (
                    SELECT COUNT(*)
                    FROM tasks
                ) AS tasks_total,

                (
                    SELECT COUNT(*)
                    FROM tasks
                    WHERE deadline < :now
                      AND status NOT IN ('done', 'cancelled')
                ) AS tasks_overdue
            """
        )

        result = await self.session.execute(
            query,
            {"now": datetime.now(UTC)},
        )

        row = result.mappings().one()

        return DashboardStatsResponse(
            clients_total=row["clients_total"],
            clients_active=row["clients_active"],
            deals_total=row["deals_total"],
            deals_won=row["deals_won"],
            deals_lost=row["deals_lost"],
            deals_open=row["deals_open"],
            deals_total_amount=Decimal(row["deals_total_amount"]),
            deals_won_amount=Decimal(row["deals_won_amount"]),
            tasks_total=row["tasks_total"],
            tasks_overdue=row["tasks_overdue"],
        )