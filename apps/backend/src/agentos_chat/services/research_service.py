import asyncio
import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.agents.research_agent import (
    build_research_team,
    parse_research_output,
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
    current_article: str | None,
    user_message: str | None = None,
) -> str:
    """Build the prompt with idea, current article, and the user's request.

    When ``user_message`` differs from ``idea`` (e.g. a follow-up action like
    "Explore Tavily pricing and rate limits"), we include it as a separate
    "User request" so the LLM acts on the new instruction instead of
    re-confirming the existing article.
    """
    parts: list[str] = [f"Research topic / idea:\n{idea}"]

    if current_article:
        parts.append(f"Current article draft:\n{current_article}")
    else:
        parts.append("No article has been written yet. Please create the first version.")

    if user_message and user_message.strip() != idea.strip():
        parts.append(f"User request:\n{user_message}")

    return "\n\n".join(parts)


async def run_research(
    run_id: uuid.UUID,
    session_id: uuid.UUID,
    user_identity_id: uuid.UUID,
) -> None:
    """Execute the research team for a given run. Designed to run as a background task."""
    factory = get_session_factory()
    settings = get_settings()

    logger.info("run_research started: run=%s session=%s", run_id, session_id)

    async with factory() as db:
        repo = ResearchRepository(db)

        session = await repo.get_session_for_owner(session_id, user_identity_id)
        if not session:
            logger.error("Research session %s not found for user %s", session_id, user_identity_id)
            return

        current_article: str | None = None
        article = await repo.get_article_for_session(session_id)
        if article:
            latest_version = await repo.get_latest_version(article.id)
            if latest_version:
                current_article = latest_version.markdown_content

        user_message: str | None = None
        run = await repo.get_run(run_id)
        if run:
            trigger_msg = await repo.get_message_by_id(run.user_message_id)
            if trigger_msg:
                user_message = trigger_msg.content

        prompt = _build_context_prompt(session.idea, current_article, user_message)

        await repo.update_run_status(run_id, ResearchRunStatusEnum.RUNNING)
        await db.commit()

        await run_event_bus.publish(
            run_id, "thinking", {"status": "researching", "message": "Researching your topic..."}
        )

        try:
            team = build_research_team(session_id=str(session_id))
            logger.info("Research team built, invoking for run=%s", run_id)

            full_text = ""
            reasoning_parts: list[str] = []
            cost_records: list[dict] = []

            def _run_team_streaming() -> str:
                """Run the team with streaming and collect output + emit SSE events."""
                nonlocal full_text, reasoning_parts, cost_records
                collected = []
                chunk_count = 0
                reasoning_buffer: list[str] = []
                last_status = ""
                current_agent = "Research Team"

                for chunk in team.run(prompt, stream=True):
                    if run_event_bus.is_cancelled(run_id):
                        logger.info("Run %s cancelled by user", run_id)
                        break
                    chunk_count += 1
                    event = getattr(chunk, "event", "")

                    # Collect content from completion events
                    if event in ("RunCompleted", "TeamRunCompleted"):
                        content = getattr(chunk, "content", "")
                        agent_name = getattr(chunk, "agent_name", "")
                        team_name = getattr(chunk, "team_name", "")
                        if content:
                            content_str = str(content)
                            collected.append(content_str)
                            logger.info(
                                "%s from %s (team=%s): %d chars",
                                event,
                                agent_name or "unknown",
                                team_name or "none",
                                len(content_str),
                            )
                        # Article preview: emit as soon as writer finishes
                        if agent_name == "Article Writer" and content:
                            writer_content = str(content)
                            h1 = re.search(r"^#\s+(.+)$", writer_content, re.MULTILINE)
                            preview_title = h1.group(1).strip() if h1 else "Research"
                            _publish_sync(
                                run_id,
                                "article_preview",
                                {
                                    "markdown": writer_content,
                                    "title": preview_title,
                                },
                            )

                    # Track which agent is active
                    if event == "RunStarted":
                        agent_name = getattr(chunk, "agent_name", "")
                        if agent_name:
                            current_agent = agent_name
                            msg = f"Delegating to {agent_name}..."
                            if msg != last_status:
                                last_status = msg
                                _publish_sync(
                                    run_id, "thinking", {"status": "delegating", "message": msg}
                                )

                    # Collect streaming content from coordinator
                    if event == "TeamRunContent":
                        content = getattr(chunk, "content", "")
                        if content:
                            collected.append(str(content))

                    # Stream coordinator reasoning
                    if event == "TeamRunContent":
                        reasoning = getattr(chunk, "reasoning_content", "")
                        if reasoning:
                            reasoning_buffer.append(reasoning)
                            reasoning_parts.append(reasoning)
                            joined = "".join(reasoning_buffer)
                            if len(joined) > 30 and (
                                joined.endswith(".")
                                or joined.endswith("\n")
                                or len(reasoning_buffer) > 15
                            ):
                                clean = joined.strip().replace("\n", " ")
                                if clean and clean != last_status:
                                    last_status = clean
                                    _publish_sync(
                                        run_id,
                                        "thinking",
                                        {
                                            "status": "reasoning",
                                            "message": clean[:120]
                                            + ("..." if len(clean) > 120 else ""),
                                        },
                                    )
                                reasoning_buffer.clear()

                    # Collect streaming content from agents
                    if event == "RunContent":
                        content = getattr(chunk, "content", "")
                        if content:
                            collected.append(str(content))

                    # Stream writer agent reasoning
                    if event == "RunContent":
                        reasoning = getattr(chunk, "reasoning_content", "")
                        if reasoning:
                            reasoning_parts.append(reasoning)
                            reasoning_buffer.append(reasoning)
                            joined = "".join(reasoning_buffer)
                            if len(joined) > 40 and (
                                joined.endswith(".")
                                or joined.endswith("\n")
                                or len(reasoning_buffer) > 20
                            ):
                                clean = joined.strip().replace("\n", " ")
                                agent = getattr(chunk, "agent_name", current_agent)
                                if clean and clean != last_status:
                                    last_status = clean
                                    _publish_sync(
                                        run_id,
                                        "thinking",
                                        {
                                            "status": "writing",
                                            "message": f"{agent}: {clean[:100]}..."
                                            if len(clean) > 100
                                            else f"{agent}: {clean}",
                                        },
                                    )
                                reasoning_buffer.clear()

                    # Cost tracking: capture token usage from model requests
                    if event == "ModelRequestCompleted":
                        cost_records.append(
                            {
                                "model": str(getattr(chunk, "model", "") or ""),
                                "agent_name": str(getattr(chunk, "agent_name", "") or ""),
                                "input_tokens": getattr(chunk, "input_tokens", 0) or 0,
                                "output_tokens": getattr(chunk, "output_tokens", 0) or 0,
                                "reasoning_tokens": getattr(chunk, "reasoning_tokens", 0) or 0,
                                "total_tokens": getattr(chunk, "total_tokens", 0) or 0,
                            }
                        )
                        agent = getattr(chunk, "agent_name", "")
                        if agent and agent != "Article Writer":
                            msg = f"{agent}: processing search results..."
                            if msg != last_status:
                                last_status = msg
                                _publish_sync(
                                    run_id, "thinking", {"status": "processing", "message": msg}
                                )

                    # Also capture TeamRunCompleted (coordinator's final output)
                    if event == "TeamRunCompleted":
                        content = getattr(chunk, "content", "")
                        if content:
                            content_str = str(content)
                            collected.append(content_str)
                            logger.info(
                                "TeamRunCompleted: %d chars",
                                len(content_str),
                            )

                logger.info(
                    "Stream finished: %d chunks, %d chars collected, %d cost records",
                    chunk_count,
                    sum(len(c) for c in collected),
                    len(cost_records),
                )
                full_text = "".join(collected)
                return full_text

            _event_loop = asyncio.get_event_loop()

            def _publish_sync(rid, event, data):
                """Schedule an SSE publish from the sync streaming thread."""
                asyncio.run_coroutine_threadsafe(
                    run_event_bus.publish(rid, event, data),
                    _event_loop,
                )

            await run_event_bus.publish(
                run_id, "thinking", {"status": "starting", "message": "Starting research team..."}
            )

            await asyncio.wait_for(
                asyncio.to_thread(_run_team_streaming),
                timeout=settings.research_timeout_seconds,
            )

            logger.info(
                "full_text has_chat=%s has_article=%s has_actions=%s len=%d",
                "---CHAT_START---" in full_text,
                "---ARTICLE_START---" in full_text,
                "---ACTIONS_START---" in full_text,
                len(full_text),
            )

            if not full_text.strip():
                full_text = "The research team could not produce an article. Please try again."

            result = parse_research_output(full_text, fallback_title=session.idea[:60].strip())

            logger.info(
                "Research result for run=%s: chat=%d chars, article=%d chars, title=%s",
                run_id,
                len(result.chat_response),
                len(result.article_markdown),
                result.article_title,
            )

            reasoning_content = "".join(reasoning_parts).strip() if reasoning_parts else None

            if reasoning_content:
                await run_event_bus.publish(run_id, "reasoning", {"content": reasoning_content})

            chunk_size = 80
            for i in range(0, len(result.chat_response), chunk_size):
                chunk = result.chat_response[i : i + chunk_size]
                await run_event_bus.publish(run_id, "token", {"text": chunk})
                await asyncio.sleep(0.01)

            assistant_msg = await repo.create_message(
                session_id,
                ResearchMessageRoleEnum.ASSISTANT,
                result.chat_response,
                reasoning_content=reasoning_content,
            )
            await repo.update_run_assistant_message(run_id, assistant_msg.id)

            # Only create/update article if the response includes article content
            version_number = 0
            title = session.idea[:60].strip()
            if result.article_markdown:
                if not article:
                    article = await repo.create_article(session_id)

                version = await repo.create_article_version(article.id, result.article_markdown)
                version_number = version.version_number

                title = (
                    result.article_title
                    or ResearchRepository.extract_h1(result.article_markdown)
                    or title
                )
                await repo.update_session_title(session_id, title)

            await repo.update_run_status(run_id, ResearchRunStatusEnum.COMPLETED)

            # Store cost records
            total_tokens_all = 0
            for cr in cost_records:
                await repo.create_cost_record(
                    session_id=session_id,
                    run_id=run_id,
                    model=cr["model"],
                    agent_name=cr["agent_name"],
                    input_tokens=cr["input_tokens"],
                    output_tokens=cr["output_tokens"],
                    reasoning_tokens=cr["reasoning_tokens"],
                    total_tokens=cr["total_tokens"],
                )
                total_tokens_all += cr["total_tokens"]

            await db.commit()
            logger.info(
                "Stored %d cost records for run=%s, total_tokens=%d",
                len(cost_records),
                run_id,
                total_tokens_all,
            )

            # Emit article event only if article was created/updated
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

            # Emit suggested actions (with fallback defaults for article runs)
            if not result.suggested_actions and result.article_markdown:
                result.suggested_actions = [
                    "Summarize this article",
                    "Add more code examples",
                    "Add a comparison section",
                    "Expand the sources list",
                ]

            if result.suggested_actions:
                await run_event_bus.publish(
                    run_id,
                    "actions",
                    {"actions": result.suggested_actions},
                )
                await asyncio.sleep(0.1)

            await run_event_bus.publish(
                run_id,
                "done",
                {
                    "run_id": str(run_id),
                    "status": "completed",
                    "total_tokens": total_tokens_all,
                    "actions": result.suggested_actions,
                },
            )

        except TimeoutError:
            await _finalize_failed(
                db,
                repo,
                run_id,
                "timeout",
                "The research request took too long. Please try again.",
            )
        except Exception:  # noqa: BLE001
            logger.exception("Research run %s failed", run_id)
            await _finalize_failed(
                db,
                repo,
                run_id,
                "agent_error",
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
