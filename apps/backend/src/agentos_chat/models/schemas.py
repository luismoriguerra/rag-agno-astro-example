from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM_STATUS = "system_status"


class MessageStatus(StrEnum):
    COMPLETE = "complete"
    STREAMING = "streaming"
    STOPPED = "stopped"
    FAILED = "failed"


class RunStatusEnum(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class HealthResponse(BaseModel):
    status: str = "healthy"


class SearchResultSchema(BaseModel):
    title: str
    url: str
    snippet: str | None = None
    rank: int = Field(ge=1)


class ChatMessageSchema(BaseModel):
    id: UUID
    role: MessageRole
    content: str
    status: MessageStatus
    sequence_index: int = Field(ge=0)
    created_at: datetime
    sources: list[SearchResultSchema] = Field(default_factory=list)


class ChatSessionSchema(BaseModel):
    id: UUID
    title: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime


class ChatSessionDetailSchema(ChatSessionSchema):
    messages: list[ChatMessageSchema]


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionSchema]


class CreateMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class RunStatusSchema(BaseModel):
    id: UUID
    status: RunStatusEnum


class CreateMessageResponse(BaseModel):
    message: ChatMessageSchema
    run: RunStatusSchema


class ErrorResponse(BaseModel):
    code: str
    message: str


class AllowedPhoneNumberSchema(BaseModel):
    phone_number: str
    created_at: datetime


class WhatsAppSettingsSchema(BaseModel):
    enabled: bool
    allowed_phone_numbers: list[AllowedPhoneNumberSchema]


class WhatsAppSettingsUpdateRequest(BaseModel):
    enabled: bool


class WhatsAppAllowlistAddRequest(BaseModel):
    phone_number: str = Field(min_length=2, max_length=20)
