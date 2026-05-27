import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.common.enums import ClientStatus, DealStatus, TaskStatus, UserRole
from app.core.security import hash_password
from app.db.session import async_session_maker
from app.models.client import Client
from app.models.deal import Deal
from app.models.task import Task
from app.models.user import User


async def get_or_create_user(
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
) -> User:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is not None:
            return user

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
        )

        session.add(user)

        await session.commit()
        await session.refresh(user)

        return user


async def create_seed_data() -> None:
    admin = await get_or_create_user(
        email="admin@example.com",
        password="admin12345",
        full_name="Admin User",
        role=UserRole.ADMIN,
    )

    manager = await get_or_create_user(
        email="manager@example.com",
        password="manager12345",
        full_name="Manager User",
        role=UserRole.MANAGER,
    )

    await get_or_create_user(
        email="viewer@example.com",
        password="viewer12345",
        full_name="Viewer User",
        role=UserRole.VIEWER,
    )

    async with async_session_maker() as session:
        clients_count = await session.execute(select(Client))
        existing_clients = clients_count.scalars().first()

        if existing_clients is not None:
            print("Seed data already exists. Skipping clients/deals/tasks.")
            return

        client_alpha = Client(
            name="ОсОО Альфа",
            phone="+996700111222",
            email="alpha@example.com",
            source="instagram",
            status=ClientStatus.ACTIVE,
        )

        client_beta = Client(
            name="ОсОО Бета",
            phone="+996700555666",
            email="beta@example.com",
            source="website",
            status=ClientStatus.LEAD,
        )

        client_gamma = Client(
            name="ИП Гамма",
            phone="+996700777888",
            email="gamma@example.com",
            source="referral",
            status=ClientStatus.INACTIVE,
        )

        session.add_all([client_alpha, client_beta, client_gamma])
        await session.flush()

        deal_1 = Deal(
            client_id=client_alpha.id,
            manager_id=manager.id,
            title="Продажа CRM",
            amount=Decimal("50000.00"),
            status=DealStatus.WON,
            closed_at=datetime.now(UTC) - timedelta(days=3),
        )

        deal_2 = Deal(
            client_id=client_beta.id,
            manager_id=manager.id,
            title="Настройка админки",
            amount=Decimal("30000.00"),
            status=DealStatus.IN_PROGRESS,
            closed_at=None,
        )

        deal_3 = Deal(
            client_id=client_gamma.id,
            manager_id=admin.id,
            title="Интеграция аналитики",
            amount=Decimal("70000.00"),
            status=DealStatus.NEW,
            closed_at=None,
        )

        session.add_all([deal_1, deal_2, deal_3])
        await session.flush()

        task_1 = Task(
            deal_id=deal_1.id,
            assigned_to=manager.id,
            title="Подготовить договор",
            description="Согласовать условия и отправить клиенту.",
            deadline=datetime.now(UTC) + timedelta(days=2),
            status=TaskStatus.TODO,
        )

        task_2 = Task(
            deal_id=deal_2.id,
            assigned_to=manager.id,
            title="Позвонить клиенту",
            description="Уточнить требования по админке.",
            deadline=datetime.now(UTC) - timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
        )

        task_3 = Task(
            deal_id=deal_3.id,
            assigned_to=admin.id,
            title="Проверить интеграцию",
            description="Проверить технические требования.",
            deadline=datetime.now(UTC) + timedelta(days=5),
            status=TaskStatus.TODO,
        )

        session.add_all([task_1, task_2, task_3])

        await session.commit()

    print("Seed data created successfully.")


if __name__ == "__main__":
    asyncio.run(create_seed_data())