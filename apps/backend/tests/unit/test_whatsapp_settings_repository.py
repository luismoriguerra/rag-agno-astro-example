from agentos_chat.db.whatsapp_validation import is_valid_e164, normalize_whatsapp_phone


def test_normalize_whatsapp_phone_adds_plus() -> None:
    assert normalize_whatsapp_phone("14155552671") == "+14155552671"


def test_is_valid_e164_accepts_international() -> None:
    assert is_valid_e164("+14155552671")


def test_is_valid_e164_rejects_missing_plus() -> None:
    assert not is_valid_e164("14155552671")
