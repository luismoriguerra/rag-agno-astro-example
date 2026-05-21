from agentos_chat.agents.whatsapp_agent import build_whatsapp_agent


def test_whatsapp_agent_uses_ten_history_runs() -> None:
    agent = build_whatsapp_agent()
    assert agent.num_history_runs == 10
    assert agent.add_history_to_context is True
