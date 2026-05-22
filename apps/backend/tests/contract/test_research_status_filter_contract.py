import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.models import (
    ArticleStatusEnum,
    ChangeSourceEnum,
    ResearchAgentRun,
    ResearchArticle,
    ResearchArticleVersion,
    ResearchMessage,
    ResearchMessageRoleEnum,
    ResearchMessageStatusEnum,
    ResearchRunStatusEnum,
    ResearchSession,
)
from agentos_chat.db.repositories import get_or_create_identity


async def _create_session_with_status(
    db: AsyncSession,
    *,
    idea: str,
    article_status: ArticleStatusEnum | None = None,
    auth_subject: str = "auth0|test-user",
) -> uuid.UUID:
    """Create a research session, optionally with an article at the given status."""
    identity = await get_or_create_identity(db, auth_subject)
    session = ResearchSession(
        user_identity_id=identity.id,
        idea=idea,
        title=idea[:60],
    )
    db.add(session)
    await db.flush()

    msg = ResearchMessage(
        session_id=session.id,
        role=ResearchMessageRoleEnum.USER,
        content=idea,
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
    await db.flush()

    if article_status is not None:
        article = ResearchArticle(session_id=session.id, current_version=1)
        db.add(article)
        await db.flush()

        version = ResearchArticleVersion(
            article_id=article.id,
            version_number=1,
            markdown_content=f"# {idea}\n\nContent here.",
            status=article_status,
            change_source=ChangeSourceEnum.AGENT,
        )
        db.add(version)
        await db.flush()

    await db.commit()
    return session.id


@pytest.mark.asyncio
async def test_filter_draft_only(
    client: AsyncClient, db_session: AsyncSession, mock_headers: dict[str, str]
) -> None:
    draft_id = await _create_session_with_status(
        db_session, idea="draft session", article_status=ArticleStatusEnum.DRAFT
    )
    pub_id = await _create_session_with_status(
        db_session, idea="published session", article_status=ArticleStatusEnum.PUBLISHED
    )

    resp = await client.get("/api/research/sessions?status=draft", headers=mock_headers)
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()["sessions"]]
    assert str(draft_id) in ids
    assert str(pub_id) not in ids


@pytest.mark.asyncio
async def test_filter_published_only(
    client: AsyncClient, db_session: AsyncSession, mock_headers: dict[str, str]
) -> None:
    draft_id = await _create_session_with_status(
        db_session, idea="draft only", article_status=ArticleStatusEnum.DRAFT
    )
    pub_id = await _create_session_with_status(
        db_session, idea="published only", article_status=ArticleStatusEnum.PUBLISHED
    )

    resp = await client.get("/api/research/sessions?status=published", headers=mock_headers)
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()["sessions"]]
    assert str(pub_id) in ids
    assert str(draft_id) not in ids


@pytest.mark.asyncio
async def test_no_filter_returns_all(
    client: AsyncClient, db_session: AsyncSession, mock_headers: dict[str, str]
) -> None:
    draft_id = await _create_session_with_status(
        db_session, idea="all draft", article_status=ArticleStatusEnum.DRAFT
    )
    pub_id = await _create_session_with_status(
        db_session, idea="all published", article_status=ArticleStatusEnum.PUBLISHED
    )

    resp = await client.get("/api/research/sessions", headers=mock_headers)
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()["sessions"]]
    assert str(draft_id) in ids
    assert str(pub_id) in ids


@pytest.mark.asyncio
async def test_session_without_article_appears_in_draft(
    client: AsyncClient, db_session: AsyncSession, mock_headers: dict[str, str]
) -> None:
    no_article_id = await _create_session_with_status(
        db_session, idea="no article session", article_status=None
    )

    resp = await client.get("/api/research/sessions?status=draft", headers=mock_headers)
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()["sessions"]]
    assert str(no_article_id) in ids

    resp_pub = await client.get("/api/research/sessions?status=published", headers=mock_headers)
    assert resp_pub.status_code == 200
    pub_ids = [s["id"] for s in resp_pub.json()["sessions"]]
    assert str(no_article_id) not in pub_ids
