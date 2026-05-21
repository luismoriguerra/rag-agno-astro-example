from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ArticleStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ResearchMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ResearchMessageStatus(StrEnum):
    COMPLETE = "complete"
    STREAMING = "streaming"
    STOPPED = "stopped"
    FAILED = "failed"


class ResearchRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class ChangeSource(StrEnum):
    AGENT = "agent"


class CreateResearchSessionRequest(BaseModel):
    idea: str = Field(min_length=1, max_length=10000)


class CreateResearchSessionResponse(BaseModel):
    session_id: UUID
    title: str
    status: ArticleStatus
    created_at: datetime
    run_id: UUID


class ResearchSessionSummary(BaseModel):
    id: UUID
    title: str
    idea: str
    status: ArticleStatus
    is_generating: bool
    current_version: int | None
    created_at: datetime
    updated_at: datetime


class ResearchSessionListResponse(BaseModel):
    sessions: list[ResearchSessionSummary]
    total: int
    page: int
    page_size: int


class ResearchMessageSchema(BaseModel):
    id: UUID
    role: ResearchMessageRole
    content: str
    reasoning_content: str | None = None
    status: ResearchMessageStatus
    sequence_index: int = Field(ge=0)
    created_at: datetime


class ArticleVersionSchema(BaseModel):
    id: UUID
    version_number: int
    markdown_content: str
    status: ArticleStatus
    change_source: ChangeSource
    created_at: datetime


class ArticleSchema(BaseModel):
    id: UUID
    current_version: int
    latest_version: ArticleVersionSchema | None = None


class ResearchSessionDetailResponse(BaseModel):
    session: ResearchSessionSummary
    article: ArticleSchema | None = None
    messages: list[ResearchMessageSchema]


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class SendMessageResponse(BaseModel):
    message_id: UUID
    run_id: UUID


class ResearchRunStatusResponse(BaseModel):
    run_id: UUID
    status: ResearchRunStatus


class UpdateArticleStatusRequest(BaseModel):
    status: ArticleStatus


class UpdateArticleStatusResponse(BaseModel):
    article_id: UUID
    version_number: int
    status: ArticleStatus


class RetryResponse(BaseModel):
    run_id: UUID
