from agno.run.agent import RunContentEvent, ToolCallStartedEvent

from agentos_chat.agents.search_agent import safe_thinking_payload
from agentos_chat.services.event_mapper import (
    ResearchPhaseTracker,
    map_chat_event,
    map_research_event,
)


class TestSafeThinkingPayload:
    def test_returns_searching_status(self):
        payload = safe_thinking_payload()
        assert payload["status"] == "searching"
        assert "message" in payload


class TestMapChatEvent:
    def test_token_from_content_event(self):
        event = RunContentEvent(content="Hello")
        mapped = map_chat_event(event)
        assert ("token", {"text": "Hello"}) in mapped

    def test_thinking_from_tavily_tool_start(self):
        from agno.models.response import ToolExecution

        event = ToolCallStartedEvent(tool=ToolExecution(tool_name="tavily_search"))
        mapped = map_chat_event(event)
        assert mapped[0][0] == "thinking"
        assert mapped[0][1]["status"] == "searching"


class TestResearchPhaseTracker:
    def test_summary_with_phases_and_tools(self):
        tracker = ResearchPhaseTracker()
        tracker.note_delegation("Article Writer")
        tracker.tool_calls = 2
        summary = tracker.redacted_summary()
        assert "Article Writer" in summary
        assert "Tool calls: 2" in summary

    def test_dedup_delegation(self):
        tracker = ResearchPhaseTracker()
        first = tracker.note_delegation("Article Writer")
        second = tracker.note_delegation("Article Writer")
        assert first is not None
        assert second is None


class TestMapResearchEvent:
    def test_delegation_event(self):
        from agno.run.agent import RunStartedEvent

        tracker = ResearchPhaseTracker()
        event = RunStartedEvent(
            event="RunStarted",
            model="test",
            model_provider="openrouter",
            agent_name="Article Writer",
        )
        mapped = map_research_event(event, tracker)
        assert mapped[0][0] == "thinking"
        assert "Delegating" in mapped[0][1]["message"]
