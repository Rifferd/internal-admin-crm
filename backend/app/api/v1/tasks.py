from fastapi import APIRouter, Depends, Query, Response, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.common.enums import TaskStatus, UserRole
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskRead,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: TaskStatus | None = Query(default=None),
    deal_id: int | None = Query(default=None),
    assigned_to: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> TaskListResponse:
    service = TaskService(session)

    return await service.list_tasks(
        current_user=current_user,
        task_status=status,
        deal_id=deal_id,
        assigned_to=assigned_to,
        overdue_only=False,
        page=page,
        size=size,
    )


@router.get("/my", response_model=TaskListResponse)
async def list_my_tasks(
    status: TaskStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> TaskListResponse:
    service = TaskService(session)

    return await service.list_my_tasks(
        current_user=current_user,
        task_status=status,
        page=page,
        size=size,
    )


@router.get("/overdue", response_model=TaskListResponse)
async def list_overdue_tasks(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> TaskListResponse:
    service = TaskService(session)

    return await service.list_overdue_tasks(
        current_user=current_user,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=TaskRead,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_task(
    data: TaskCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> TaskRead:
    service = TaskService(session)
    task = await service.create_task(data, current_user)

    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)
    ),
) -> TaskRead:
    service = TaskService(session)
    task = await service.get_task(task_id, current_user)

    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> TaskRead:
    service = TaskService(session)
    task = await service.update_task(task_id, data, current_user)

    return TaskRead.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    service = TaskService(session)
    await service.delete_task(task_id, current_user)

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)