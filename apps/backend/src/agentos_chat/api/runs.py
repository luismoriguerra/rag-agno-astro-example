import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.session import get_db_session
from agentos_chat.models.schemas import RunStatusEnum as RunStatusSchemaEnum
from agentos_chat.models.schemas import RunStatusSchema
from agentos_chat.services.agent_service import AgentService

router = APIRouter(prefix="/api/chat/runs", tags=["runs"])


@router.post("/{run_id}/stop", response_model=RunStatusSchema, status_code=status.HTTP_202_ACCEPTED)
async def stop_agent_run(
    run_id: uuid.UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> RunStatusSchema:
    service = AgentService(db)
    result = await service.stop_run(identity.auth_subject, run_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Run not found."},
        )
    if result.status == RunStatusSchemaEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "run_terminal", "message": "Run is already complete."},
        )
    return result
