"""In-process SSE event bus for agent runs (single-instance local/dev)."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class RunEvent:
    event: str
    data: dict[str, Any]


@dataclass
class RunEventBus:
    queues: dict[UUID, asyncio.Queue[RunEvent | None]] = field(default_factory=dict)
    history: dict[UUID, list[RunEvent]] = field(default_factory=dict)
    cancel_flags: dict[UUID, bool] = field(default_factory=dict)
    closed: set[UUID] = field(default_factory=set)

    def create(self, run_id: UUID) -> asyncio.Queue[RunEvent | None]:
        queue: asyncio.Queue[RunEvent | None] = asyncio.Queue()
        self.queues[run_id] = queue
        self.history[run_id] = []
        self.cancel_flags[run_id] = False
        self.closed.discard(run_id)
        return queue

    def get_queue(self, run_id: UUID) -> asyncio.Queue[RunEvent | None] | None:
        return self.queues.get(run_id)

    def request_cancel(self, run_id: UUID) -> None:
        self.cancel_flags[run_id] = True

    def is_cancelled(self, run_id: UUID) -> bool:
        return self.cancel_flags.get(run_id, False)

    async def publish(self, run_id: UUID, event: str, data: dict[str, Any]) -> None:
        item = RunEvent(event=event, data=data)
        self.history.setdefault(run_id, []).append(item)
        queue = self.queues.get(run_id)
        if queue:
            await queue.put(item)

    async def iter_events(self, run_id: UUID) -> AsyncIterator[RunEvent | None]:
        already_closed = run_id in self.closed

        queue = self.queues.get(run_id)
        if queue is None and not already_closed:
            queue = asyncio.Queue()
            self.queues[run_id] = queue
            self.history.setdefault(run_id, [])
            self.cancel_flags.setdefault(run_id, False)

        for item in list(self.history.get(run_id, [])):
            yield item

        if already_closed:
            yield None
            return

        if queue:
            while True:
                item = await queue.get()
                yield item
                if item is None:
                    break

    async def close(self, run_id: UUID) -> None:
        queue = self.queues.get(run_id)
        if queue:
            await queue.put(None)
        self.queues.pop(run_id, None)
        self.cancel_flags.pop(run_id, None)
        self.closed.add(run_id)


run_event_bus = RunEventBus()
