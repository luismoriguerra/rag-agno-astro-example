import asyncio
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.identity_session_repository import IdentitySessionRepository
from agentos_chat.db.message_run_repository import MessageRunRepository
from agentos_chat.db.models import RunStatusEnum
from agentos_chat.models.schemas import (
    ChatMessageSchema,
    CreateMessageResponse,
    MessageRole,
    MessageStatus,
    RunStatusSchema,
)
from agentos_chat.models.schemas import (
    RunStatusEnum as RunStatusSchemaEnum,
)
from agentos_chat.services.concurrency import ConcurrencyConflict, assert_can_start_run
from agentos_chat.services.logging import trace_run_stopped
from agentos_chat.services.run_events import run_event_bus
from agentos_chat.services.run_executor import get_run_executor


class AgentService:
    def __init__(self, db: AsyncSession) -> None:
        self.sessions = IdentitySessionRepository(db)
        self.messages = MessageRunRepository(db)
        self.db = db

    async def submit_message(
        self, auth_subject: str, session_id: uuid.UUID, content: str
    ) -> CreateMessageResponse | None:
        identity_id = await self.sessions.ensure_identity(auth_subject)
        session = await self.sessions.get_session(session_id, identity_id)
        if not session:
            return None

        try:
            await assert_can_start_run(
                self.db,
                user_identity_id=identity_id,
                session_id=session_id,
                workflow="chat",
            )
        except ConcurrencyConflict as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": exc.code, "message": exc.message},
            ) from exc

        seq = await self.messages.next_sequence_index(session_id)
        user_message = await self.messages.create_user_message(session_id, content, seq)
        assistant = await self.messages.create_assistant_message(session_id, seq + 1)
        run = await self.messages.create_run(session_id, user_message.id, assistant.id)
        await self.db.commit()

        run_event_bus.create(run.id)
        executor = get_run_executor()
        asyncio.create_task(
            executor.execute_chat_run(
                run_id=run.id,
                session_id=session_id,
                user_identity_id=identity_id,
                auth_subject=auth_subject,
                user_content=content,
            )
        )

        return CreateMessageResponse(
            message=ChatMessageSchema(
                id=user_message.id,
                role=MessageRole.USER,
                content=user_message.content,
                status=MessageStatus.COMPLETE,
                sequence_index=user_message.sequence_index,
                created_at=user_message.created_at,
            ),
            run=RunStatusSchema(id=run.id, status=RunStatusSchemaEnum.QUEUED),
        )

    async def stop_run(self, auth_subject: str, run_id: uuid.UUID) -> RunStatusSchema | None:
        identity_id = await self.sessions.ensure_identity(auth_subject)
        run = await self.messages.get_run_for_owner(run_id, identity_id)
        if not run:
            return None
        if run.status in (RunStatusEnum.COMPLETED, RunStatusEnum.FAILED, RunStatusEnum.STOPPED):
            return RunStatusSchema(id=run.id, status=RunStatusSchemaEnum(run.status.value))
        run_event_bus.request_cancel(run_id)
        await self.messages.update_run_status(run, RunStatusEnum.STOPPING)
        await self.db.commit()
        trace_run_stopped(str(run_id))
        return RunStatusSchema(id=run.id, status=RunStatusSchemaEnum.STOPPING)
