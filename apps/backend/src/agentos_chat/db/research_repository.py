import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agentos_chat.db.models import (
    ArticleStatusEnum,
    ChangeSourceEnum,
    ResearchAgentRun,
    ResearchArticle,
    ResearchArticleVersion,
    ResearchMessage,
    ResearchMessageRoleEnum,
    ResearchMessageStatusEnum,
    ResearchRunStatusEnum,
    ResearchSession,
)

H1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)


class ResearchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_identity_id: uuid.UUID,
        idea: str,
    ) -> ResearchSession:
        title = idea[:60].strip()
        session = ResearchSession(
            user_identity_id=user_identity_id,
            idea=idea,
            title=title,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    def _owner_filter(self, user_identity_id: uuid.UUID) -> Select[tuple[ResearchSession]]:
        return select(ResearchSession).where(
            ResearchSession.user_identity_id == user_identity_id
        )

    async def get_session_for_owner(
        self,
        session_id: uuid.UUID,
        user_identity_id: uuid.UUID,
    ) -> ResearchSession | None:
        stmt = (
            self._owner_filter(user_identity_id)
            .where(ResearchSession.id == session_id)
            .options(
                selectinload(ResearchSession.article).selectinload(ResearchArticle.versions),
                selectinload(ResearchSession.runs),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions_paginated(
        self,
        user_identity_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[ResearchSession], int]:
        count_stmt = (
            select(func.count())
            .select_from(ResearchSession)
            .where(ResearchSession.user_identity_id == user_identity_id)
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            self._owner_filter(user_identity_id)
            .options(
                selectinload(ResearchSession.article).selectinload(ResearchArticle.versions),
                selectinload(ResearchSession.runs),
            )
            .order_by(ResearchSession.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())
        return sessions, total

    async def create_message(
        self,
        session_id: uuid.UUID,
        role: ResearchMessageRoleEnum,
        content: str,
        reasoning_content: str | None = None,
        status: ResearchMessageStatusEnum = ResearchMessageStatusEnum.COMPLETE,
    ) -> ResearchMessage:
        count_stmt = (
            select(func.count())
            .select_from(ResearchMessage)
            .where(ResearchMessage.session_id == session_id)
        )
        count_result = await self.db.execute(count_stmt)
        seq = count_result.scalar_one()

        msg = ResearchMessage(
            session_id=session_id,
            role=role,
            content=content,
            reasoning_content=reasoning_content,
            status=status,
            sequence_index=seq,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def list_messages(self, session_id: uuid.UUID) -> list[ResearchMessage]:
        stmt = (
            select(ResearchMessage)
            .where(ResearchMessage.session_id == session_id)
            .order_by(ResearchMessage.sequence_index)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_article(self, session_id: uuid.UUID) -> ResearchArticle:
        article = ResearchArticle(session_id=session_id, current_version=0)
        self.db.add(article)
        await self.db.flush()
        return article

    async def get_article_for_owner(
        self,
        article_id: uuid.UUID,
        user_identity_id: uuid.UUID,
    ) -> ResearchArticle | None:
        stmt = (
            select(ResearchArticle)
            .join(ResearchSession, ResearchArticle.session_id == ResearchSession.id)
            .where(
                ResearchArticle.id == article_id,
                ResearchSession.user_identity_id == user_identity_id,
            )
            .options(selectinload(ResearchArticle.versions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_article_for_session(self, session_id: uuid.UUID) -> ResearchArticle | None:
        stmt = (
            select(ResearchArticle)
            .where(ResearchArticle.session_id == session_id)
            .options(selectinload(ResearchArticle.versions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_article_version(
        self,
        article_id: uuid.UUID,
        markdown_content: str,
        change_source: ChangeSourceEnum = ChangeSourceEnum.AGENT,
    ) -> ResearchArticleVersion:
        article_stmt = select(ResearchArticle).where(ResearchArticle.id == article_id)
        article_result = await self.db.execute(article_stmt)
        article = article_result.scalar_one()

        new_version = article.current_version + 1
        version = ResearchArticleVersion(
            article_id=article_id,
            version_number=new_version,
            markdown_content=markdown_content,
            status=ArticleStatusEnum.DRAFT,
            change_source=change_source,
        )
        self.db.add(version)

        article.current_version = new_version
        article.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return version

    async def get_latest_version(self, article_id: uuid.UUID) -> ResearchArticleVersion | None:
        stmt = (
            select(ResearchArticleVersion)
            .where(ResearchArticleVersion.article_id == article_id)
            .order_by(ResearchArticleVersion.version_number.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_version_status(
        self,
        version_id: uuid.UUID,
        status: ArticleStatusEnum,
    ) -> None:
        stmt = (
            update(ResearchArticleVersion)
            .where(ResearchArticleVersion.id == version_id)
            .values(status=status)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def create_agent_run(
        self,
        session_id: uuid.UUID,
        user_message_id: uuid.UUID,
    ) -> ResearchAgentRun:
        run = ResearchAgentRun(
            session_id=session_id,
            user_message_id=user_message_id,
            status=ResearchRunStatusEnum.QUEUED,
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def get_run_for_owner(
        self,
        run_id: uuid.UUID,
        user_identity_id: uuid.UUID,
    ) -> ResearchAgentRun | None:
        stmt = (
            select(ResearchAgentRun)
            .join(ResearchSession, ResearchAgentRun.session_id == ResearchSession.id)
            .where(
                ResearchAgentRun.id == run_id,
                ResearchSession.user_identity_id == user_identity_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_run_status(
        self,
        run_id: uuid.UUID,
        status: ResearchRunStatusEnum,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        values: dict = {"status": status}
        if status == ResearchRunStatusEnum.RUNNING:
            values["started_at"] = datetime.now(timezone.utc)
        if status in (
            ResearchRunStatusEnum.COMPLETED,
            ResearchRunStatusEnum.FAILED,
            ResearchRunStatusEnum.STOPPED,
        ):
            values["completed_at"] = datetime.now(timezone.utc)
        if error_code:
            values["error_code"] = error_code
        if error_message:
            values["error_message"] = error_message

        stmt = update(ResearchAgentRun).where(ResearchAgentRun.id == run_id).values(**values)
        await self.db.execute(stmt)
        await self.db.flush()

    async def has_active_run(self, session_id: uuid.UUID) -> bool:
        stmt = (
            select(func.count())
            .select_from(ResearchAgentRun)
            .where(
                ResearchAgentRun.session_id == session_id,
                ResearchAgentRun.status.in_([
                    ResearchRunStatusEnum.QUEUED,
                    ResearchRunStatusEnum.RUNNING,
                ]),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() > 0

    async def update_session_title(self, session_id: uuid.UUID, title: str) -> None:
        stmt = (
            update(ResearchSession)
            .where(ResearchSession.id == session_id)
            .values(title=title, updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.flush()

    @staticmethod
    def extract_h1(markdown: str) -> str | None:
        match = H1_PATTERN.search(markdown)
        return match.group(1).strip() if match else None
