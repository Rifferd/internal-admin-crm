from httpx import AsyncClient

from tests.conftest import auth_headers, login_user, register_user


async def test_viewer_can_view_clients_but_cannot_create(client: AsyncClient) -> None:
    await register_user(
        client,
        email="viewer@example.com",
        role="viewer",
    )

    token = await login_user(client, email="viewer@example.com")

    list_response = await client.get(
        "/api/v1/clients",
        headers=auth_headers(token),
    )

    assert list_response.status_code == 200

    create_response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "Viewer Client",
            "phone": "+996700333444",
            "email": "viewer-client@example.com",
            "source": "test",
            "status": "lead",
        },
    )

    assert create_response.status_code == 403
    assert create_response.json()["detail"] == "Not enough permissions"


async def test_viewer_cannot_create_deal(client: AsyncClient) -> None:
    await register_user(
        client,
        email="viewer@example.com",
        role="viewer",
    )

    token = await login_user(client, email="viewer@example.com")

    response = await client.post(
        "/api/v1/deals",
        headers=auth_headers(token),
        json={
            "client_id": 1,
            "title": "Viewer Deal",
            "amount": "10000.00",
            "status": "new",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


async def test_unauthorized_request_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/clients")

    assert response.status_code == 401