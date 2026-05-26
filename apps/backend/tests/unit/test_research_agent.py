from agentos_chat.agents.research_agent import ResearchResult


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
