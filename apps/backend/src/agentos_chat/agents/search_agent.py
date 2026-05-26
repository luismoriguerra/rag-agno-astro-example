"""Search agent factory for chat Q&A with Tavily grounding."""

from __future__ import annotations

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openrouter import OpenRouter
from agno.tools.tavily import TavilyTools

from agentos_chat.settings import Settings

SAFE_THINKING_MESSAGE = "Searching public web results"


def safe_thinking_payload() -> dict[str, str]:
    return {"status": "searching", "message": SAFE_THINKING_MESSAGE}


def create_search_agent(settings: Settings) -> Agent:
    return Agent(
        model=OpenRouter(id=settings.agent_model, api_key=settings.openrouter_api_key or None),
        tools=[TavilyTools(api_key=settings.tavily_api_key or None, search_depth="advanced")],
        db=PostgresDb(
            db_url=settings.database_url_sync,
            session_table="chat_agno_sessions",
        ),
        markdown=True,
        telemetry=settings.agno_telemetry,
        add_history_to_context=True,
        instructions=[
            "You answer questions using web search results.",
            "Cite sources with title and URL when grounding answers.",
            "If search does not provide enough information, say so clearly.",
            "Never reveal chain-of-thought or hidden reasoning.",
        ],
    )


# Backward-compatible alias for tests and gradual migration
def build_search_agent() -> Agent:
    from agentos_chat.settings import get_settings

    return create_search_agent(get_settings())
