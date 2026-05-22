import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agentos_chat.db.models import (
    ArticleStatusEnum,
    ChangeSourceEnum,
    ResearchAgentRun,
    ResearchArticle,
    ResearchArticleVersion,
    ResearchCost,
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
        return select(ResearchSession).where(ResearchSession.user_identity_id == user_identity_id)

    async def delete_session(
        self,
        session_id: uuid.UUID,
        user_identity_id: uuid.UUID,
    ) -> bool:
        session = await self.get_session_for_owner(session_id, user_identity_id)
        if not session:
            return False

        if await self.has_active_run(session_id):
            raise ValueError("run_in_progress")

        article = await self.get_article_for_session(session_id)
        if article:
            await self.db.execute(
                delete(ResearchArticleVersion).where(
                    ResearchArticleVersion.article_id == article.id
                )
            )

        await self.db.execute(delete(ResearchCost).where(ResearchCost.session_id == session_id))
        await self.db.execute(
            delete(ResearchAgentRun).where(ResearchAgentRun.session_id == session_id)
        )
        if article:
            await self.db.execute(
                delete(ResearchArticle).where(ResearchArticle.id == article.id)
            )
        await self.db.execute(
            delete(ResearchMessage).where(ResearchMessage.session_id == session_id)
        )
        await self.db.execute(
            delete(ResearchSession).where(ResearchSession.id == session_id)
        )
        await self.db.flush()
        return True

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

    def _latest_version_status_subquery(self):
        """Subquery that returns the status of the latest article version per session."""
        return (
            select(
                ResearchArticle.session_id,
                ResearchArticleVersion.status.label("latest_status"),
            )
            .join(
                ResearchArticleVersion,
                ResearchArticleVersion.article_id == ResearchArticle.id,
            )
            .where(
                ResearchArticleVersion.version_number == (
                    select(func.max(ResearchArticleVersion.version_number))
                    .where(ResearchArticleVersion.article_id == ResearchArticle.id)
                    .correlate(ResearchArticle)
                    .scalar_subquery()
                )
            )
            .subquery()
        )

    def _apply_status_filter(self, stmt, status: str | None):
        if status is None:
            return stmt
        sub = self._latest_version_status_subquery()
        stmt = stmt.outerjoin(sub, sub.c.session_id == ResearchSession.id)
        if status == ArticleStatusEnum.DRAFT.value:
            stmt = stmt.where(
                or_(sub.c.latest_status.is_(None), sub.c.latest_status == status)
            )
        else:
            stmt = stmt.where(sub.c.latest_status == status)
        return stmt

    async def list_sessions_paginated(
        self,
        user_identity_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
    ) -> tuple[list[ResearchSession], int]:
        count_stmt = (
            select(func.count())
            .select_from(ResearchSession)
            .where(ResearchSession.user_identity_id == user_identity_id)
        )
        count_stmt = self._apply_status_filter(count_stmt, status)
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
        stmt = self._apply_status_filter(stmt, status)
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
        article.updated_at = datetime.now(UTC)
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

    async def get_run(self, run_id: uuid.UUID) -> ResearchAgentRun | None:
        stmt = select(ResearchAgentRun).where(ResearchAgentRun.id == run_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_message_by_id(self, message_id: uuid.UUID) -> ResearchMessage | None:
        stmt = select(ResearchMessage).where(ResearchMessage.id == message_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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

    async def update_run_assistant_message(
        self, run_id: uuid.UUID, assistant_message_id: uuid.UUID
    ) -> None:
        stmt = (
            update(ResearchAgentRun)
            .where(ResearchAgentRun.id == run_id)
            .values(assistant_message_id=assistant_message_id)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def update_run_status(
        self,
        run_id: uuid.UUID,
        status: ResearchRunStatusEnum,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        values: dict = {"status": status}
        if status == ResearchRunStatusEnum.RUNNING:
            values["started_at"] = datetime.now(UTC)
        if status in (
            ResearchRunStatusEnum.COMPLETED,
            ResearchRunStatusEnum.FAILED,
            ResearchRunStatusEnum.STOPPED,
        ):
            values["completed_at"] = datetime.now(UTC)
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
                ResearchAgentRun.status.in_(
                    [
                        ResearchRunStatusEnum.QUEUED,
                        ResearchRunStatusEnum.RUNNING,
                    ]
                ),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() > 0

    async def get_active_run_id(self, session_id: uuid.UUID) -> uuid.UUID | None:
        stmt = (
            select(ResearchAgentRun.id)
            .where(
                ResearchAgentRun.session_id == session_id,
                ResearchAgentRun.status.in_(
                    [
                        ResearchRunStatusEnum.QUEUED,
                        ResearchRunStatusEnum.RUNNING,
                    ]
                ),
            )
            .order_by(ResearchAgentRun.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_session_title(self, session_id: uuid.UUID, title: str) -> None:
        stmt = (
            update(ResearchSession)
            .where(ResearchSession.id == session_id)
            .values(title=title, updated_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def create_cost_record(
        self,
        session_id: uuid.UUID,
        run_id: uuid.UUID,
        model: str,
        agent_name: str,
        input_tokens: int,
        output_tokens: int,
        reasoning_tokens: int,
        total_tokens: int,
        estimated_cost_usd: float = 0.0,
    ) -> ResearchCost:
        cost = ResearchCost(
            session_id=session_id,
            run_id=run_id,
            model=model,
            agent_name=agent_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
        self.db.add(cost)
        await self.db.flush()
        return cost

    async def get_session_total_cost(self, session_id: uuid.UUID) -> dict:
        stmt = select(
            func.sum(ResearchCost.input_tokens).label("input_tokens"),
            func.sum(ResearchCost.output_tokens).label("output_tokens"),
            func.sum(ResearchCost.reasoning_tokens).label("reasoning_tokens"),
            func.sum(ResearchCost.total_tokens).label("total_tokens"),
            func.sum(ResearchCost.estimated_cost_usd).label("estimated_cost_usd"),
        ).where(ResearchCost.session_id == session_id)
        result = await self.db.execute(stmt)
        row = result.one()
        return {
            "input_tokens": row.input_tokens or 0,
            "output_tokens": row.output_tokens or 0,
            "reasoning_tokens": row.reasoning_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "estimated_cost_usd": round(row.estimated_cost_usd or 0.0, 6),
        }

    @staticmethod
    def extract_h1(markdown: str) -> str | None:
        match = H1_PATTERN.search(markdown)
        return match.group(1).strip() if match else None
