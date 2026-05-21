import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_settings_lazy_creates_defaults(client: AsyncClient, auth_headers, db_session) -> None:
    response = await client.get("/api/whatsapp/settings", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["allowed_phone_numbers"] == []


@pytest.mark.asyncio
async def test_patch_settings_toggle(client: AsyncClient, auth_headers) -> None:
    response = await client.patch(
        "/api/whatsapp/settings",
        headers=auth_headers,
        json={"enabled": True},
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is True


@pytest.mark.asyncio
async def test_add_allowlist_phone(client: AsyncClient, auth_headers) -> None:
    response = await client.post(
        "/api/whatsapp/settings/allowlist",
        headers=auth_headers,
        json={"phone_number": "+14155552671"},
    )
    assert response.status_code == 201
    numbers = [entry["phone_number"] for entry in response.json()["allowed_phone_numbers"]]
    assert "+14155552671" in numbers


@pytest.mark.asyncio
async def test_add_invalid_phone_returns_400(client: AsyncClient, auth_headers) -> None:
    response = await client.post(
        "/api/whatsapp/settings/allowlist",
        headers=auth_headers,
        json={"phone_number": "not-a-phone"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_phone_number"


@pytest.mark.asyncio
async def test_duplicate_phone_returns_409(client: AsyncClient, auth_headers) -> None:
    payload = {"phone_number": "+14155552672"}
    first = await client.post(
        "/api/whatsapp/settings/allowlist",
        headers=auth_headers,
        json=payload,
    )
    assert first.status_code == 201
    second = await client.post(
        "/api/whatsapp/settings/allowlist",
        headers=auth_headers,
        json=payload,
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_delete_allowlist_phone(client: AsyncClient, auth_headers) -> None:
    await client.post(
        "/api/whatsapp/settings/allowlist",
        headers=auth_headers,
        json={"phone_number": "+14155552673"},
    )
    response = await client.delete(
        "/api/whatsapp/settings/allowlist/%2B14155552673",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["allowed_phone_numbers"] == []


@pytest.mark.asyncio
async def test_settings_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/whatsapp/settings")
    assert response.status_code == 401
