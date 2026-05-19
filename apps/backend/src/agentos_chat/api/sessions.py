import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.session import get_db_session
from agentos_chat.models.schemas import (
    ChatSessionDetailSchema,
    ChatSessionListResponse,
    ChatSessionSchema,
)
from agentos_chat.services.session_service import SessionService

router = APIRouter(prefix="/api/chat/sessions", tags=["sessions"])


@router.get("", response_model=ChatSessionListResponse)
async def list_sessions(
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> ChatSessionListResponse:
    service = SessionService(db)
    sessions = await service.list_sessions(identity.auth_subject)
    return ChatSessionListResponse(sessions=sessions)


@router.post("", response_model=ChatSessionSchema, status_code=status.HTTP_201_CREATED)
async def create_session(
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> ChatSessionSchema:
    service = SessionService(db)
    return await service.create_session(identity.auth_subject)


@router.get("/{session_id}", response_model=ChatSessionDetailSchema)
async def get_session(
    session_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> ChatSessionDetailSchema:
    service = SessionService(db)
    detail = await service.restore_session(identity.auth_subject, session_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Session not found."},
        )
    await db.commit()
    return detail


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = SessionService(db)
    deleted = await service.delete_session(identity.auth_subject, session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Session not found."},
        )
