import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.models import ChatSession, SessionStatusEnum, UserIdentity


class OwnerFilterMixin:
    """Owner-scoped query helpers."""

    @staticmethod
    def session_for_owner(
        session_id: uuid.UUID, user_identity_id: uuid.UUID
    ) -> Select[tuple[ChatSession]]:
        return select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_identity_id == user_identity_id,
            ChatSession.status != SessionStatusEnum.DELETED,
        )

    @staticmethod
    def sessions_for_owner(user_identity_id: uuid.UUID) -> Select[tuple[ChatSession]]:
        return (
            select(ChatSession)
            .where(
                ChatSession.user_identity_id == user_identity_id,
                ChatSession.status != SessionStatusEnum.DELETED,
            )
            .order_by(ChatSession.updated_at.desc())
        )


async def get_or_create_identity(
    db: AsyncSession, auth_subject: str, display_name: str | None = None
) -> UserIdentity:
    result = await db.execute(select(UserIdentity).where(UserIdentity.auth_subject == auth_subject))
    identity = result.scalar_one_or_none()
    if identity:
        return identity
    identity = UserIdentity(auth_subject=auth_subject, display_name=display_name)
    db.add(identity)
    await db.flush()
    return identity
