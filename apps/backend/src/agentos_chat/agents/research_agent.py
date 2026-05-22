import json
import os
import re

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openrouter import OpenRouter
from agno.team import Team
from agno.tools.tavily import TavilyTools
from pydantic import BaseModel, Field

from agentos_chat.settings import get_settings

CHAT_PATTERN = re.compile(r"---CHAT_START---\s*(.*?)\s*---CHAT_END---", re.DOTALL)
ARTICLE_PATTERN = re.compile(r"---ARTICLE_START---\s*(.*?)\s*---ARTICLE_END---", re.DOTALL)
ACTIONS_PATTERN = re.compile(r"---ACTIONS_START---\s*(.*?)\s*---ACTIONS_END---", re.DOTALL)


class ResearchResult(BaseModel):
    chat_response: str = Field(default="")
    article_markdown: str = Field(default="")
    article_title: str = Field(default="")
    suggested_actions: list[str] = Field(default_factory=list)


COORDINATOR_PROMPT = """\
You are a research assistant that helps users create, refine, and discuss technical articles.

You can handle several types of requests:

## 1. Create or Modify an Article
When the user asks to research a topic, create an article, or modify the existing article:
- Search the web using Tavily for relevant information
- Delegate the actual writing to the Article Writer agent
- Include the article in your response using the ARTICLE delimiters
- Suggest follow-up actions

## 2. Summarize the Article
When the user asks for a summary, provide a concise summary in your chat response.
Do NOT include ARTICLE delimiters — the article panel stays unchanged.

## 3. Answer Questions
When the user asks a question about the article or topic, answer conversationally.
Do NOT include ARTICLE delimiters — the article panel stays unchanged.

## 4. General Conversation
For any other message, respond conversationally and helpfully.

## Output Format

### When creating/modifying an article:
Your response MUST include ALL three delimiter blocks:

---CHAT_START---
[Your conversational response about the research, what you found, any gaps]
---CHAT_END---

---ARTICLE_START---
[The complete article markdown from the Article Writer — no preamble]
---ARTICLE_END---

---ACTIONS_START---
["Suggested action 1", "Suggested action 2", "Suggested action 3"]
---ACTIONS_END---

### When NOT creating/modifying an article (summary, Q&A, chat):
Your response should ONLY include the CHAT block:

---CHAT_START---
[Your conversational response]
---CHAT_END---

## Rules
- Always include ---CHAT_START/END--- in every response.
- Only include ---ARTICLE_START/END--- when you are creating or modifying the article.
- Only include ---ACTIONS_START/END--- after article creation/modification.
- The ACTIONS block must contain a valid JSON array of 3-5 short action strings.
- Actions should be specific and actionable
  (e.g., "Add benchmarks section", "Compare with X").
- The CHAT section should be friendly, for Engineers and PMs.
- Never put AI preamble in the ARTICLE section.
"""

WRITER_PROMPT = """\
You are a technical article writer. You produce ONLY article content in markdown format.

## Rules
- Start with `# Title` — never start with conversational text.
- NEVER include preambles like "Here is the article", "Let me write...", "Sure, I'll...", etc.
- NEVER include meta-commentary about the writing process.
- Output ONLY the article markdown, nothing else.

## Required Article Structure
1. `# Title` (H1 heading)
2. `## TL;DR` — 2-3 sentence summary
3. `## What You Will Learn Here` — bullet list of key takeaways
4. At least 3 well-researched body sections (H2 headings)
5. Code examples and ASCII diagrams where relevant
6. `## Sources` — numbered list with at least 3 cited URLs

## Writing Style
- Friendly and clear for an audience of Engineers and PMs
- Include code examples with language-tagged fenced code blocks
- Use ASCII flow diagrams for architecture/process explanation
- Cite sources inline (linked) and in the final Sources section
"""


def build_research_team(session_id: str | None = None) -> Team:
    settings = get_settings()
    if settings.openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
    if settings.tavily_api_key:
        os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

    model = OpenRouter(
        id=settings.research_agent_model,
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

    team_kwargs: dict = {
        "name": "Research Team",
        "model": model,
        "members": [writer_agent],
        "tools": [TavilyTools(search_depth="advanced")],
        "instructions": [COORDINATOR_PROMPT],
        "markdown": True,
        "db": db,
        "add_history_to_context": True,
    }
    if session_id:
        team_kwargs["session_id"] = session_id

    return Team(**team_kwargs)


def parse_research_output(text: str, fallback_title: str = "Research") -> ResearchResult:
    """Parse the Team output into structured ResearchResult.

    Handles both article-producing and chat-only responses.
    """
    chat_match = CHAT_PATTERN.search(text)
    article_match = ARTICLE_PATTERN.search(text)
    actions_match = ACTIONS_PATTERN.search(text)

    # Extract chat response
    if chat_match:
        chat_response = chat_match.group(1).strip()
    else:
        cleaned = text.strip()
        for pattern in (ARTICLE_PATTERN, ACTIONS_PATTERN):
            cleaned = pattern.sub("", cleaned).strip()
        chat_response = cleaned if cleaned else "Done."

    # Extract article (empty string = chat-only, no article update)
    article_markdown = ""
    if article_match:
        article_markdown = article_match.group(1).strip()

    # Extract title from article H1
    article_title = fallback_title
    if article_markdown:
        h1_match = re.search(r"^#\s+(.+)$", article_markdown, re.MULTILINE)
        if h1_match:
            article_title = h1_match.group(1).strip()

    # Extract suggested actions
    suggested_actions: list[str] = []
    if actions_match:
        try:
            raw = actions_match.group(1).strip()
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                suggested_actions = [str(a) for a in parsed[:5]]
        except (json.JSONDecodeError, ValueError):
            pass

    return ResearchResult(
        chat_response=chat_response,
        article_markdown=article_markdown,
        article_title=article_title,
        suggested_actions=suggested_actions,
    )
