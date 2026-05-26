"""Research team factory — delegates to Article Writer, then structured parse."""

from __future__ import annotations

import re

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openrouter import OpenRouter
from agno.team import Team
from agno.tools.tavily import TavilyTools
from pydantic import BaseModel, Field

from agentos_chat.settings import Settings


class ResearchResult(BaseModel):
    chat_response: str = Field(
        default="",
        description="Conversational response for the chat panel",
    )
    article_markdown: str = Field(
        default="",
        description=(
            "Full article markdown when creating or updating; "
            "empty for Q&A/summary-only"
        ),
    )
    article_title: str = Field(
        default="",
        description="Article title from H1 when article_markdown is set",
    )
    suggested_actions: list[str] = Field(
        default_factory=list,
        description="3-5 follow-up action suggestions after article creation",
    )


COORDINATOR_PROMPT = """\
You are a research assistant that helps users create, refine, and discuss \
technical articles.

You can handle several types of requests:

## 1. Create or Modify an Article
When the user asks to research a topic, create an article, or modify the \
existing article:
- Search the web using Tavily for relevant information
- Delegate the actual writing to the Article Writer agent
- After the writer produces the article, include the FULL article markdown \
in your final response

## 2. Summarize the Article
When the user asks for a summary, provide a concise summary. Do NOT include \
the article again.

## 3. Answer Questions
When the user asks a question, answer conversationally. Do NOT repeat the \
article.

## 4. General Conversation
For any other message, respond helpfully.

## Rules
- ALWAYS search with Tavily before delegating writing.
- ALWAYS delegate article writing to the Article Writer.
- After delegation, include the writer's full article in your response.
- Be friendly and concise in your conversational parts.
- Never expose raw chain-of-thought to the user.
"""

WRITER_PROMPT = """\
You are a technical article writer. You produce ONLY article content in markdown format.

## Rules
- Start with `# Title` — never start with conversational text.
- NEVER include preambles like "Here is the article", "Let me write...", "Sure, I'll...", etc.
- Output ONLY the article markdown, nothing else.

## Required Article Structure
1. `# Title` (H1 heading)
2. `## TL;DR` — 2-3 sentence summary
3. `## What You Will Learn Here` — bullet list of key takeaways
4. At least 3 well-researched body sections (H2 headings)
5. Code examples and ASCII diagrams where relevant
6. `## Sources` — numbered list with at least 3 cited URLs
"""


def create_research_team(settings: Settings) -> Team:
    model = OpenRouter(
        id=settings.research_agent_model,
        api_key=settings.openrouter_api_key or None,
        max_tokens=16384,
    )
    db = PostgresDb(
        db_url=settings.database_url_sync,
        session_table="research_agno_sessions",
    )
    writer_agent = Agent(
        name="Article Writer",
        role=(
            "Write technical articles in markdown format only. "
            "Output pure markdown, no conversational text."
        ),
        instructions=[WRITER_PROMPT],
    )
    return Team(
        name="Research Team",
        model=model,
        members=[writer_agent],
        tools=[TavilyTools(api_key=settings.tavily_api_key or None, search_depth="advanced")],
        instructions=[COORDINATOR_PROMPT],
        markdown=True,
        db=db,
        add_history_to_context=True,
        telemetry=settings.agno_telemetry,
    )


def parse_team_output(text: str, fallback_title: str = "Research") -> ResearchResult:
    """Parse the coordinator's final text into a structured ResearchResult.

    Looks for an article block (markdown starting with # heading) and separates
    conversational text from article content.
    """
    if not text or not text.strip():
        return ResearchResult(chat_response="Done.")

    h1_match = re.search(r"^(#\s+.+)$", text, re.MULTILINE)
    if not h1_match:
        return ResearchResult(chat_response=text.strip())

    article_start = h1_match.start()
    chat_part = text[:article_start].strip()
    article_part = text[article_start:].strip()

    title = h1_match.group(1).lstrip("# ").strip()

    actions: list[str] = []
    actions_match = re.search(
        r"(?:suggested|follow[- ]?up|next)[^:]*:\s*\n((?:\s*[-*]\s+.+\n?)+)",
        text[article_start:],
        re.IGNORECASE,
    )
    if actions_match:
        raw = actions_match.group(1)
        actions = [
            line.lstrip("-* ").strip()
            for line in raw.strip().splitlines()
            if line.strip()
        ][:5]

    if not actions and article_part:
        actions = [
            "Summarize this article",
            "Add more code examples",
            "Add a comparison section",
            "Expand the sources list",
        ]

    if not chat_part:
        chat_part = f"Here is the research article on {title}."

    return ResearchResult(
        chat_response=chat_part,
        article_markdown=article_part,
        article_title=title or fallback_title,
        suggested_actions=actions,
    )


def build_research_context_prompt(
    idea: str,
    current_article: str | None,
    user_message: str | None = None,
) -> str:
    parts: list[str] = [f"Research topic / idea:\n{idea}"]
    if current_article:
        parts.append(f"Current article draft:\n{current_article}")
    else:
        parts.append("No article has been written yet. Please create the first version.")
    if user_message and user_message.strip() != idea.strip():
        parts.append(f"User request:\n{user_message}")
    return "\n\n".join(parts)


def build_research_team(session_id: str | None = None) -> Team:
    """Backward-compatible factory; session_id is passed per arun() call instead."""
    from agentos_chat.settings import get_settings

    _ = session_id
    return create_research_team(get_settings())
