import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SessionStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class MessageRoleEnum(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM_STATUS = "system_status"


class MessageStatusEnum(str, enum.Enum):
    COMPLETE = "complete"
    STREAMING = "streaming"
    STOPPED = "stopped"
    FAILED = "failed"


class RunStatusEnum(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class UserIdentity(Base):
    __tablename__ = "user_identities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user_identity")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_sessions_user_status_updated", "user_identity_id", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_identity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_identities.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), default="New chat")
    status: Mapped[SessionStatusEnum] = mapped_column(
        String(20), default=SessionStatusEnum.ACTIVE, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user_identity: Mapped[UserIdentity] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")
    runs: Mapped[list["AgentRun"]] = relationship(back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_session_seq", "session_id", "sequence_index"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[MessageRoleEnum] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[MessageStatusEnum] = mapped_column(
        String(20), default=MessageStatusEnum.COMPLETE, nullable=False
    )
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (Index("ix_agent_runs_session_status", "session_id", "status", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    user_message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False
    )
    assistant_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_messages.id")
    )
    status: Mapped[RunStatusEnum] = mapped_column(
        String(20), default=RunStatusEnum.QUEUED, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)

    session: Mapped[ChatSession] = relationship(back_populates="runs")
    search_results: Mapped[list["SearchResult"]] = relationship(back_populates="agent_run")


class SearchResult(Base):
    __tablename__ = "search_results"
    __table_args__ = (Index("ix_search_results_run_rank", "agent_run_id", "rank"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent_run: Mapped[AgentRun] = relationship(back_populates="search_results")


class WhatsAppSettings(Base):
    __tablename__ = "whatsapp_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    allowed_phone_numbers: Mapped[list["AllowedPhoneNumber"]] = relationship(
        back_populates="settings",
        cascade="all, delete-orphan",
    )


class AllowedPhoneNumber(Base):
    __tablename__ = "allowed_phone_numbers"
    __table_args__ = (Index("ix_allowed_phone_numbers_phone", "phone_number", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    settings_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("whatsapp_settings.id", ondelete="CASCADE"), nullable=False
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    settings: Mapped[WhatsAppSettings] = relationship(back_populates="allowed_phone_numbers")
