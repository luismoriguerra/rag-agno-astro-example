import pytest
from httpx import AsyncClient

from agentos_chat.db.models import ChatSession, SessionStatusEnum, UserIdentity
from tests.conftest import make_test_jwt


@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/chat/sessions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_missing_scope_returns_403(
    client: AsyncClient,
    auth_headers_no_scope: dict[str, str],
) -> None:
    response = await client.get("/api/chat/sessions", headers=auth_headers_no_scope)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_auth0_style_scope_string_is_accepted(
    client: AsyncClient,
) -> None:
    token = make_test_jwt(scope="openid profile email access:api offline_access")
    response = await client.get(
        "/api/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_authenticated_user_can_create_and_list_sessions(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    create = await client.post("/api/chat/sessions", headers=auth_headers)
    assert create.status_code == 201

    listed = await client.get("/api/chat/sessions", headers=auth_headers)
    assert listed.status_code == 200
    body = listed.json()
    assert len(body["sessions"]) == 1


@pytest.mark.asyncio
async def test_cross_identity_cannot_read_other_users_session(
    client: AsyncClient,
    db_session,
) -> None:
    user_a = make_test_jwt(sub="auth0|user-a")
    user_b = make_test_jwt(sub="auth0|user-b")

    created = await client.post(
        "/api/chat/sessions",
        headers={"Authorization": f"Bearer {user_a}"},
    )
    session_id = created.json()["id"]

    forbidden = await client.get(
        f"/api/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {user_b}"},
    )
    assert forbidden.status_code == 404


@pytest.mark.asyncio
async def test_auth0_identity_does_not_see_mock_owned_sessions(
    client: AsyncClient,
    db_session,
) -> None:
    mock_identity = UserIdentity(auth_subject="mock|legacy-user", display_name="Legacy")
    db_session.add(mock_identity)
    await db_session.flush()

    mock_session = ChatSession(
        user_identity_id=mock_identity.id,
        title="Legacy chat",
        status=SessionStatusEnum.ACTIVE,
    )
    db_session.add(mock_session)
    await db_session.commit()

    token = make_test_jwt(sub="auth0|new-user")
    listed = await client.get(
        "/api/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert listed.json()["sessions"] == []
