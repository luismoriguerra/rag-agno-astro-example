import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.identity_session_repository import IdentitySessionRepository
from agentos_chat.db.message_run_repository import MessageRunRepository
from agentos_chat.db.models import (
    ChatMessage,
    ChatSession,
    MessageRoleEnum,
    MessageStatusEnum,
    SessionStatusEnum,
)
from agentos_chat.models.schemas import (
    ChatMessageSchema,
    ChatSessionDetailSchema,
    ChatSessionSchema,
    MessageRole,
    MessageStatus,
    SessionStatus,
)
from agentos_chat.services.logging import trace_session_restore


class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.sessions = IdentitySessionRepository(db)
        self.messages = MessageRunRepository(db)
        self.db = db

    async def list_sessions(self, auth_subject: str) -> list[ChatSessionSchema]:
        identity_id = await self.sessions.ensure_identity(auth_subject)
        rows = await self.sessions.list_sessions(identity_id)
        return [self._to_session_schema(s) for s in rows]

    async def create_session(self, auth_subject: str) -> ChatSessionSchema:
        identity_id = await self.sessions.ensure_identity(auth_subject)
        session = await self.sessions.create_session(identity_id)
        await self.db.commit()
        return self._to_session_schema(session)

    async def restore_session(
        self, auth_subject: str, session_id: uuid.UUID
    ) -> ChatSessionDetailSchema | None:
        identity_id = await self.sessions.ensure_identity(auth_subject)
        session = await self.sessions.get_session(session_id, identity_id)
        if not session:
            return None
        trace_session_restore(str(session_id), auth_subject)
        message_rows = await self.messages.list_messages(session_id)
        return self._to_detail(session, message_rows)

    async def restore_active_session(self, auth_subject: str) -> ChatSessionDetailSchema | None:
        identity_id = await self.sessions.ensure_identity(auth_subject)
        session = await self.sessions.get_active_session(identity_id)
        if not session:
            session = await self.sessions.create_session(identity_id)
            await self.db.commit()
            return self._to_detail(session, [])
        trace_session_restore(str(session.id), auth_subject)
        message_rows = await self.messages.list_messages(session.id)
        await self.db.commit()
        return self._to_detail(session, message_rows)

    async def delete_session(self, auth_subject: str, session_id: uuid.UUID) -> bool:
        identity_id = await self.sessions.ensure_identity(auth_subject)
        deleted = await self.sessions.delete_session(session_id, identity_id)
        if deleted:
            await self.db.commit()
        return deleted

    def _to_session_schema(self, session: ChatSession) -> ChatSessionSchema:
        status = (
            SessionStatus.ACTIVE
            if session.status == SessionStatusEnum.ACTIVE
            else SessionStatus.INACTIVE
        )
        return ChatSessionSchema(
            id=session.id,
            title=session.title,
            status=status,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    async def _sources_for_messages(self, message_rows: list[ChatMessage]) -> dict[uuid.UUID, list]:
        # Sources are attached to assistant messages via latest run — simplified: empty for restore
        return {}

    @staticmethod
    def _enum_value(value: str | SessionStatusEnum | MessageRoleEnum | MessageStatusEnum) -> str:
        return value.value if hasattr(value, "value") else str(value)

    def _to_detail(
        self, session: ChatSession, message_rows: list[ChatMessage]
    ) -> ChatSessionDetailSchema:
        return ChatSessionDetailSchema(
            **self._to_session_schema(session).model_dump(),
            messages=[
                ChatMessageSchema(
                    id=m.id,
                    role=MessageRole(self._enum_value(m.role)),
                    content=m.content,
                    status=MessageStatus(self._enum_value(m.status)),
                    sequence_index=m.sequence_index,
                    created_at=m.created_at,
                    sources=[],
                )
                for m in message_rows
            ],
        )
