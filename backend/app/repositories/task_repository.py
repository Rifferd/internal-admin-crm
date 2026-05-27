from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TaskStatus
from app.models.task import Task


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: TaskStatus | None,
        deal_id: int | None,
        assigned_to: int | None,
        visible_assigned_to: int | None,
        overdue_only: bool,
        offset: int,
        limit: int,
    ) -> tuple[list[Task], int]:
        base_stmt = self._apply_filters(
            select(Task),
            status=status,
            deal_id=deal_id,
            assigned_to=assigned_to,
            visible_assigned_to=visible_assigned_to,
            overdue_only=overdue_only,
        )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        list_stmt = (
            base_stmt
            .order_by(Task.deadline.asc(), Task.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        tasks_result = await self.session.execute(list_stmt)
        tasks = list(tasks_result.scalars().all())

        return tasks, total

    async def create(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()

    def _apply_filters(
        self,
        stmt: Select[tuple[Task]],
        *,
        status: TaskStatus | None,
        deal_id: int | None,
        assigned_to: int | None,
        visible_assigned_to: int | None,
        overdue_only: bool,
    ) -> Select[tuple[Task]]:
        if status:
            stmt = stmt.where(Task.status == status)

        if deal_id:
            stmt = stmt.where(Task.deal_id == deal_id)

        if assigned_to:
            stmt = stmt.where(Task.assigned_to == assigned_to)

        if visible_assigned_to:
            stmt = stmt.where(Task.assigned_to == visible_assigned_to)

        if overdue_only:
            stmt = stmt.where(Task.deadline < datetime.now(UTC))
            stmt = stmt.where(Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]))

        return stmt