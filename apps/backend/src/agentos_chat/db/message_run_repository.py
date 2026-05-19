import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agentos_chat.db.models import (
    AgentRun,
    ChatMessage,
    MessageRoleEnum,
    MessageStatusEnum,
    RunStatusEnum,
    SearchResult,
)


class MessageRunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def next_sequence_index(self, session_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.coalesce(func.max(ChatMessage.sequence_index), -1)).where(
                ChatMessage.session_id == session_id
            )
        )
        return int(result.scalar_one()) + 1

    async def list_messages(self, session_id: uuid.UUID) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.sequence_index)
        )
        return list(result.scalars().all())

    async def create_user_message(
        self, session_id: uuid.UUID, content: str, sequence_index: int
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=MessageRoleEnum.USER,
            content=content,
            status=MessageStatusEnum.COMPLETE,
            sequence_index=sequence_index,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def create_assistant_message(
        self, session_id: uuid.UUID, sequence_index: int
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=MessageRoleEnum.ASSISTANT,
            content="",
            status=MessageStatusEnum.STREAMING,
            sequence_index=sequence_index,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def create_run(
        self, session_id: uuid.UUID, user_message_id: uuid.UUID, assistant_message_id: uuid.UUID
    ) -> AgentRun:
        run = AgentRun(
            session_id=session_id,
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            status=RunStatusEnum.QUEUED,
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def get_run(self, run_id: uuid.UUID) -> AgentRun | None:
        result = await self.db.execute(
            select(AgentRun)
            .options(selectinload(AgentRun.search_results))
            .where(AgentRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_run_for_owner(
        self, run_id: uuid.UUID, user_identity_id: uuid.UUID
    ) -> AgentRun | None:
        from agentos_chat.db.models import ChatSession, SessionStatusEnum

        result = await self.db.execute(
            select(AgentRun)
            .join(ChatSession, ChatSession.id == AgentRun.session_id)
            .where(
                AgentRun.id == run_id,
                ChatSession.user_identity_id == user_identity_id,
                ChatSession.status != SessionStatusEnum.DELETED,
            )
        )
        return result.scalar_one_or_none()

    async def update_run_status(
        self,
        run: AgentRun,
        status: RunStatusEnum,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        run.status = status
        if status == RunStatusEnum.RUNNING and run.started_at is None:
            run.started_at = datetime.now(UTC)
        if status in (
            RunStatusEnum.COMPLETED,
            RunStatusEnum.FAILED,
            RunStatusEnum.STOPPED,
        ):
            run.completed_at = datetime.now(UTC)
        if error_code:
            run.error_code = error_code
        if error_message:
            run.error_message = error_message
        await self.db.flush()

    async def append_assistant_content(self, message: ChatMessage, text: str) -> None:
        message.content += text
        await self.db.flush()

    async def finalize_assistant_message(
        self, message: ChatMessage, status: MessageStatusEnum
    ) -> None:
        message.status = status
        message.completed_at = datetime.now(UTC)
        await self.db.flush()

    async def add_search_results(
        self, run_id: uuid.UUID, sources: list[dict[str, str | int | None]]
    ) -> list[SearchResult]:
        rows: list[SearchResult] = []
        for item in sources:
            row = SearchResult(
                agent_run_id=run_id,
                title=str(item["title"]),
                url=str(item["url"]),
                snippet=item.get("snippet") if item.get("snippet") else None,
                rank=int(item["rank"]),
            )
            self.db.add(row)
            rows.append(row)
        await self.db.flush()
        return rows

    async def sources_for_run(self, run_id: uuid.UUID) -> list[SearchResult]:
        result = await self.db.execute(
            select(SearchResult)
            .where(SearchResult.agent_run_id == run_id)
            .order_by(SearchResult.rank)
        )
        return list(result.scalars().all())
