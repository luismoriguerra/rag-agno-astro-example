import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.session import get_db_session
from agentos_chat.models.schemas import CreateMessageRequest, CreateMessageResponse
from agentos_chat.services.agent_service import AgentService

router = APIRouter(prefix="/api/chat/sessions", tags=["messages"])


@router.post(
    "/{session_id}/messages",
    response_model=CreateMessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_message(
    session_id: uuid.UUID,
    body: CreateMessageRequest,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> CreateMessageResponse:
    if not body.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "empty_message", "message": "Message cannot be empty."},
        )
    service = AgentService(db)
    result = await service.submit_message(identity.auth_subject, session_id, body.content.strip())
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Session not found."},
        )
    return result
