import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.message_run_repository import MessageRunRepository
from agentos_chat.db.session import get_db_session
from agentos_chat.services.run_events import run_event_bus

router = APIRouter(prefix="/api/chat/runs", tags=["stream"])


async def _sse_generator(run_id: uuid.UUID):
    async for item in run_event_bus.iter_events(run_id):
        if item is None:
            break
        payload = json.dumps(item.data)
        yield f"event: {item.event}\ndata: {payload}\n\n"


@router.get("/{run_id}/stream")
async def stream_agent_run(
    run_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    from agentos_chat.db.identity_session_repository import IdentitySessionRepository

    sessions = IdentitySessionRepository(db)
    repo = MessageRunRepository(db)
    user_id = await sessions.ensure_identity(identity.auth_subject)
    run = await repo.get_run_for_owner(run_id, user_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Run not found."},
        )
    return StreamingResponse(
        _sse_generator(run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
