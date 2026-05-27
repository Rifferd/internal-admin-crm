from fastapi import APIRouter, Depends, Query, Response, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.common.enums import ClientStatus, UserRole
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientRead,
    ClientUpdate,
)
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=ClientListResponse)
async def list_clients(
    search: str | None = Query(default=None),
    status: ClientStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> ClientListResponse:
    service = ClientService(session)

    return await service.list_clients(
        search=search,
        client_status=status,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=ClientRead,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_client(
    data: ClientCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> ClientRead:
    service = ClientService(session)
    client = await service.create_client(data)

    return ClientRead.model_validate(client)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> ClientRead:
    service = ClientService(session)
    client = await service.get_client(client_id)

    return ClientRead.model_validate(client)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> ClientRead:
    service = ClientService(session)
    client = await service.update_client(client_id, data)

    return ClientRead.model_validate(client)


@router.delete(
    "/{client_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_client(
    client_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    service = ClientService(session)
    await service.delete_client(client_id)

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)