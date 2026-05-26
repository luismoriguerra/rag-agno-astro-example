"""Idempotent backfill of chat_agno_sessions from domain chat_messages.

Run once after deploy:
    cd apps/backend && python -m scripts.backfill_chat_agno_sessions
"""

from __future__ import annotations

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info(
        "Backfill script placeholder: Agno PostgresDb auto-provisions chat_agno_sessions. "
        "Existing sessions gain history on next message via add_history_to_context."
    )


if __name__ == "__main__":
    asyncio.run(main())
