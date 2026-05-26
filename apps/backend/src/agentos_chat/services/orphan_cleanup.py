"""Mark in-progress runs as failed after application restart."""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.models import AgentRun, ResearchAgentRun, ResearchRunStatusEnum, RunStatusEnum

_ACTIVE_STATUSES = (
    RunStatusEnum.QUEUED,
    RunStatusEnum.RUNNING,
    RunStatusEnum.STOPPING,
)

_RESEARCH_ACTIVE = (
    ResearchRunStatusEnum.QUEUED,
    ResearchRunStatusEnum.RUNNING,
    ResearchRunStatusEnum.STOPPING,
)


async def cleanup_orphaned_runs(db: AsyncSession) -> tuple[int, int]:
    """Transition orphaned chat and research runs to failed. Returns (chat, research) counts."""
    chat_result = await db.execute(
        update(AgentRun)
        .where(AgentRun.status.in_(_ACTIVE_STATUSES))
        .values(
            status=RunStatusEnum.FAILED,
            error_code="orphaned",
            error_message="Run was interrupted by application restart.",
        )
    )
    research_result = await db.execute(
        update(ResearchAgentRun)
        .where(ResearchAgentRun.status.in_(_RESEARCH_ACTIVE))
        .values(
            status=ResearchRunStatusEnum.FAILED,
            error_code="orphaned",
            error_message="Run was interrupted by application restart.",
        )
    )
    await db.flush()
    return int(chat_result.rowcount or 0), int(research_result.rowcount or 0)
