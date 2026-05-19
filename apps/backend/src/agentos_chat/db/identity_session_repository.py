import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.models import ChatSession, SessionStatusEnum
from agentos_chat.db.repositories import OwnerFilterMixin, get_or_create_identity


class IdentitySessionRepository(OwnerFilterMixin):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ensure_identity(self, auth_subject: str) -> uuid.UUID:
        identity = await get_or_create_identity(self.db, auth_subject)
        return identity.id

    async def list_sessions(self, user_identity_id: uuid.UUID) -> list[ChatSession]:
        result = await self.db.execute(self.sessions_for_owner(user_identity_id))
        return list(result.scalars().all())

    async def get_session(
        self, session_id: uuid.UUID, user_identity_id: uuid.UUID
    ) -> ChatSession | None:
        result = await self.db.execute(self.session_for_owner(session_id, user_identity_id))
        return result.scalar_one_or_none()

    async def create_session(
        self, user_identity_id: uuid.UUID, title: str = "New chat"
    ) -> ChatSession:
        await self.db.execute(
            update(ChatSession)
            .where(
                ChatSession.user_identity_id == user_identity_id,
                ChatSession.status == SessionStatusEnum.ACTIVE,
            )
            .values(status=SessionStatusEnum.INACTIVE)
        )
        session = ChatSession(
            user_identity_id=user_identity_id,
            title=title,
            status=SessionStatusEnum.ACTIVE,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_active_session(self, user_identity_id: uuid.UUID) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession)
            .where(
                ChatSession.user_identity_id == user_identity_id,
                ChatSession.status == SessionStatusEnum.ACTIVE,
            )
            .order_by(ChatSession.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_session(self, session_id: uuid.UUID, user_identity_id: uuid.UUID) -> bool:
        session = await self.get_session(session_id, user_identity_id)
        if not session:
            return False
        session.status = SessionStatusEnum.DELETED
        session.deleted_at = datetime.now(UTC)
        await self.db.flush()
        return True
