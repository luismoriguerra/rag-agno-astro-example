"""Research team factory — uses Agno structured output and best practices."""

from __future__ import annotations

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


COORDINATOR_DESCRIPTION = (
    "You are a research assistant that helps users create, refine, "
    "and discuss technical articles."
)

COORDINATOR_INSTRUCTIONS = """\
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

COORDINATOR_EXPECTED_OUTPUT = """\
Return a structured ResearchResult with these fields:
- chat_response: A friendly conversational message for the user.
- article_markdown: The full article in markdown (empty if Q&A/summary-only).
- article_title: The article title extracted from the H1 heading (empty if no article).
- suggested_actions: 3-5 specific follow-up actions the user could take next \
(empty if no article).
"""

WRITER_DESCRIPTION = (
    "You are a technical article writer that produces high-quality "
    "markdown content from research findings."
)

WRITER_INSTRUCTIONS = """\
- Start with `# Title` — never start with conversational text.
- NEVER include preambles like "Here is the article", "Let me write...", etc.
- Output ONLY the article markdown, nothing else.
"""

WRITER_EXPECTED_OUTPUT = """\
A markdown article with this structure:
1. `# Title` (H1 heading)
2. `## TL;DR` — 2-3 sentence summary
3. `## What You Will Learn Here` — bullet list of key takeaways
4. At least 3 well-researched body sections (H2 headings)
5. Code examples and ASCII diagrams where relevant
6. `## Sources` — numbered list with at least 3 cited URLs
"""


def create_research_team(settings: Settings) -> Team:
    coordinator_model = OpenRouter(
        id=settings.research_agent_model,
        api_key=settings.openrouter_api_key or None,
        max_tokens=16384,
    )

    writer_model_id = settings.research_writer_model or settings.research_agent_model
    writer_model = OpenRouter(
        id=writer_model_id,
        api_key=settings.openrouter_api_key or None,
        max_tokens=16384,
    )

    db = PostgresDb(
        db_url=settings.database_url_sync,
        session_table="research_agno_sessions",
    )

    writer_agent = Agent(
        name="Article Writer",
        description=WRITER_DESCRIPTION,
        role=(
            "Write technical articles in markdown format only. "
            "Output pure markdown, no conversational text."
        ),
        model=writer_model,
        instructions=[WRITER_INSTRUCTIONS],
        expected_output=WRITER_EXPECTED_OUTPUT,
    )

    return Team(
        name="Research Team",
        description=COORDINATOR_DESCRIPTION,
        model=coordinator_model,
        members=[writer_agent],
        tools=[TavilyTools(api_key=settings.tavily_api_key or None, search_depth="advanced")],
        instructions=[COORDINATOR_INSTRUCTIONS],
        expected_output=COORDINATOR_EXPECTED_OUTPUT,
        markdown=True,
        db=db,
        add_history_to_context=True,
        enable_session_summaries=True,
        add_session_summary_to_context=True,
        enable_user_memories=True,
        add_memories_to_context=True,
        retries=3,
        delay_between_retries=1,
        exponential_backoff=True,
        debug_mode=settings.agno_debug,
        telemetry=settings.agno_telemetry,
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
