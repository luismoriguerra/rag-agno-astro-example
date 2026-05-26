"""Unit tests for RunExecutor finalization paths."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentos_chat.db.models import (
    AgentRun,
    MessageStatusEnum,
    ResearchRunStatusEnum,
    RunStatusEnum,
)
from agentos_chat.services.run_executor import _finalize_chat, _finalize_research


def _make_run(*, status=RunStatusEnum.RUNNING) -> MagicMock:
    run = MagicMock(spec=AgentRun)
    run.id = uuid.uuid4()
    run.status = status
    run.assistant_message_id = uuid.uuid4()
    run.session_id = uuid.uuid4()
    return run


def _mock_bus() -> MagicMock:
    bus = MagicMock()
    bus.publish = AsyncMock()
    bus.close = AsyncMock()
    return bus


@pytest.mark.asyncio
async def test_finalize_chat_stopped():
    db = AsyncMock()
    repo = AsyncMock()
    projection = AsyncMock()
    run = _make_run()

    with patch("agentos_chat.services.run_executor.run_event_bus", _mock_bus()), \
         patch("agentos_chat.services.run_executor.trace_stream_complete"):
        await _finalize_chat(
            db, repo, projection, run, run.assistant_message_id,
            RunStatusEnum.STOPPED, MessageStatusEnum.STOPPED,
        )
        repo.update_run_status.assert_awaited_once_with(run, RunStatusEnum.STOPPED)
        projection.finalize_chat_assistant.assert_awaited_once_with(
            run.assistant_message_id, status=MessageStatusEnum.STOPPED
        )
        db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_finalize_chat_failed_with_error():
    db = AsyncMock()
    repo = AsyncMock()
    projection = AsyncMock()
    run = _make_run()

    bus = _mock_bus()
    with patch("agentos_chat.services.run_executor.run_event_bus", bus), \
         patch("agentos_chat.services.run_executor.trace_stream_complete"):
        await _finalize_chat(
            db, repo, projection, run, run.assistant_message_id,
            RunStatusEnum.FAILED, MessageStatusEnum.FAILED,
            error=("timeout", "Took too long."),
        )
        repo.update_run_status.assert_awaited_once()
        db.commit.assert_awaited()
        assert bus.publish.await_count >= 2


@pytest.mark.asyncio
async def test_finalize_research_failed():
    db = AsyncMock()
    repo = AsyncMock()
    run_id = uuid.uuid4()

    bus = _mock_bus()
    with patch("agentos_chat.services.run_executor.run_event_bus", bus), \
         patch("agentos_chat.services.run_executor.trace_stream_complete"):
        await _finalize_research(
            db, repo, run_id, "agent_error", "Something broke.",
        )
        repo.update_run_status.assert_awaited_once_with(
            run_id, ResearchRunStatusEnum.FAILED,
            error_code="agent_error",
            error_message="Something broke.",
        )
        db.commit.assert_awaited()
        assert bus.publish.await_count >= 2
