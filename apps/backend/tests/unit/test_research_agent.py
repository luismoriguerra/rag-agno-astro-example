from agentos_chat.agents.research_agent import ResearchResult, parse_team_output


class TestResearchResult:
    def test_defaults(self):
        result = ResearchResult()
        assert result.chat_response == ""
        assert result.article_markdown == ""
        assert result.suggested_actions == []

    def test_full_structured_output(self):
        result = ResearchResult(
            chat_response="Here is what I found.",
            article_markdown="# My Article\n\n## TL;DR\nSummary.",
            article_title="My Article",
            suggested_actions=["Add benchmarks", "Compare with X"],
        )
        assert result.chat_response == "Here is what I found."
        assert result.article_markdown.startswith("# My Article")
        assert result.article_title == "My Article"
        assert len(result.suggested_actions) == 2

    def test_chat_only_response(self):
        result = ResearchResult(chat_response="Summary only.")
        assert result.article_markdown == ""
        assert result.suggested_actions == []


class TestParseTeamOutput:
    def test_article_with_chat_preamble(self):
        text = (
            "Here is what I found about Redis.\n\n"
            "# Redis: An In-Memory Data Store\n\n"
            "## TL;DR\nRedis is fast.\n\n"
            "## Sources\n1. https://redis.io\n"
        )
        result = parse_team_output(text)
        assert result.chat_response == "Here is what I found about Redis."
        assert result.article_markdown.startswith("# Redis")
        assert result.article_title == "Redis: An In-Memory Data Store"
        assert len(result.suggested_actions) > 0

    def test_chat_only_no_h1(self):
        text = "Here is a summary of the article. No changes needed."
        result = parse_team_output(text)
        assert result.chat_response == text
        assert result.article_markdown == ""
        assert result.suggested_actions == []

    def test_empty_text(self):
        result = parse_team_output("", fallback_title="Fallback")
        assert result.chat_response == "Done."

    def test_article_without_chat_preamble(self):
        text = "# Direct Article\n\n## TL;DR\nContent here.\n"
        result = parse_team_output(text, fallback_title="Fallback")
        assert result.article_markdown.startswith("# Direct Article")
        assert result.article_title == "Direct Article"
        assert "Direct Article" in result.chat_response

    def test_fallback_title(self):
        text = "Some conversation."
        result = parse_team_output(text, fallback_title="My Topic")
        assert result.chat_response == text
