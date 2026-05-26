"""Shared async agent run execution pipeline.

Delegates to ChatRunHandler and ResearchRunHandler for workflow-specific logic.
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from typing import Any

from agno.agent import Agent
from agno.team import Team
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.agents.research_agent import (
    ResearchResult,
    build_research_context_prompt,
)
from agentos_chat.db.message_run_repository import MessageRunRepository
from agentos_chat.db.models import (
    AgentRun,
    MessageStatusEnum,
    ResearchRunStatusEnum,
    RunStatusEnum,
)
from agentos_chat.db.research_repository import ResearchRepository
from agentos_chat.db.session import get_session_factory
from agentos_chat.observability.langwatch import trace_agent_run
from agentos_chat.services.event_mapper import (
    MODEL_COMPLETED_TYPES,
    RUN_COMPLETED_TYPES,
    TOOL_COMPLETED_TYPES,
    ResearchPhaseTracker,
    extract_all_tavily_sources,
    map_chat_event,
    map_model_cost,
    map_research_event,
)
from agentos_chat.services.logging import (
    trace_agent_run_start,
    trace_run_failed,
    trace_search_sources,
    trace_stream_complete,
)
from agentos_chat.services.projection import RunProjection
from agentos_chat.services.run_events import run_event_bus
from agentos_chat.settings import Settings

logger = logging.getLogger(__name__)


class ChatRunHandler:
    def __init__(self, agent: Agent, settings: Settings) -> None:
        self.agent = agent
        self.settings = settings

    async def execute(
        self,
        *,
        run_id: uuid.UUID,
        session_id: uuid.UUID,
        user_identity_id: uuid.UUID,
        auth_subject: str,
        user_content: str,
    ) -> None:
        try:
            factory = get_session_factory()
            async with factory() as db:
                repo = MessageRunRepository(db)
                projection = RunProjection(db)
                run = await repo.get_run(run_id)
                if not run or not run.assistant_message_id:
                    return

                aid = run.assistant_message_id
                await repo.update_run_status(run, RunStatusEnum.RUNNING)
                await db.commit()
                trace_agent_run_start(str(run_id), str(session_id))

                accumulated = ""
                sources: list[dict[str, Any]] = []
                cost_records: list[dict[str, Any]] = []

                async def _stream() -> None:
                    nonlocal accumulated
                    with trace_agent_run(run_id, session_id, auth_subject):
                        async for event in self.agent.arun(
                            user_content,
                            stream=True,
                            stream_events=True,
                            session_id=str(session_id),
                            user_id=str(user_identity_id),
                            add_history_to_context=True,
                        ):
                            if run_event_bus.is_cancelled(run_id):
                                break
                            if isinstance(event, MODEL_COMPLETED_TYPES):
                                cost_records.append(map_model_cost(event))
                                continue
                            if isinstance(event, RUN_COMPLETED_TYPES):
                                content = getattr(event, "content", None)
                                if content and not accumulated:
                                    accumulated = str(content)
                                continue
                            for sse_name, payload in map_chat_event(event):
                                if sse_name == "token":
                                    chunk = str(payload.get("text", ""))
                                    accumulated += chunk
                                    await projection.append_chat_assistant_text(aid, chunk)
                                elif sse_name == "source":
                                    sources.append(payload)
                                await run_event_bus.publish(run_id, sse_name, payload)
                            await db.commit()

                try:
                    await asyncio.wait_for(
                        _stream(), timeout=self.settings.request_timeout_seconds
                    )
                except TimeoutError:
                    await _finalize_chat(
                        db, repo, projection, run, aid,
                        RunStatusEnum.FAILED, MessageStatusEnum.FAILED,
                        error=("timeout", "The request took too long. Please try again."),
                    )
                    return
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Chat run %s failed", run_id)
                    await _finalize_chat(
                        db, repo, projection, run, aid,
                        RunStatusEnum.FAILED, MessageStatusEnum.FAILED,
                        error=("agent_error", "Something went wrong. Please try again."),
                    )
                    trace_run_failed(str(run_id), "agent_error", str(exc))
                    return

                if run_event_bus.is_cancelled(run_id):
                    await _finalize_chat(
                        db, repo, projection, run, aid,
                        RunStatusEnum.STOPPED, MessageStatusEnum.STOPPED,
                    )
                    return

                if not accumulated.strip():
                    accumulated = (
                        "I could not find enough supporting information "
                        "from public web search to answer confidently."
                    )
                    await projection.append_chat_assistant_text(aid, accumulated)
                    await run_event_bus.publish(run_id, "token", {"text": accumulated})

                if sources:
                    await projection.persist_chat_sources(run_id, sources)
                    trace_search_sources(str(run_id), len(sources))

                await repo.update_run_status(run, RunStatusEnum.COMPLETED)
                await projection.finalize_chat_assistant(
                    aid, status=MessageStatusEnum.COMPLETE
                )
                await db.commit()
                await run_event_bus.publish(
                    run_id, "done", {"run_id": str(run_id), "status": "completed"}
                )
                trace_stream_complete(str(run_id), "completed")
        finally:
            await run_event_bus.close(run_id)


class ResearchRunHandler:
    def __init__(self, team: Team, settings: Settings) -> None:
        self.team = team
        self.settings = settings

    async def execute(
        self,
        *,
        run_id: uuid.UUID,
        session_id: uuid.UUID,
        user_identity_id: uuid.UUID,
    ) -> None:
        try:
            factory = get_session_factory()
            async with factory() as db:
                repo = ResearchRepository(db)
                projection = RunProjection(db)

                session = await repo.get_session_for_owner(session_id, user_identity_id)
                if not session:
                    logger.error("Research session %s not found", session_id)
                    return

                current_article: str | None = None
                article = await repo.get_article_for_session(session_id)
                if article:
                    latest = await repo.get_latest_version(article.id)
                    if latest:
                        current_article = latest.markdown_content

                user_message: str | None = None
                run = await repo.get_run(run_id)
                if run:
                    trigger = await repo.get_message_by_id(run.user_message_id)
                    if trigger:
                        user_message = trigger.content

                prompt = build_research_context_prompt(
                    session.idea, current_article, user_message
                )
                fallback_title = session.idea[:60].strip()

                await repo.update_run_status(run_id, ResearchRunStatusEnum.RUNNING)
                await db.commit()
                trace_agent_run_start(str(run_id), str(session_id))

                tracker = ResearchPhaseTracker()
                cost_records: list[dict[str, Any]] = []
                coordinator_parts: list[str] = []
                writer_article = ""

                async def _stream() -> None:
                    nonlocal writer_article
                    with trace_agent_run(run_id, session_id, str(user_identity_id)):
                        async for event in self.team.arun(
                            prompt,
                            stream=True,
                            stream_events=True,
                            session_id=str(session_id),
                            user_id=str(user_identity_id),
                        ):
                            if run_event_bus.is_cancelled(run_id):
                                break
                            if isinstance(event, MODEL_COMPLETED_TYPES):
                                cost_records.append(map_model_cost(event))
                                continue
                            if isinstance(event, RUN_COMPLETED_TYPES):
                                content = getattr(event, "content", None)
                                agent_name = getattr(event, "agent_name", None)
                                if agent_name == "Article Writer" and content:
                                    writer_article = str(content)
                                if content:
                                    coordinator_parts.append(str(content))
                                continue
                            if isinstance(event, TOOL_COMPLETED_TYPES):
                                for src in extract_all_tavily_sources(event):
                                    await run_event_bus.publish(run_id, "source", src)
                            for sse_name, payload in map_research_event(event, tracker):
                                await run_event_bus.publish(run_id, sse_name, payload)

                try:
                    await asyncio.wait_for(
                        _stream(), timeout=self.settings.research_timeout_seconds
                    )
                except TimeoutError:
                    await _finalize_research(
                        db, repo, run_id, "timeout",
                        "The research request took too long. Please try again.",
                    )
                    return
                except Exception:  # noqa: BLE001
                    logger.exception("Research run %s failed", run_id)
                    await _finalize_research(
                        db, repo, run_id, "agent_error",
                        "Something went wrong. Please try again.",
                    )
                    return

                if run_event_bus.is_cancelled(run_id):
                    await repo.update_run_status(run_id, ResearchRunStatusEnum.STOPPED)
                    await db.commit()
                    await run_event_bus.publish(
                        run_id, "done", {"run_id": str(run_id), "status": "stopped"}
                    )
                    trace_stream_complete(str(run_id), "stopped")
                    return

                result = self._build_result(
                    coordinator_parts, writer_article, fallback_title
                )

                summary = tracker.redacted_summary()
                if summary:
                    await run_event_bus.publish(run_id, "reasoning", {"content": summary})

                version_number, title, chat_text = (
                    await projection.finalize_research_result(
                        session_id=session_id,
                        run_id=run_id,
                        result=result,
                        reasoning_content=summary,
                        fallback_title=fallback_title,
                    )
                )

                total_tokens = await projection.persist_research_costs(
                    session_id, run_id, cost_records
                )

                await repo.update_run_status(run_id, ResearchRunStatusEnum.COMPLETED)
                await db.commit()

                chunk_size = 80
                for i in range(0, len(chat_text), chunk_size):
                    await run_event_bus.publish(
                        run_id, "token", {"text": chat_text[i : i + chunk_size]}
                    )

                if result.article_markdown:
                    await run_event_bus.publish(
                        run_id,
                        "article",
                        {
                            "markdown": result.article_markdown,
                            "version": version_number,
                            "title": title,
                        },
                    )

                actions = result.suggested_actions
                if not actions and result.article_markdown:
                    actions = [
                        "Summarize this article",
                        "Add more code examples",
                        "Add a comparison section",
                        "Expand the sources list",
                    ]
                if actions:
                    await run_event_bus.publish(run_id, "actions", {"actions": actions})

                await run_event_bus.publish(
                    run_id,
                    "done",
                    {
                        "run_id": str(run_id),
                        "status": "completed",
                        "total_tokens": total_tokens,
                        "actions": actions,
                    },
                )
                trace_stream_complete(str(run_id), "completed")
        finally:
            await run_event_bus.close(run_id)

    @staticmethod
    def _build_result(
        coordinator_parts: list[str],
        writer_article: str,
        fallback_title: str,
    ) -> ResearchResult:
        """Build ResearchResult using writer output directly when available."""
        if writer_article:
            coordinator_text = "\n\n".join(
                p for p in coordinator_parts if p != writer_article
            ).strip()
            h1 = re.search(r"^#\s+(.+)$", writer_article, re.MULTILINE)
            title = h1.group(1).strip() if h1 else fallback_title
            return ResearchResult(
                chat_response=coordinator_text or f"Here is the article on {title}.",
                article_markdown=writer_article,
                article_title=title,
            )

        full_text = "\n\n".join(coordinator_parts).strip()
        if not full_text:
            return ResearchResult(
                chat_response="The research team could not produce an article. Please try again."
            )
        return ResearchResult(chat_response=full_text)


async def _finalize_chat(
    db: AsyncSession,
    repo: MessageRunRepository,
    projection: RunProjection,
    run: AgentRun,
    assistant_message_id: uuid.UUID,
    run_status: RunStatusEnum,
    msg_status: MessageStatusEnum,
    *,
    error: tuple[str, str] | None = None,
) -> None:
    kwargs: dict[str, str] = {}
    if error:
        kwargs["error_code"] = error[0]
        kwargs["error_message"] = error[1]
    await repo.update_run_status(run, run_status, **kwargs)
    await projection.finalize_chat_assistant(assistant_message_id, status=msg_status)
    await db.commit()
    if error:
        await run_event_bus.publish(run.id, "error", {"code": error[0], "message": error[1]})
    await run_event_bus.publish(
        run.id, "done", {"run_id": str(run.id), "status": run_status.value}
    )
    trace_stream_complete(str(run.id), run_status.value)


async def _finalize_research(
    db: AsyncSession,
    repo: ResearchRepository,
    run_id: uuid.UUID,
    code: str,
    message: str,
) -> None:
    await repo.update_run_status(
        run_id, ResearchRunStatusEnum.FAILED, error_code=code, error_message=message
    )
    await db.commit()
    await run_event_bus.publish(run_id, "error", {"code": code, "message": message})
    await run_event_bus.publish(
        run_id, "done", {"run_id": str(run_id), "status": "failed"}
    )
    trace_stream_complete(str(run_id), "failed")


class RunExecutor:
    """Thin dispatcher delegating to workflow-specific handlers."""

    def __init__(
        self,
        *,
        search_agent: Agent,
        research_team: Team,
        settings: Settings,
    ) -> None:
        self.chat = ChatRunHandler(search_agent, settings)
        self.research = ResearchRunHandler(research_team, settings)

    async def execute_chat_run(self, **kwargs: Any) -> None:
        await self.chat.execute(**kwargs)

    async def execute_research_run(self, **kwargs: Any) -> None:
        await self.research.execute(**kwargs)


_executor: RunExecutor | None = None


def set_run_executor(executor: RunExecutor) -> None:
    global _executor
    _executor = executor


def get_run_executor() -> RunExecutor:
    global _executor
    if _executor is None:
        from agentos_chat.agents.research_agent import create_research_team
        from agentos_chat.agents.search_agent import create_search_agent
        from agentos_chat.settings import get_settings

        settings = get_settings()
        _executor = RunExecutor(
            search_agent=create_search_agent(settings),
            research_team=create_research_team(settings),
            settings=settings,
        )
    return _executor
