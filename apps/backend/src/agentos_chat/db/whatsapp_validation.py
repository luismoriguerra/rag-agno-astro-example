import re

E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")


def normalize_whatsapp_phone(raw: str) -> str:
    """Normalize Meta webhook sender id to E.164."""
    stripped = raw.strip()
    if not stripped:
        return stripped
    if stripped.startswith("+"):
        return stripped
    return f"+{stripped}"


def is_valid_e164(phone: str) -> bool:
    return bool(E164_PATTERN.match(phone))
