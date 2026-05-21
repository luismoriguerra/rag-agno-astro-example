from agentos_chat.interfaces.whatsapp_mount import WhatsAppSessionRegistry


def test_new_session_changes_session_id() -> None:
    registry = WhatsAppSessionRegistry()
    phone = "+14155550999"
    first = registry.get_session_id(phone)
    second = registry.reset_session(phone)
    third = registry.get_session_id(phone)
    assert first == f"wa:{phone}"
    assert second.startswith(f"wa:{phone}:")
    assert third == second
    assert second != first
