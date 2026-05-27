from httpx import AsyncClient

from tests.conftest import auth_headers, login_user, register_user


async def create_admin_token(client: AsyncClient) -> str:
    await register_user(
        client,
        email="admin@example.com",
        role="admin",
    )

    return await login_user(client, email="admin@example.com")


async def create_manager(client: AsyncClient) -> tuple[int, str]:
    register_response = await register_user(
        client,
        email="manager@example.com",
        role="manager",
    )

    manager_id = register_response["user"]["id"]
    token = await login_user(client, email="manager@example.com")

    return manager_id, token


async def create_client(client: AsyncClient, token: str) -> int:
    response = await client.post(
        "/api/v1/clients",
        headers=auth_headers(token),
        json={
            "name": "ОсОО Бета",
            "phone": "+996700555666",
            "email": "beta@example.com",
            "source": "website",
            "status": "active",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


async def test_create_deal(client: AsyncClient) -> None:
    admin_token = await create_admin_token(client)
    manager_id, _manager_token = await create_manager(client)
    client_id = await create_client(client, admin_token)

    response = await client.post(
        "/api/v1/deals",
        headers=auth_headers(admin_token),
        json={
            "client_id": client_id,
            "manager_id": manager_id,
            "title": "Продажа CRM",
            "amount": "50000.00",
            "status": "new",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["client_id"] == client_id
    assert data["manager_id"] == manager_id
    assert data["title"] == "Продажа CRM"
    assert data["amount"] == "50000.00"
    assert data["status"] == "new"
    assert data["closed_at"] is None


async def test_deal_closed_at_rule_for_won_status(client: AsyncClient) -> None:
    admin_token = await create_admin_token(client)
    manager_id, _manager_token = await create_manager(client)
    client_id = await create_client(client, admin_token)

    create_response = await client.post(
        "/api/v1/deals",
        headers=auth_headers(admin_token),
        json={
            "client_id": client_id,
            "manager_id": manager_id,
            "title": "Продажа CRM",
            "amount": "50000.00",
            "status": "new",
        },
    )

    deal_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/deals/{deal_id}",
        headers=auth_headers(admin_token),
        json={
            "status": "won",
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["status"] == "won"
    assert data["closed_at"] is not None


async def test_manager_sees_only_own_deals(client: AsyncClient) -> None:
    admin_token = await create_admin_token(client)

    manager_id, manager_token = await create_manager(client)

    register_response = await register_user(
        client,
        email="other-manager@example.com",
        role="manager",
    )
    other_manager_id = register_response["user"]["id"]

    client_id = await create_client(client, admin_token)

    await client.post(
        "/api/v1/deals",
        headers=auth_headers(admin_token),
        json={
            "client_id": client_id,
            "manager_id": manager_id,
            "title": "Своя сделка",
            "amount": "50000.00",
            "status": "new",
        },
    )

    await client.post(
        "/api/v1/deals",
        headers=auth_headers(admin_token),
        json={
            "client_id": client_id,
            "manager_id": other_manager_id,
            "title": "Чужая сделка",
            "amount": "10000.00",
            "status": "new",
        },
    )

    response = await client.get(
        "/api/v1/deals",
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meta"]["total"] == 1
    assert data["items"][0]["title"] == "Своя сделка"