"""Project agent run state into domain tables for API restore."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.agents.research_agent import ResearchResult
from agentos_chat.db.message_run_repository import MessageRunRepository
from agentos_chat.db.models import ChatMessage, MessageStatusEnum, ResearchMessageRoleEnum
from agentos_chat.db.research_repository import ResearchRepository


class RunProjection:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.chat = MessageRunRepository(db)
        self.research = ResearchRepository(db)
        self._assistant_cache: dict[uuid.UUID, ChatMessage] = {}

    async def get_assistant_message(
        self, assistant_message_id: uuid.UUID
    ) -> ChatMessage | None:
        cached = self._assistant_cache.get(assistant_message_id)
        if cached is not None:
            return cached
        msg = await self.chat.get_message_by_id(assistant_message_id)
        if msg:
            self._assistant_cache[assistant_message_id] = msg
        return msg

    async def append_chat_assistant_text(
        self, assistant_message_id: uuid.UUID, text: str
    ) -> None:
        assistant = await self.get_assistant_message(assistant_message_id)
        if assistant:
            await self.chat.append_assistant_content(assistant, text)

    async def finalize_chat_assistant(
        self,
        assistant_message_id: uuid.UUID,
        *,
        status: MessageStatusEnum,
    ) -> None:
        assistant = await self.get_assistant_message(assistant_message_id)
        if assistant:
            await self.chat.finalize_assistant_message(assistant, status)

    async def persist_chat_sources(
        self, run_id: uuid.UUID, sources: list[dict[str, str | int | None]]
    ) -> None:
        if sources:
            await self.chat.add_search_results(run_id, sources)

    async def persist_research_costs(
        self,
        session_id: uuid.UUID,
        run_id: uuid.UUID,
        cost_records: list[dict[str, Any]],
    ) -> int:
        total = 0
        for record in cost_records:
            await self.research.create_cost_record(
                session_id=session_id,
                run_id=run_id,
                model=str(record.get("model") or ""),
                agent_name=str(record.get("agent_name") or ""),
                input_tokens=int(record.get("input_tokens") or 0),
                output_tokens=int(record.get("output_tokens") or 0),
                reasoning_tokens=int(record.get("reasoning_tokens") or 0),
                total_tokens=int(record.get("total_tokens") or 0),
            )
            total += int(record.get("total_tokens") or 0)
        return total

    async def persist_chat_costs(
        self, run_id: uuid.UUID, cost_records: list[dict[str, Any]]
    ) -> None:
        for record in cost_records:
            await self.chat.add_cost_record(run_id, record)

    async def finalize_research_result(
        self,
        *,
        session_id: uuid.UUID,
        run_id: uuid.UUID,
        result: ResearchResult,
        reasoning_content: str | None,
        fallback_title: str,
    ) -> tuple[int, str, str]:
        """Persist research message and optional article; return version, title, chat."""
        assistant_msg = await self.research.create_message(
            session_id,
            ResearchMessageRoleEnum.ASSISTANT,
            result.chat_response,
            reasoning_content=reasoning_content,
        )
        await self.research.update_run_assistant_message(run_id, assistant_msg.id)

        version_number = 0
        title = fallback_title
        if result.article_markdown:
            article = await self.research.get_article_for_session(session_id)
            if not article:
                article = await self.research.create_article(session_id)
            version = await self.research.create_article_version(
                article.id, result.article_markdown
            )
            version_number = version.version_number
            title = (
                result.article_title
                or ResearchRepository.extract_h1(result.article_markdown)
                or fallback_title
            )
            await self.research.update_session_title(session_id, title)

        return version_number, title, result.chat_response
