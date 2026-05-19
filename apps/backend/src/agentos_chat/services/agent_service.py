import asyncio
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.agents.search_agent import (
    build_search_agent,
    extract_sources_from_text,
    format_user_prompt,
    safe_thinking_payload,
)
from agentos_chat.db.identity_session_repository import IdentitySessionRepository
from agentos_chat.db.message_run_repository import MessageRunRepository
from agentos_chat.db.models import MessageRoleEnum, MessageStatusEnum, RunStatusEnum
from agentos_chat.db.session import get_session_factory
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
from agentos_chat.observability.langwatch import trace_agent_run
from agentos_chat.services.logging import (
    trace_agent_run_start,
    trace_run_failed,
    trace_run_stopped,
    trace_search_sources,
    trace_stream_complete,
)
from agentos_chat.services.run_events import run_event_bus
from agentos_chat.settings import get_settings


def _message_role(role: MessageRoleEnum | str) -> str:
    return role.value if hasattr(role, "value") else str(role)


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

        seq = await self.messages.next_sequence_index(session_id)
        user_message = await self.messages.create_user_message(session_id, content, seq)
        assistant = await self.messages.create_assistant_message(session_id, seq + 1)
        run = await self.messages.create_run(session_id, user_message.id, assistant.id)
        await self.db.commit()

        run_event_bus.create(run.id)
        asyncio.create_task(self._execute_run(auth_subject, run.id, session_id))

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

    async def _execute_run(
        self, auth_subject: str, run_id: uuid.UUID, session_id: uuid.UUID
    ) -> None:
        factory = get_session_factory()
        async with factory() as db:
            messages_repo = MessageRunRepository(db)
            sessions_repo = IdentitySessionRepository(db)
            run = await messages_repo.get_run(run_id)
            if not run or not run.assistant_message_id:
                return

            await sessions_repo.ensure_identity(auth_subject)
            history_rows = await messages_repo.list_messages(session_id)
            history = [
                (role, m.content)
                for m in history_rows
                if m.id != run.user_message_id
                and m.id != run.assistant_message_id
                and (role := _message_role(m.role)) in ("user", "assistant")
                and m.content
            ]

            await messages_repo.update_run_status(run, RunStatusEnum.RUNNING)
            await db.commit()
            trace_agent_run_start(str(run_id), str(session_id))

            await run_event_bus.publish(run_id, "thinking", safe_thinking_payload())

            settings = get_settings()
            try:
                user_msg = next(m for m in history_rows if m.id == run.user_message_id)
                prompt = format_user_prompt(history, user_msg.content)
                agent = build_search_agent()
                assistant_msg = next(m for m in history_rows if m.id == run.assistant_message_id)

                with trace_agent_run(run_id, session_id, auth_subject):
                    response = await asyncio.wait_for(
                        asyncio.to_thread(agent.run, prompt, stream=False),
                        timeout=settings.request_timeout_seconds,
                    )
                if run_event_bus.is_cancelled(run_id):
                    await self._finalize_cancelled(db, messages_repo, run, assistant_msg)
                    return

                text = ""
                if hasattr(response, "content") and response.content:
                    text = str(response.content)
                elif hasattr(response, "messages") and response.messages:
                    text = str(response.messages[-1].content)
                else:
                    text = str(response)

                if not text.strip():
                    text = (
                        "I could not find enough supporting information "
                        "from public web search to answer confidently."
                    )

                chunk_size = 24
                for i in range(0, len(text), chunk_size):
                    if run_event_bus.is_cancelled(run_id):
                        await self._finalize_cancelled(db, messages_repo, run, assistant_msg)
                        return
                    chunk = text[i : i + chunk_size]
                    await messages_repo.append_assistant_content(assistant_msg, chunk)
                    await db.commit()
                    await run_event_bus.publish(run_id, "token", {"text": chunk})
                    await asyncio.sleep(0.02)

                sources = extract_sources_from_text(text)
                if sources:
                    await messages_repo.add_search_results(run_id, sources)
                    trace_search_sources(str(run_id), len(sources))
                    for src in sources:
                        await run_event_bus.publish(run_id, "source", src)

                await messages_repo.update_run_status(run, RunStatusEnum.COMPLETED)
                await messages_repo.finalize_assistant_message(
                    assistant_msg, MessageStatusEnum.COMPLETE
                )
                await db.commit()
                await run_event_bus.publish(
                    run_id,
                    "done",
                    {"run_id": str(run_id), "status": "completed"},
                )
                trace_stream_complete(str(run_id), "completed")
            except TimeoutError:
                await self._finalize_failed(
                    db,
                    messages_repo,
                    run,
                    "timeout",
                    "The request took too long. Please try again.",
                )
            except Exception as exc:  # noqa: BLE001
                await self._finalize_failed(
                    db,
                    messages_repo,
                    run,
                    "agent_error",
                    "Something went wrong while generating a response. Please try again.",
                )
                trace_run_failed(str(run_id), "agent_error", str(exc))
            finally:
                await run_event_bus.close(run_id)

    async def _finalize_cancelled(
        self,
        db: AsyncSession,
        repo: MessageRunRepository,
        run: Any,
        assistant_msg: Any,
    ) -> None:
        await repo.update_run_status(run, RunStatusEnum.STOPPED)
        await repo.finalize_assistant_message(assistant_msg, MessageStatusEnum.STOPPED)
        await db.commit()
        await run_event_bus.publish(run.id, "done", {"run_id": str(run.id), "status": "stopped"})
        trace_stream_complete(str(run.id), "stopped")

    async def _finalize_failed(
        self,
        db: AsyncSession,
        repo: MessageRunRepository,
        run: Any,
        code: str,
        message: str,
    ) -> None:
        assistant_msg = None
        if run.assistant_message_id:
            rows = await repo.list_messages(run.session_id)
            assistant_msg = next((m for m in rows if m.id == run.assistant_message_id), None)
        await repo.update_run_status(
            run, RunStatusEnum.FAILED, error_code=code, error_message=message
        )
        if assistant_msg:
            await repo.finalize_assistant_message(assistant_msg, MessageStatusEnum.FAILED)
        await db.commit()
        await run_event_bus.publish(run.id, "error", {"code": code, "message": message})
        trace_stream_complete(str(run.id), "failed")
