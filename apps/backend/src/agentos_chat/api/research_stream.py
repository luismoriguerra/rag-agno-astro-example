import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.repositories import get_or_create_identity
from agentos_chat.db.research_repository import ResearchRepository
from agentos_chat.db.session import get_db_session
from agentos_chat.services.run_events import run_event_bus

router = APIRouter(prefix="/api/research", tags=["research-stream"])


async def _sse_generator(run_id: uuid.UUID):
    async for item in run_event_bus.iter_events(run_id):
        if item is None:
            break
        payload = json.dumps(item.data)
        yield f"event: {item.event}\ndata: {payload}\n\n"


@router.get("/runs/{run_id}/stream")
async def stream_research_run(
    run_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)
    run = await repo.get_run_for_owner(run_id, user_identity.id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Research run not found."},
        )
    return StreamingResponse(
        _sse_generator(run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/runs/{run_id}/stop")
async def stop_research_run(
    run_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    user_identity = await get_or_create_identity(db, identity.auth_subject)
    repo = ResearchRepository(db)
    run = await repo.get_run_for_owner(run_id, user_identity.id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Research run not found."},
        )
    run_event_bus.request_cancel(run_id)
    return {"status": "stopping"}
