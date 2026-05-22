"""Unit tests for research service prompt building logic."""

from agentos_chat.services.research_service import _build_context_prompt


class TestBuildContextPrompt:
    def test_first_version_no_article(self):
        result = _build_context_prompt("What is Tavily?", None)
        assert "Research topic / idea:" in result
        assert "What is Tavily?" in result
        assert "No article has been written yet" in result
        assert "User request:" not in result

    def test_with_existing_article(self):
        result = _build_context_prompt(
            "What is Tavily?",
            "# Tavily\n\nContent here.",
        )
        assert "Current article draft:" in result
        assert "# Tavily" in result
        assert "No article has been written yet" not in result
        assert "User request:" not in result

    def test_same_message_as_idea_not_duplicated(self):
        result = _build_context_prompt(
            "What is Tavily?",
            "# Tavily\n\nContent.",
            user_message="What is Tavily?",
        )
        assert "User request:" not in result

    def test_follow_up_action_included(self):
        result = _build_context_prompt(
            "What is Tavily?",
            "# Tavily\n\nContent.",
            user_message="Explore Tavily pricing and rate limits",
        )
        assert "User request:" in result
        assert "Explore Tavily pricing and rate limits" in result

    def test_whitespace_variations_still_match(self):
        result = _build_context_prompt(
            "What is Tavily? ",
            "# Tavily\n\nContent.",
            user_message="  What is Tavily?  ",
        )
        assert "User request:" not in result

    def test_none_user_message(self):
        result = _build_context_prompt(
            "My topic",
            "# Article",
            user_message=None,
        )
        assert "User request:" not in result

    def test_empty_user_message(self):
        result = _build_context_prompt(
            "My topic",
            "# Article",
            user_message="",
        )
        assert "User request:" not in result

    def test_follow_up_without_article(self):
        result = _build_context_prompt(
            "What is Tavily?",
            None,
            user_message="Add more detail",
        )
        assert "No article has been written yet" in result
        assert "User request:" in result
        assert "Add more detail" in result

    def test_prompt_structure_order(self):
        result = _build_context_prompt(
            "Topic",
            "# Draft",
            user_message="Expand sources",
        )
        parts = result.split("\n\n")
        assert len(parts) == 3
        assert parts[0].startswith("Research topic / idea:")
        assert parts[1].startswith("Current article draft:")
        assert parts[2].startswith("User request:")
