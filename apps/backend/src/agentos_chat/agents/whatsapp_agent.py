import os

from agno.agent import Agent
from agno.db.postgres import PostgresDb

from agentos_chat.agents.search_agent import build_search_agent
from agentos_chat.settings import Settings, get_settings


def sync_database_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def build_whatsapp_agent(settings: Settings | None = None) -> Agent:
    """WhatsApp agent sharing search config with REST, separate session namespace."""
    resolved = settings or get_settings()
    if resolved.openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = resolved.openrouter_api_key

    base = build_search_agent()
    db = PostgresDb(
        db_url=sync_database_url(resolved.database_url),
        session_table="whatsapp_agent_sessions",
    )
    return Agent(
        model=base.model,
        tools=base.tools,
        markdown=True,
        instructions=base.instructions,
        db=db,
        num_history_runs=10,
        add_history_to_context=True,
    )
