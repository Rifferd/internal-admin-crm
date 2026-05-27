from httpx import AsyncClient

from tests.conftest import auth_headers, login_user, register_user


async def test_register_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "password12345",
            "full_name": "Admin User",
            "role": "admin",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user"]["id"] == 1
    assert data["user"]["email"] == "admin@example.com"
    assert data["user"]["full_name"] == "Admin User"
    assert data["user"]["role"] == "admin"
    assert data["user"]["is_active"] is True


async def test_login_user(client: AsyncClient) -> None:
    await register_user(
        client,
        email="manager@example.com",
        role="manager",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "manager@example.com",
            "password": "password12345",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


async def test_get_me(client: AsyncClient) -> None:
    await register_user(
        client,
        email="viewer@example.com",
        full_name="Viewer User",
        role="viewer",
    )

    token = await login_user(client, email="viewer@example.com")

    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user"]["email"] == "viewer@example.com"
    assert data["user"]["role"] == "viewer"


async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await register_user(
        client,
        email="admin@example.com",
        role="admin",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"