import asyncio
from collections.abc import Awaitable, Callable

PROCESSING_ACK = "processing..."


class WhatsAppMessageQueue:
    """Per-phone sequential message processing with processing acknowledgment."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._busy: dict[str, bool] = {}

    def _lock_for(self, phone: str) -> asyncio.Lock:
        if phone not in self._locks:
            self._locks[phone] = asyncio.Lock()
        return self._locks[phone]

    async def enqueue(
        self,
        phone: str,
        handler: Callable[[], Awaitable[None]],
        *,
        on_queued: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        lock = self._lock_for(phone)
        if lock.locked() and on_queued is not None:
            await on_queued()

        async with lock:
            await handler()
