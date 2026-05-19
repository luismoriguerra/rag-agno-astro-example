import os
import re
from typing import Any

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools

from agentos_chat.settings import get_settings

URL_PATTERN = re.compile(r"https?://[^\s\])>]+")


def build_search_agent() -> Agent:
    settings = get_settings()
    if settings.openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
    model = OpenRouter(id=settings.agent_model)
    return Agent(
        model=model,
        tools=[DuckDuckGoTools()],
        markdown=True,
        instructions=[
            "You answer questions using DuckDuckGo search results.",
            "Cite sources with title and URL when grounding answers.",
            "If search does not provide enough information, say so clearly.",
            "Never reveal chain-of-thought or hidden reasoning.",
        ],
    )


def extract_sources_from_text(text: str) -> list[dict[str, str | int | None]]:
    urls = list(dict.fromkeys(URL_PATTERN.findall(text)))
    sources: list[dict[str, str | int | None]] = []
    for rank, url in enumerate(urls, start=1):
        sources.append({"title": url, "url": url, "snippet": None, "rank": rank})
    return sources[:10]


def build_history_prompt(messages: list[tuple[str, str]]) -> str:
    if not messages:
        return ""
    lines = ["Previous conversation:"]
    for role, content in messages:
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {content}")
    lines.append("")
    return "\n".join(lines)


def format_user_prompt(history: list[tuple[str, str]], question: str) -> str:
    prefix = build_history_prompt(history)
    if prefix:
        return f"{prefix}\nUser question: {question}"
    return question


SAFE_THINKING_MESSAGE = "Searching public web results"


def safe_thinking_payload() -> dict[str, Any]:
    return {"status": "searching", "message": SAFE_THINKING_MESSAGE}
