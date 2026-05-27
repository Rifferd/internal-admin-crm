from datetime import UTC, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ClientStatus
from app.models.client import Client


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, client_id: int) -> Client | None:
        stmt = (
            select(Client)
            .where(Client.id == client_id)
            .where(Client.deleted_at.is_(None))
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        search: str | None,
        status: ClientStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Client], int]:
        base_stmt = self._apply_filters(
            select(Client).where(Client.deleted_at.is_(None)),
            search=search,
            status=status,
        )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        list_stmt = (
            base_stmt
            .order_by(Client.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        clients_result = await self.session.execute(list_stmt)
        clients = list(clients_result.scalars().all())

        return clients, total

    async def create(self, client: Client) -> Client:
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def soft_delete(self, client: Client) -> None:
        client.deleted_at = datetime.now(UTC)
        await self.session.flush()

    def _apply_filters(
        self,
        stmt: Select[tuple[Client]],
        *,
        search: str | None,
        status: ClientStatus | None,
    ) -> Select[tuple[Client]]:
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Client.name.ilike(pattern),
                    Client.phone.ilike(pattern),
                    Client.email.ilike(pattern),
                )
            )

        if status:
            stmt = stmt.where(Client.status == status)

        return stmt