"""Research run delegation to RunExecutor."""

from __future__ import annotations

import uuid

from agentos_chat.services.run_executor import get_run_executor


async def run_research(
    run_id: uuid.UUID,
    session_id: uuid.UUID,
    user_identity_id: uuid.UUID,
) -> None:
    executor = get_run_executor()
    await executor.execute_research_run(
        run_id=run_id,
        session_id=session_id,
        user_identity_id=user_identity_id,
    )
