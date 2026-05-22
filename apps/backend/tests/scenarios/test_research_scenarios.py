"""Scenario-based simulation tests for the Research Team agent.

Uses langwatch-scenario to simulate multi-turn conversations
and evaluate agent behavior with a judge.

Requires:
- OPENROUTER_API_KEY (for judge/user simulator + research team)
- TAVILY_API_KEY (for the research team)
- PostgreSQL running (for Agno session storage)

Run: pytest tests/scenarios/ -v --timeout=120
"""

import os
import uuid

import pytest
import scenario

from agentos_chat.agents.research_agent import build_research_team

scenario.configure(
    default_model=os.environ.get(
        "SCENARIO_MODEL",
        "openrouter/google/gemini-2.0-flash-001",
    ),
)


class ResearchTeamAdapter(scenario.AgentAdapter):
    """Wraps the Research Team for scenario testing."""

    def __init__(self) -> None:
        self.session_id = f"test-scenario-{uuid.uuid4().hex[:8]}"
        self.team = build_research_team(session_id=self.session_id)

    async def call(
        self, input: scenario.AgentInput
    ) -> scenario.AgentReturnTypes:
        response = self.team.run(
            input.last_new_user_message_str(),
            session_id=input.thread_id,
            stream=False,
        )
        content = ""
        if hasattr(response, "content") and response.content:
            content = str(response.content)
        elif hasattr(response, "messages") and response.messages:
            content = str(response.messages[-1].content)
        return content


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_article_generation():
    """Scenario 1: User asks to research a topic and generate an article."""
    result = await scenario.run(
        name="research article generation",
        description=(
            "User asks the agent to research 'What is WebAssembly' "
            "and generate a concise article. Be very concise."
        ),
        agents=[
            ResearchTeamAdapter(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                criteria=[
                    "Agent should search the web for information",
                    (
                        "Agent response should contain "
                        "---ARTICLE_START--- and ---ARTICLE_END--- delimiters"
                    ),
                    "Article should start with a markdown H1 heading (#)",
                    "Article should contain a TL;DR section",
                    (
                        "Agent should include ---CHAT_START--- "
                        "with a conversational response"
                    ),
                ]
            ),
        ],
    )
    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_summarize_article():
    """Scenario 2: User generates article, then asks for a summary."""
    result = await scenario.run(
        name="summarize article",
        description=(
            "User first asks the agent to research 'Tavily API' "
            "and generate a very short article (2 paragraphs). "
            "Then the user asks 'Can you summarize this article?'"
        ),
        agents=[
            ResearchTeamAdapter(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                criteria=[
                    (
                        "On the summary request, agent should NOT include "
                        "---ARTICLE_START--- delimiters"
                    ),
                    (
                        "Agent should provide a concise summary "
                        "in ---CHAT_START--- block"
                    ),
                    (
                        "Summary should reference key points "
                        "from the previously generated article"
                    ),
                    "Agent should not re-generate the article",
                ]
            ),
        ],
    )
    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_question_about_article():
    """Scenario 3: User generates article, then asks a question."""
    result = await scenario.run(
        name="question about article",
        description=(
            "User asks the agent to research 'Deno vs Bun' "
            "and generate a very short article. Then the user asks "
            "'What are the main differences in their architecture?'"
        ),
        agents=[
            ResearchTeamAdapter(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                criteria=[
                    (
                        "Agent should answer the question "
                        "conversationally in ---CHAT_START---"
                    ),
                    (
                        "Agent should NOT include "
                        "---ARTICLE_START--- delimiters "
                        "when answering a question"
                    ),
                    "Answer should be relevant to the article content",
                ]
            ),
        ],
    )
    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_modify_article():
    """Scenario 4: User generates article, then asks to add a section."""
    result = await scenario.run(
        name="modify existing article",
        description=(
            "User asks the agent to research 'OpenFGA' "
            "and generate a very short article. Then the user asks "
            "'Add a section about performance benchmarks.'"
        ),
        agents=[
            ResearchTeamAdapter(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                criteria=[
                    (
                        "Agent should include ---ARTICLE_START--- "
                        "with an updated article"
                    ),
                    (
                        "Updated article should contain "
                        "a section about performance benchmarks"
                    ),
                    (
                        "---CHAT_START--- should describe "
                        "what was changed or added"
                    ),
                ]
            ),
        ],
    )
    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_actions_format():
    """Scenario 5: Verify follow-up actions format after article generation."""
    result = await scenario.run(
        name="follow-up actions format",
        description=(
            "User asks the agent to research 'GraphQL vs REST' "
            "and generate a very short article."
        ),
        agents=[
            ResearchTeamAdapter(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                criteria=[
                    (
                        "Agent response should contain "
                        "---ACTIONS_START--- and ---ACTIONS_END--- delimiters"
                    ),
                    (
                        "The ACTIONS block should contain "
                        "a valid JSON array of strings"
                    ),
                    "Array should have between 3 and 5 elements",
                    (
                        "Each action should be a specific, "
                        "actionable suggestion, not generic"
                    ),
                ]
            ),
        ],
    )
    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_follow_up_action_modifies_article():
    """Scenario 6: Click a follow-up action to expand the article.

    Verifies the fix where action clicks were ignored because the prompt
    only included the original idea without the user's follow-up request.
    """
    result = await scenario.run(
        name="follow-up action modifies article",
        description=(
            "User asks the agent to research 'Redis caching' "
            "and generate a very short article (1 paragraph). "
            "Then the user clicks an action button that says "
            "'Add a section about cache eviction strategies'. "
            "The agent must NOT refuse or say the article is already done. "
            "It must modify the article."
        ),
        agents=[
            ResearchTeamAdapter(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                criteria=[
                    (
                        "When the user requests to add a section, "
                        "the agent should NOT refuse or say "
                        "the article is already complete"
                    ),
                    (
                        "The agent should include ---ARTICLE_START--- "
                        "with an updated article on the second turn"
                    ),
                    (
                        "The updated article should contain content "
                        "about cache eviction strategies"
                    ),
                    (
                        "---CHAT_START--- should acknowledge "
                        "the addition or modification"
                    ),
                ]
            ),
        ],
    )
    assert result.success
