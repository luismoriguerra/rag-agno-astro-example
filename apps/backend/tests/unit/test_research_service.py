"""Unit tests for research context prompt building."""

from agentos_chat.agents.research_agent import build_research_context_prompt


class TestBuildContextPrompt:
    def test_first_version_no_article(self):
        result = build_research_context_prompt("What is Tavily?", None)
        assert "Research topic / idea:" in result
        assert "What is Tavily?" in result
        assert "No article has been written yet" in result
        assert "User request:" not in result

    def test_with_existing_article(self):
        result = build_research_context_prompt(
            "What is Tavily?",
            "# Tavily\n\nContent here.",
        )
        assert "Current article draft:" in result
        assert "# Tavily" in result
        assert "No article has been written yet" not in result

    def test_same_message_as_idea_not_duplicated(self):
        result = build_research_context_prompt(
            "What is Tavily?",
            "# Tavily\n\nContent.",
            user_message="What is Tavily?",
        )
        assert "User request:" not in result

    def test_follow_up_action_included(self):
        result = build_research_context_prompt(
            "What is Tavily?",
            "# Tavily\n\nContent.",
            user_message="Explore Tavily pricing",
        )
        assert "User request:" in result
        assert "Explore Tavily pricing" in result

    def test_none_user_message(self):
        result = build_research_context_prompt("My topic", "# Article", user_message=None)
        assert "User request:" not in result
