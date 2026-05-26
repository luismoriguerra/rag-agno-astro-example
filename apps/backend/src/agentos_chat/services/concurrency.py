"""Per-session and per-user run concurrency guards."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.message_run_repository import MessageRunRepository
from agentos_chat.db.research_repository import ResearchRepository

MAX_CONCURRENT_RUNS_PER_USER = 10


@dataclass(frozen=True)
class ConcurrencyConflict(Exception):
    code: str
    message: str


RUN_IN_PROGRESS = ConcurrencyConflict(
    code="run_in_progress",
    message="An agent run is already in progress.",
)

CONCURRENT_RUN_LIMIT = ConcurrencyConflict(
    code="concurrent_run_limit",
    message=(
        "You have reached the maximum of 10 concurrent agent runs. "
        "Wait for a run to finish or stop one."
    ),
)


async def count_active_runs_for_user(db: AsyncSession, user_identity_id: uuid.UUID) -> int:
    chat_repo = MessageRunRepository(db)
    research_repo = ResearchRepository(db)
    chat_count = await chat_repo.count_active_runs_for_user(user_identity_id)
    research_count = await research_repo.count_active_research_runs_for_user(user_identity_id)
    return chat_count + research_count


async def assert_can_start_run(
    db: AsyncSession,
    *,
    user_identity_id: uuid.UUID,
    session_id: uuid.UUID,
    workflow: str,
) -> None:
    """Raise ConcurrencyConflict when session or user limits would be exceeded."""
    if await count_active_runs_for_user(db, user_identity_id) >= MAX_CONCURRENT_RUNS_PER_USER:
        raise CONCURRENT_RUN_LIMIT

    if workflow == "chat":
        if await MessageRunRepository(db).has_active_chat_run(session_id):
            raise RUN_IN_PROGRESS
    elif workflow == "research":
        if await ResearchRepository(db).has_active_research_run(session_id):
            raise RUN_IN_PROGRESS
    else:
        raise ValueError(f"Unknown workflow: {workflow}")
