import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.models import (
    ResearchMessageRoleEnum,
    ResearchRunStatusEnum,
)
from agentos_chat.db.repositories import get_or_create_identity
from agentos_chat.db.research_repository import ResearchRepository
from agentos_chat.db.session import get_db_session
from agentos_chat.models.research_schemas import (
    ArticleSchema,
    ArticleStatus,
    ArticleVersionSchema,
    ChangeSource,
    CreateResearchSessionRequest,
    CreateResearchSessionResponse,
    ResearchMessageRole,
    ResearchMessageSchema,
    ResearchMessageStatus,
    ResearchSessionDetailResponse,
    ResearchSessionListResponse,
    ResearchSessionSummary,
    RetryResponse,
    SendMessageRequest,
    SendMessageResponse,
    SessionCostSummary,
)
from agentos_chat.services.research_service import run_research
from agentos_chat.services.run_events import run_event_bus

router = APIRouter(prefix="/api/research", tags=["research-sessions"])


def _session_summary(session) -> ResearchSessionSummary:
    active_statuses = (ResearchRunStatusEnum.QUEUED.value, ResearchRunStatusEnum.RUNNING.value)
    active_run_id = None
    is_generating = False
    for r in session.runs or []:
        run_status = r.status if isinstance(r.status, str) else r.status.value
        if run_status in active_statuses:
            is_generating = True
            active_run_id = r.id
            break

    current_version = None
    article_status = ArticleStatus.DRAFT
    if session.article:
        current_version = session.article.current_version
        if session.article.versions:
            latest = max(session.article.versions, key=lambda v: v.version_number)
            raw_status = latest.status if isinstance(latest.status, str) else latest.status.value
            article_status = ArticleStatus(raw_status)

    return ResearchSessionSummary(
        id=session.id,
        title=session.title,
        idea=session.idea,
        status=article_status,
        is_generating=is_generating,
        active_run_id=active_run_id,
        current_version=current_version,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_research_session(
    body: CreateResearchSessionRequest,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> CreateResearchSessionResponse:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)

    session = await repo.create_session(user_identity.id, body.idea)

    user_msg = await repo.create_message(
        session.id,
        ResearchMessageRoleEnum.USER,
        body.idea,
    )

    run = await repo.create_agent_run(session.id, user_msg.id)
    await db.commit()

    run_event_bus.create(run.id)
    asyncio.create_task(run_research(run.id, session.id, user_identity.id))

    return CreateResearchSessionResponse(
        session_id=session.id,
        title=session.title,
        status=ArticleStatus.DRAFT,
        created_at=session.created_at,
        run_id=run.id,
    )


@router.get("/sessions")
async def list_research_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status: str | None = Query(None, pattern="^(draft|published)$"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> ResearchSessionListResponse:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)
    sessions, total = await repo.list_sessions_paginated(
        user_identity.id, page, page_size, status=status
    )
    return ResearchSessionListResponse(
        sessions=[_session_summary(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_session(
    session_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)

    try:
        deleted = await repo.delete_session(session_id, user_identity.id)
    except ValueError as exc:
        if str(exc) == "run_in_progress":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "run_in_progress",
                    "message": "Cannot delete while an agent run is in progress.",
                },
            ) from exc
        raise

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Research session not found."},
        )

    await db.commit()


@router.get("/sessions/{session_id}")
async def get_research_session(
    session_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> ResearchSessionDetailResponse:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)
    session = await repo.get_session_for_owner(session_id, user_identity.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Research session not found."},
        )

    messages_rows = await repo.list_messages(session_id)
    messages = [
        ResearchMessageSchema(
            id=m.id,
            role=ResearchMessageRole(m.role if isinstance(m.role, str) else m.role.value),
            content=m.content,
            reasoning_content=m.reasoning_content,
            status=ResearchMessageStatus(m.status if isinstance(m.status, str) else m.status.value),
            sequence_index=m.sequence_index,
            created_at=m.created_at,
        )
        for m in messages_rows
    ]

    article_schema = None
    if session.article:
        latest_version = None
        if session.article.versions:
            latest = max(session.article.versions, key=lambda v: v.version_number)
            latest_version = ArticleVersionSchema(
                id=latest.id,
                version_number=latest.version_number,
                markdown_content=latest.markdown_content,
                status=ArticleStatus(
                    latest.status if isinstance(latest.status, str) else latest.status.value
                ),
                change_source=ChangeSource(
                    latest.change_source
                    if isinstance(latest.change_source, str)
                    else latest.change_source.value
                ),
                created_at=latest.created_at,
            )
        article_schema = ArticleSchema(
            id=session.article.id,
            current_version=session.article.current_version,
            latest_version=latest_version,
        )

    cost_data = await repo.get_session_total_cost(session_id)
    costs = SessionCostSummary(**cost_data) if cost_data["total_tokens"] > 0 else None

    return ResearchSessionDetailResponse(
        session=_session_summary(session),
        article=article_schema,
        messages=messages,
        costs=costs,
    )


@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_research_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> SendMessageResponse:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)

    session = await repo.get_session_for_owner(session_id, user_identity.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Research session not found."},
        )

    if await repo.has_active_run(session_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "run_in_progress", "message": "An agent run is already in progress."},
        )

    user_msg = await repo.create_message(
        session_id,
        ResearchMessageRoleEnum.USER,
        body.content,
    )
    run = await repo.create_agent_run(session_id, user_msg.id)
    await db.commit()

    run_event_bus.create(run.id)
    asyncio.create_task(run_research(run.id, session_id, user_identity.id))

    return SendMessageResponse(message_id=user_msg.id, run_id=run.id)


@router.post("/sessions/{session_id}/retry", status_code=status.HTTP_201_CREATED)
async def retry_research_session(
    session_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> RetryResponse:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)

    session = await repo.get_session_for_owner(session_id, user_identity.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Research session not found."},
        )

    if await repo.has_active_run(session_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "run_in_progress", "message": "An agent run is already in progress."},
        )

    messages = await repo.list_messages(session_id)
    last_user_msg = next(
        (
            m
            for m in reversed(messages)
            if (m.role if isinstance(m.role, str) else m.role.value) == "user"
        ),
        None,
    )
    if not last_user_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "no_user_message", "message": "No user message to retry."},
        )

    run = await repo.create_agent_run(session_id, last_user_msg.id)
    await db.commit()

    run_event_bus.create(run.id)
    asyncio.create_task(run_research(run.id, session_id, user_identity.id))

    return RetryResponse(run_id=run.id)
