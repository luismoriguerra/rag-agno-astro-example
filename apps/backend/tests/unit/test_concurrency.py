import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentos_chat.services.concurrency import (
    CONCURRENT_RUN_LIMIT,
    RUN_IN_PROGRESS,
    ConcurrencyConflict,
    assert_can_start_run,
)


@pytest.mark.asyncio
async def test_run_in_progress_for_chat():
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db = MagicMock()

    with patch(
        "agentos_chat.services.concurrency.MessageRunRepository"
    ) as chat_repo_cls, patch(
        "agentos_chat.services.concurrency.ResearchRepository"
    ) as research_repo_cls:
        chat_repo = chat_repo_cls.return_value
        research_repo = research_repo_cls.return_value
        chat_repo.count_active_runs_for_user = AsyncMock(return_value=0)
        research_repo.count_active_research_runs_for_user = AsyncMock(return_value=0)
        chat_repo.has_active_chat_run = AsyncMock(return_value=True)

        with pytest.raises(ConcurrencyConflict) as exc:
            await assert_can_start_run(
                db,
                user_identity_id=user_id,
                session_id=session_id,
                workflow="chat",
            )
        assert exc.value.code == RUN_IN_PROGRESS.code


@pytest.mark.asyncio
async def test_concurrent_run_limit():
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db = MagicMock()

    with patch(
        "agentos_chat.services.concurrency.count_active_runs_for_user",
        new_callable=AsyncMock,
        return_value=10,
    ):
        with pytest.raises(ConcurrencyConflict) as exc:
            await assert_can_start_run(
                db,
                user_identity_id=user_id,
                session_id=session_id,
                workflow="research",
            )
        assert exc.value.code == CONCURRENT_RUN_LIMIT.code
