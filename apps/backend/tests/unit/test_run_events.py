"""Unit tests for RunEventBus — covers late reconnect fix and cancel flags."""

import asyncio

import pytest

from agentos_chat.services.run_events import RunEventBus, RunEvent
from uuid import uuid4


@pytest.fixture
def bus() -> RunEventBus:
    return RunEventBus()


class TestRunEventBusBasic:
    @pytest.mark.asyncio
    async def test_create_and_publish(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        await bus.publish(run_id, "token", {"text": "hello"})
        assert len(bus.history[run_id]) == 1
        assert bus.history[run_id][0].event == "token"

    @pytest.mark.asyncio
    async def test_iter_events_yields_published_items(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        await bus.publish(run_id, "thinking", {"message": "working..."})
        await bus.publish(run_id, "done", {"status": "completed"})
        await bus.close(run_id)

        events: list[RunEvent] = []
        async for item in bus.iter_events(run_id):
            if item is None:
                break
            events.append(item)

        assert len(events) == 2
        assert events[0].event == "thinking"
        assert events[1].event == "done"

    @pytest.mark.asyncio
    async def test_close_terminates_stream(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)

        async def consume():
            items = []
            async for item in bus.iter_events(run_id):
                if item is None:
                    break
                items.append(item)
            return items

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await bus.close(run_id)
        items = await asyncio.wait_for(task, timeout=2.0)
        assert items == []


class TestLateReconnect:
    """Verify that connecting to a closed run replays history then terminates."""

    @pytest.mark.asyncio
    async def test_late_connect_does_not_hang(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        await bus.publish(run_id, "thinking", {"message": "start"})
        await bus.publish(run_id, "done", {"status": "completed"})
        await bus.close(run_id)

        assert run_id in bus.closed

        events: list[RunEvent] = []
        async for item in bus.iter_events(run_id):
            if item is None:
                break
            events.append(item)

        assert len(events) == 2
        assert events[0].event == "thinking"
        assert events[1].event == "done"

    @pytest.mark.asyncio
    async def test_late_connect_with_timeout_does_not_hang(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        await bus.publish(run_id, "token", {"text": "hi"})
        await bus.close(run_id)

        async def consume():
            items = []
            async for item in bus.iter_events(run_id):
                if item is None:
                    break
                items.append(item)
            return items

        result = await asyncio.wait_for(consume(), timeout=2.0)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_unknown_run_creates_empty_stream(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)

        async def consume():
            items = []
            async for item in bus.iter_events(run_id):
                if item is None:
                    break
                items.append(item)
            return items

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await bus.close(run_id)
        result = await asyncio.wait_for(task, timeout=2.0)
        assert result == []


class TestCancelFlags:
    def test_cancel_flag_default_false(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        assert bus.is_cancelled(run_id) is False

    def test_request_cancel_sets_flag(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        bus.request_cancel(run_id)
        assert bus.is_cancelled(run_id) is True

    def test_close_clears_cancel_flag(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        bus.request_cancel(run_id)
        asyncio.get_event_loop().run_until_complete(bus.close(run_id))
        assert bus.is_cancelled(run_id) is False

    def test_create_clears_closed_state(self, bus: RunEventBus):
        run_id = uuid4()
        bus.create(run_id)
        asyncio.get_event_loop().run_until_complete(bus.close(run_id))
        assert run_id in bus.closed
        bus.create(run_id)
        assert run_id not in bus.closed
