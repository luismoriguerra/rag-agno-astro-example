import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.agents.research_agent import (
    build_research_agent,
    split_article_and_chat,
)
from agentos_chat.db.models import (
    ResearchMessageRoleEnum,
    ResearchRunStatusEnum,
)
from agentos_chat.db.research_repository import ResearchRepository
from agentos_chat.db.session import get_session_factory
from agentos_chat.services.run_events import run_event_bus
from agentos_chat.settings import get_settings

logger = logging.getLogger(__name__)


def _build_context_prompt(
    idea: str,
    chat_history: list[tuple[str, str]],
    current_article: str | None,
) -> str:
    parts: list[str] = [f"Research topic / idea:\n{idea}"]

    if chat_history:
        lines = ["Previous conversation:"]
        for role, content in chat_history:
            label = "User" if role == "user" else "Assistant"
            lines.append(f"{label}: {content}")
        parts.append("\n".join(lines))

    if current_article:
        parts.append(f"Current article draft:\n{current_article}")
    else:
        parts.append("No article has been written yet. Please create the first version.")

    return "\n\n".join(parts)


async def run_research(
    run_id: uuid.UUID,
    session_id: uuid.UUID,
    user_identity_id: uuid.UUID,
) -> None:
    """Execute the research agent for a given run. Designed to run as a background task."""
    factory = get_session_factory()
    settings = get_settings()

    async with factory() as db:
        repo = ResearchRepository(db)

        session = await repo.get_session_for_owner(session_id, user_identity_id)
        if not session:
            logger.error("Research session %s not found for user %s", session_id, user_identity_id)
            return

        messages = await repo.list_messages(session_id)
        chat_history: list[tuple[str, str]] = [
            (m.role if isinstance(m.role, str) else m.role.value, m.content)
            for m in messages
            if m.content
        ]

        current_article: str | None = None
        article = await repo.get_article_for_session(session_id)
        if article:
            latest_version = await repo.get_latest_version(article.id)
            if latest_version:
                current_article = latest_version.markdown_content

        prompt = _build_context_prompt(session.idea, chat_history, current_article)

        await repo.update_run_status(run_id, ResearchRunStatusEnum.RUNNING)
        await db.commit()

        await run_event_bus.publish(
            run_id, "thinking", {"status": "researching", "message": "Researching your topic..."}
        )

        try:
            agent = build_research_agent()
            response = await asyncio.wait_for(
                asyncio.to_thread(agent.run, prompt, stream=False),
                timeout=settings.research_timeout_seconds,
            )

            text = ""
            if hasattr(response, "content") and response.content:
                text = str(response.content)
            elif hasattr(response, "messages") and response.messages:
                text = str(response.messages[-1].content)
            else:
                text = str(response)

            if not text.strip():
                text = "The research agent could not produce an article. Please try again with more specific guidance."

            article_md, chat_text = split_article_and_chat(text)

            reasoning_content = None
            if hasattr(response, "messages") and response.messages:
                for msg in response.messages:
                    if hasattr(msg, "reasoning_content") and msg.reasoning_content:
                        reasoning_content = str(msg.reasoning_content)
                        break

            if reasoning_content:
                await run_event_bus.publish(
                    run_id, "reasoning", {"content": reasoning_content}
                )

            chunk_size = 80
            for i in range(0, len(chat_text or article_md), chunk_size):
                chunk = (chat_text or article_md)[i : i + chunk_size]
                await run_event_bus.publish(run_id, "token", {"text": chunk})
                await asyncio.sleep(0.01)

            agent_chat_content = chat_text if chat_text else "Article generated successfully."
            await repo.create_message(
                session_id,
                ResearchMessageRoleEnum.ASSISTANT,
                agent_chat_content,
                reasoning_content=reasoning_content,
            )

            if not article:
                article = await repo.create_article(session_id)

            version = await repo.create_article_version(article.id, article_md)

            h1 = ResearchRepository.extract_h1(article_md)
            title = h1 or session.idea[:60].strip()
            await repo.update_session_title(session_id, title)

            await repo.update_run_status(run_id, ResearchRunStatusEnum.COMPLETED)
            await db.commit()

            await run_event_bus.publish(
                run_id,
                "article",
                {
                    "markdown": article_md,
                    "version": version.version_number,
                    "title": title,
                },
            )
            await run_event_bus.publish(
                run_id,
                "done",
                {"run_id": str(run_id), "status": "completed"},
            )

        except TimeoutError:
            await _finalize_failed(
                db, repo, run_id, "timeout",
                "The research request took too long. Please try again.",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Research run %s failed", run_id)
            await _finalize_failed(
                db, repo, run_id, "agent_error",
                "Something went wrong while generating the article. Please try again.",
            )
        finally:
            await run_event_bus.close(run_id)


async def _finalize_failed(
    db: AsyncSession,
    repo: ResearchRepository,
    run_id: uuid.UUID,
    code: str,
    message: str,
) -> None:
    await repo.update_run_status(
        run_id,
        ResearchRunStatusEnum.FAILED,
        error_code=code,
        error_message=message,
    )
    await db.commit()
    await run_event_bus.publish(run_id, "error", {"code": code, "message": message})
