"""Map Agno run events to SSE payloads for chat and research streams."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from agno.run.agent import (
    ModelRequestCompletedEvent,
    ReasoningContentDeltaEvent,
    RunCompletedEvent,
    RunContentEvent,
    RunStartedEvent,
    ToolCallCompletedEvent,
    ToolCallStartedEvent,
)
from agno.run.team import (
    ModelRequestCompletedEvent as TeamModelRequestCompleted,
)
from agno.run.team import (
    ReasoningContentDeltaEvent as TeamReasoningDelta,
)
from agno.run.team import (
    RunCompletedEvent as TeamRunCompletedEvent,
)
from agno.run.team import (
    RunContentEvent as TeamRunContentEvent,
)
from agno.run.team import (
    RunStartedEvent as TeamRunStartedEvent,
)
from agno.run.team import (
    ToolCallCompletedEvent as TeamToolCallCompleted,
)
from agno.run.team import (
    ToolCallStartedEvent as TeamToolCallStarted,
)

_SSEEvent = tuple[str, dict[str, Any]]

AnyModelRequestCompleted = ModelRequestCompletedEvent | TeamModelRequestCompleted
AnyRunCompleted = RunCompletedEvent | TeamRunCompletedEvent
AnyToolCallCompleted = ToolCallCompletedEvent | TeamToolCallCompleted

MODEL_COMPLETED_TYPES = (ModelRequestCompletedEvent, TeamModelRequestCompleted)
RUN_COMPLETED_TYPES = (RunCompletedEvent, TeamRunCompletedEvent)
TOOL_COMPLETED_TYPES = (ToolCallCompletedEvent, TeamToolCallCompleted)
TOOL_STARTED_TYPES = (ToolCallStartedEvent, TeamToolCallStarted)
RUN_STARTED_TYPES = (RunStartedEvent, TeamRunStartedEvent)
CONTENT_TYPES = (RunContentEvent, TeamRunContentEvent)
REASONING_TYPES = (ReasoningContentDeltaEvent, TeamReasoningDelta)


@dataclass
class ResearchPhaseTracker:
    """Track delegation/tool milestones for redacted research reasoning summary."""

    phases: list[str] = field(default_factory=list)
    tool_calls: int = 0
    _last_thinking: str = ""

    def note_delegation(self, agent_name: str) -> _SSEEvent | None:
        message = f"Delegating to {agent_name}..."
        if message == self._last_thinking:
            return None
        self._last_thinking = message
        if agent_name not in self.phases:
            self.phases.append(agent_name)
        return ("thinking", {"status": "delegating", "message": message})

    def note_tool_start(self, tool_name: str | None) -> _SSEEvent:
        self.tool_calls += 1
        label = (
            "Searching…"
            if tool_name and "tavily" in tool_name.lower()
            else "Working…"
        )
        self._last_thinking = label
        return ("thinking", {"status": "searching", "message": label})

    def redacted_summary(self) -> str:
        parts: list[str] = []
        if self.phases:
            parts.append(f"Phases: {', '.join(self.phases)}")
        if self.tool_calls:
            parts.append(f"Tool calls: {self.tool_calls}")
        return "; ".join(parts) if parts else "Research completed."


def _safe_thinking() -> _SSEEvent:
    return ("thinking", {"status": "working", "message": "Processing…"})


def map_chat_event(event: object) -> list[_SSEEvent]:
    out: list[_SSEEvent] = []
    if isinstance(event, CONTENT_TYPES):
        content = getattr(event, "content", None)
        if content:
            out.append(("token", {"text": str(content)}))
    elif isinstance(event, TOOL_STARTED_TYPES):
        tool = getattr(event, "tool", None)
        tool_name = tool.tool_name if tool else None
        if tool_name and "tavily" in tool_name.lower():
            out.append(("thinking", {"status": "searching", "message": "Searching…"}))
        else:
            out.append(("thinking", {"status": "working", "message": "Working…"}))
    elif isinstance(event, TOOL_COMPLETED_TYPES):
        source = extract_tavily_source(event)
        if source:
            out.append(("source", source))
    elif isinstance(event, REASONING_TYPES):
        out.append(_safe_thinking())
    return out


def map_research_event(
    event: object, tracker: ResearchPhaseTracker
) -> list[_SSEEvent]:
    out: list[_SSEEvent] = []
    if isinstance(event, RUN_STARTED_TYPES):
        name = getattr(event, "agent_name", None) or getattr(event, "team_name", None)
        if name:
            delegated = tracker.note_delegation(str(name))
            if delegated:
                out.append(delegated)
    elif isinstance(event, CONTENT_TYPES):
        content = getattr(event, "content", None)
        agent_name = getattr(event, "agent_name", None)
        if agent_name == "Article Writer" and content:
            writer_content = str(content)
            h1 = re.search(r"^#\s+(.+)$", writer_content, re.MULTILINE)
            preview_title = h1.group(1).strip() if h1 else "Research"
            out.append(
                ("article_preview", {"markdown": writer_content, "title": preview_title})
            )
    elif isinstance(event, TOOL_STARTED_TYPES):
        tool = getattr(event, "tool", None)
        tool_name = tool.tool_name if tool else None
        out.append(tracker.note_tool_start(tool_name))
    elif isinstance(event, TOOL_COMPLETED_TYPES):
        source = extract_tavily_source(event)
        if source:
            out.append(("source", source))
    elif isinstance(event, REASONING_TYPES):
        out.append(_safe_thinking())
    return out


def extract_tavily_source(event: object) -> dict[str, Any] | None:
    tool = getattr(event, "tool", None)
    if not tool or not tool.result:
        return None
    tool_name = tool.tool_name or ""
    if "tavily" not in tool_name.lower():
        return None
    try:
        payload = json.loads(tool.result)
    except (json.JSONDecodeError, TypeError):
        return None

    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        return None

    first = results[0]
    if not isinstance(first, dict):
        return None
    url = str(first.get("url") or "")
    if not url:
        return None
    return {
        "title": str(first.get("title") or url),
        "url": url,
        "snippet": str(first.get("content"))[:500] if first.get("content") else None,
        "rank": 1,
    }


def extract_all_tavily_sources(event: object) -> list[dict[str, Any]]:
    tool = getattr(event, "tool", None)
    if not tool or not tool.result:
        return []
    tool_name = tool.tool_name or ""
    if "tavily" not in tool_name.lower():
        return []
    try:
        payload = json.loads(tool.result)
    except (json.JSONDecodeError, TypeError):
        return []

    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return []

    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rank, item in enumerate(results, start=1):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append(
            {
                "title": str(item.get("title") or url),
                "url": url,
                "snippet": str(item.get("content"))[:500] if item.get("content") else None,
                "rank": rank,
            }
        )
        if len(sources) >= 10:
            break
    return sources


def map_model_cost(event: AnyModelRequestCompleted) -> dict[str, Any]:
    return {
        "model": str(getattr(event, "model", "") or ""),
        "agent_name": str(getattr(event, "agent_name", "") or ""),
        "input_tokens": int(getattr(event, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(event, "output_tokens", 0) or 0),
        "reasoning_tokens": int(getattr(event, "reasoning_tokens", 0) or 0),
        "total_tokens": int(getattr(event, "total_tokens", 0) or 0),
    }
