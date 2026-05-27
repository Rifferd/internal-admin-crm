from httpx import AsyncClient

from tests.conftest import auth_headers, login_user, register_user


async def create_admin_token(client: AsyncClient) -> str:
    await register_user(
        client,
        email="admin@example.com",
        role="admin",
    )

    return await login_user(client, email="admin@example.com")


async def test_create_client(client: AsyncClient) -> None:
    token = await create_admin_token(client)

    response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "ОсОО Альфа",
            "phone": "+996700111222",
            "email": "alpha@example.com",
            "source": "instagram",
            "status": "lead",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "ОсОО Альфа"
    assert data["email"] == "alpha@example.com"
    assert data["status"] == "lead"
    assert data["deleted_at"] is None


async def test_list_clients(client: AsyncClient) -> None:
    token = await create_admin_token(client)

    await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "ОсОО Альфа",
            "phone": "+996700111222",
            "email": "alpha@example.com",
            "source": "instagram",
            "status": "lead",
        },
    )

    response = await client.get(
        "/api/v1/clients?page=1&size=10",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meta"]["total"] == 1
    assert data["items"][0]["name"] == "ОсОО Альфа"


async def test_update_client(client: AsyncClient) -> None:
    token = await create_admin_token(client)

    create_response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "ОсОО Альфа",
            "phone": "+996700111222",
            "email": "alpha@example.com",
            "source": "instagram",
            "status": "lead",
        },
    )

    client_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(token),
        json={
            "status": "active",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "active"


async def test_delete_client_soft_delete(client: AsyncClient) -> None:
    token = await create_admin_token(client)

    create_response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "ОсОО Альфа",
            "phone": "+996700111222",
            "email": "alpha@example.com",
            "source": "instagram",
            "status": "lead",
        },
    )

    client_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/clients/{client_id}",
        headers=auth_headers(token),
    )

    assert delete_response.status_code == 204

    list_response = await client.get(
        "/api/v1/clients",
        headers=auth_headers(token),
    )

    assert list_response.status_code == 200
    assert list_response.json()["meta"]["total"] == 0