from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TaskStatus, UserRole
from app.common.pagination import build_page_meta
from app.models.task import Task
from app.models.user import User
from app.repositories.deal_repository import DealRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskRead,
    TaskUpdate,
)


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repository = TaskRepository(session)
        self.deal_repository = DealRepository(session)
        self.user_repository = UserRepository(session)

    async def list_tasks(
        self,
        *,
        current_user: User,
        task_status: TaskStatus | None,
        deal_id: int | None,
        assigned_to: int | None,
        overdue_only: bool,
        page: int,
        size: int,
    ) -> TaskListResponse:
        offset = (page - 1) * size
        visible_assigned_to = None

        if current_user.role == UserRole.MANAGER:
            visible_assigned_to = current_user.id

        tasks, total = await self.task_repository.list(
            status=task_status,
            deal_id=deal_id,
            assigned_to=assigned_to,
            visible_assigned_to=visible_assigned_to,
            overdue_only=overdue_only,
            offset=offset,
            limit=size,
        )

        return TaskListResponse(
            items=[TaskRead.model_validate(task) for task in tasks],
            meta=build_page_meta(page=page, size=size, total=total),
        )

    async def list_my_tasks(
        self,
        *,
        current_user: User,
        task_status: TaskStatus | None,
        page: int,
        size: int,
    ) -> TaskListResponse:
        offset = (page - 1) * size

        tasks, total = await self.task_repository.list(
            status=task_status,
            deal_id=None,
            assigned_to=current_user.id,
            visible_assigned_to=None,
            overdue_only=False,
            offset=offset,
            limit=size,
        )

        return TaskListResponse(
            items=[TaskRead.model_validate(task) for task in tasks],
            meta=build_page_meta(page=page, size=size, total=total),
        )

    async def list_overdue_tasks(
        self,
        *,
        current_user: User,
        page: int,
        size: int,
    ) -> TaskListResponse:
        return await self.list_tasks(
            current_user=current_user,
            task_status=None,
            deal_id=None,
            assigned_to=None,
            overdue_only=True,
            page=page,
            size=size,
        )

    async def get_task(self, task_id: int, current_user: User) -> Task:
        task = await self.task_repository.get_by_id(task_id)

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        self._check_can_view_task(task, current_user)

        return task

    async def create_task(self, data: TaskCreate, current_user: User) -> Task:
        await self._ensure_deal_exists_for_user(data.deal_id, current_user)

        assigned_to = await self._resolve_assigned_to_for_create(data, current_user)

        task = Task(
            deal_id=data.deal_id,
            assigned_to=assigned_to,
            title=data.title,
            description=data.description,
            deadline=data.deadline,
            status=data.status,
        )

        task = await self.task_repository.create(task)

        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def update_task(
        self,
        task_id: int,
        data: TaskUpdate,
        current_user: User,
    ) -> Task:
        task = await self.get_task(task_id, current_user)

        update_data = data.model_dump(exclude_unset=True)

        if current_user.role == UserRole.MANAGER:
            if "assigned_to" in update_data and update_data["assigned_to"] != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Manager cannot reassign tasks to other users",
                )

        if "deal_id" in update_data:
            await self._ensure_deal_exists_for_user(update_data["deal_id"], current_user)

        if "assigned_to" in update_data:
            await self._ensure_user_can_be_assigned(update_data["assigned_to"])

        for field, value in update_data.items():
            setattr(task, field, value)

        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def delete_task(self, task_id: int, current_user: User) -> None:
        task = await self.get_task(task_id, current_user)

        await self.task_repository.delete(task)
        await self.session.commit()

    async def _ensure_deal_exists_for_user(
        self,
        deal_id: int,
        current_user: User,
    ) -> None:
        deal = await self.deal_repository.get_by_id(deal_id)

        if deal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found",
            )

        if current_user.role == UserRole.ADMIN:
            return

        if current_user.role == UserRole.MANAGER and deal.manager_id == current_user.id:
            return

        if current_user.role == UserRole.VIEWER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Viewer cannot create or edit tasks",
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    async def _resolve_assigned_to_for_create(
        self,
        data: TaskCreate,
        current_user: User,
    ) -> int:
        if current_user.role == UserRole.ADMIN:
            assigned_to = data.assigned_to or current_user.id
            await self._ensure_user_can_be_assigned(assigned_to)
            return assigned_to

        if current_user.role == UserRole.MANAGER:
            if data.assigned_to is not None and data.assigned_to != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Manager can assign tasks only to himself",
                )

            return current_user.id

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    async def _ensure_user_can_be_assigned(self, user_id: int) -> None:
        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user is inactive",
            )

        if user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task can be assigned only to admin or manager",
            )

    def _check_can_view_task(self, task: Task, current_user: User) -> None:
        if current_user.role == UserRole.ADMIN:
            return

        if current_user.role == UserRole.VIEWER:
            return

        if current_user.role == UserRole.MANAGER and task.assigned_to == current_user.id:
            return

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )