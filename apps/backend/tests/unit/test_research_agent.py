from agentos_chat.agents.research_agent import parse_research_output


class TestParseResearchOutput:
    def test_full_output_with_all_delimiters(self):
        text = """
---CHAT_START---
Here is what I found about the topic.
---CHAT_END---

---ARTICLE_START---
# My Article

## TL;DR
A brief summary.

## Sources
1. https://example.com
---ARTICLE_END---

---ACTIONS_START---
["Add benchmarks", "Compare with X", "Add code examples"]
---ACTIONS_END---
"""
        result = parse_research_output(text)
        assert result.chat_response == "Here is what I found about the topic."
        assert result.article_markdown.startswith("# My Article")
        assert "TL;DR" in result.article_markdown
        assert result.article_title == "My Article"
        assert result.suggested_actions == [
            "Add benchmarks",
            "Compare with X",
            "Add code examples",
        ]

    def test_chat_only_response(self):
        text = """
---CHAT_START---
Here is a summary of the article. It covers three main topics.
---CHAT_END---
"""
        result = parse_research_output(text)
        assert result.chat_response == (
            "Here is a summary of the article. It covers three main topics."
        )
        assert result.article_markdown == ""
        assert result.suggested_actions == []

    def test_article_without_chat(self):
        text = """
---ARTICLE_START---
# Test Article

## TL;DR
Summary here.
---ARTICLE_END---
"""
        result = parse_research_output(text)
        assert result.article_markdown.startswith("# Test Article")
        assert result.article_title == "Test Article"
        assert result.chat_response == "Done."

    def test_no_delimiters_treats_as_chat(self):
        text = "# Raw Article\n\n## TL;DR\nSome content."
        result = parse_research_output(text, fallback_title="Fallback")
        assert result.article_markdown == ""
        assert result.article_title == "Fallback"
        assert "Raw Article" in result.chat_response

    def test_empty_text(self):
        result = parse_research_output("", fallback_title="Empty")
        assert result.chat_response == "Done."
        assert result.article_markdown == ""
        assert result.article_title == "Empty"

    def test_actions_invalid_json(self):
        text = """
---CHAT_START---
Response here.
---CHAT_END---

---ACTIONS_START---
not valid json
---ACTIONS_END---
"""
        result = parse_research_output(text)
        assert result.chat_response == "Response here."
        assert result.suggested_actions == []

    def test_actions_limits_to_five(self):
        text = """
---CHAT_START---
Ok.
---CHAT_END---

---ACTIONS_START---
["a", "b", "c", "d", "e", "f", "g"]
---ACTIONS_END---
"""
        result = parse_research_output(text)
        assert len(result.suggested_actions) == 5

    def test_fallback_title_when_no_h1(self):
        text = """
---ARTICLE_START---
Some content without an H1 heading.
---ARTICLE_END---
"""
        result = parse_research_output(text, fallback_title="My Fallback")
        assert result.article_title == "My Fallback"
