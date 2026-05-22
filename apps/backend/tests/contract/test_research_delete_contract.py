import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.models import (
    ResearchAgentRun,
    ResearchMessage,
    ResearchMessageRoleEnum,
    ResearchMessageStatusEnum,
    ResearchRunStatusEnum,
    ResearchSession,
)
from agentos_chat.db.repositories import get_or_create_identity


async def _create_session_directly(
    db: AsyncSession, *, auth_subject: str = "auth0|test-user"
) -> uuid.UUID:
    """Insert a research session with a completed run so it's deleteable."""
    identity = await get_or_create_identity(db, auth_subject)
    session = ResearchSession(
        user_identity_id=identity.id,
        idea="test delete idea",
        title="test delete idea",
    )
    db.add(session)
    await db.flush()

    msg = ResearchMessage(
        session_id=session.id,
        role=ResearchMessageRoleEnum.USER,
        content="test delete idea",
        status=ResearchMessageStatusEnum.COMPLETE,
        sequence_index=0,
    )
    db.add(msg)
    await db.flush()

    run = ResearchAgentRun(
        session_id=session.id,
        user_message_id=msg.id,
        status=ResearchRunStatusEnum.COMPLETED,
    )
    db.add(run)
    await db.commit()
    return session.id


@pytest.mark.asyncio
async def test_delete_session_lifecycle(
    client: AsyncClient, db_session: AsyncSession, mock_headers: dict[str, str]
) -> None:
    session_id = await _create_session_directly(db_session)

    listed = await client.get("/api/research/sessions", headers=mock_headers)
    assert listed.status_code == 200
    assert any(s["id"] == str(session_id) for s in listed.json()["sessions"])

    deleted = await client.delete(
        f"/api/research/sessions/{session_id}", headers=mock_headers
    )
    assert deleted.status_code == 204

    listed_after = await client.get("/api/research/sessions", headers=mock_headers)
    assert not any(
        s["id"] == str(session_id) for s in listed_after.json()["sessions"]
    )

    detail = await client.get(
        f"/api/research/sessions/{session_id}", headers=mock_headers
    )
    assert detail.status_code == 404


@pytest.mark.asyncio
async def test_delete_unknown_session_returns_404(
    client: AsyncClient, mock_headers: dict[str, str]
) -> None:
    fake_id = uuid.uuid4()
    resp = await client.delete(
        f"/api/research/sessions/{fake_id}", headers=mock_headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_with_active_run_returns_409(
    client: AsyncClient, db_session: AsyncSession, mock_headers: dict[str, str]
) -> None:
    identity = await get_or_create_identity(db_session, "auth0|test-user")
    session = ResearchSession(
        user_identity_id=identity.id,
        idea="active run idea",
        title="active run idea",
    )
    db_session.add(session)
    await db_session.flush()

    msg = ResearchMessage(
        session_id=session.id,
        role=ResearchMessageRoleEnum.USER,
        content="active run idea",
        status=ResearchMessageStatusEnum.COMPLETE,
        sequence_index=0,
    )
    db_session.add(msg)
    await db_session.flush()

    run = ResearchAgentRun(
        session_id=session.id,
        user_message_id=msg.id,
        status=ResearchRunStatusEnum.RUNNING,
    )
    db_session.add(run)
    await db_session.commit()

    resp = await client.delete(
        f"/api/research/sessions/{session.id}", headers=mock_headers
    )
    assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
