import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.redis import redis_client
from app.db.session import async_session_maker
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def clean_database_and_redis() -> None:
    async with async_session_maker() as session:
        await session.execute(
            text(
                """
                TRUNCATE TABLE
                    tasks,
                    deals,
                    clients,
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )
        await session.commit()

    await redis_client.flushdb()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def register_user(
    client: AsyncClient,
    *,
    email: str,
    password: str = "password12345",
    full_name: str = "Test User",
    role: str = "viewer",
) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
        },
    )

    assert response.status_code == 201

    return response.json()


async def login_user(
    client: AsyncClient,
    *,
    email: str,
    password: str = "password12345",
) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}