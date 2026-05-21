import os
import re

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools

from agentos_chat.settings import get_settings

ARTICLE_DELIMITER = "---ARTICLE_END---"
ARTICLE_SPLIT_PATTERN = re.compile(rf"\n*{re.escape(ARTICLE_DELIMITER)}\n*")

RESEARCH_SYSTEM_PROMPT = """\
You are a research agent that creates high-quality technical articles.

## Research Process
1. Search the web for the given topic using multiple searches (one per section/theme)
2. Plan the article structure: propose sections, target audience, and writing style
3. Write the full article

## Article Structure Requirements
Every article MUST include:
- TL;DR at the top (2-3 sentence summary)
- "What you will learn here" section (bullet list)
- At least 3 well-researched body sections
- Code examples and ASCII diagrams where relevant
- Source list at the end with at least 3 cited URLs

## Writing Style
- Be friendly and clear for an audience of Engineers and PMs
- Include code examples and ASCII flow diagrams for better understanding
- Cite sources inline and in a final source list

## After Writing
- Identify any gaps in the article
- Recommend additional sections or improvements

## Output Format
Write the complete article in markdown. At the very end, on a new line, output the delimiter:
---ARTICLE_END---

Then provide any gap analysis or recommendations as regular chat text.
"""


def build_research_agent() -> Agent:
    settings = get_settings()
    if settings.openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
    model = OpenRouter(
        id=settings.research_agent_model,
        max_tokens=16384,
    )
    return Agent(
        model=model,
        tools=[DuckDuckGoTools()],
        markdown=True,
        instructions=[RESEARCH_SYSTEM_PROMPT],
    )


def split_article_and_chat(text: str) -> tuple[str, str]:
    """Split agent output at the ---ARTICLE_END--- delimiter.

    Returns (article_markdown, chat_text). If the delimiter is absent,
    the entire text is treated as the article with empty chat.
    """
    parts = ARTICLE_SPLIT_PATTERN.split(text, maxsplit=1)
    article = parts[0].strip()
    chat = parts[1].strip() if len(parts) > 1 else ""
    return article, chat
