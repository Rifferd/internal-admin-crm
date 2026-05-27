from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ClientStatus
from app.common.pagination import build_page_meta
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientRead,
    ClientUpdate,
)


class ClientService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.client_repository = ClientRepository(session)

    async def list_clients(
        self,
        *,
        search: str | None,
        client_status: ClientStatus | None,
        page: int,
        size: int,
    ) -> ClientListResponse:
        offset = (page - 1) * size

        clients, total = await self.client_repository.list(
            search=search,
            status=client_status,
            offset=offset,
            limit=size,
        )

        return ClientListResponse(
            items=[ClientRead.model_validate(client) for client in clients],
            meta=build_page_meta(page=page, size=size, total=total),
        )

    async def get_client(self, client_id: int) -> Client:
        client = await self.client_repository.get_by_id(client_id)

        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        return client

    async def create_client(self, data: ClientCreate) -> Client:
        client = Client(
            name=data.name,
            phone=data.phone,
            email=str(data.email) if data.email else None,
            source=data.source,
            status=data.status,
        )

        client = await self.client_repository.create(client)

        await self.session.commit()
        await self.session.refresh(client)

        return client

    async def update_client(self, client_id: int, data: ClientUpdate) -> Client:
        client = await self.get_client(client_id)

        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] is not None:
            update_data["email"] = str(update_data["email"])

        for field, value in update_data.items():
            setattr(client, field, value)

        await self.session.commit()
        await self.session.refresh(client)

        return client

    async def delete_client(self, client_id: int) -> None:
        client = await self.get_client(client_id)

        await self.client_repository.soft_delete(client)
        await self.session.commit()