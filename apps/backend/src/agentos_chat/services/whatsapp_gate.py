from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.whatsapp_settings_repository import get_or_create_settings
from agentos_chat.db.whatsapp_validation import normalize_whatsapp_phone


class GateDecision(StrEnum):
    ALLOW = "allow"
    DISABLED = "disabled"
    NOT_ALLOWLISTED = "not_allowlisted"


@dataclass(frozen=True)
class GateResult:
    decision: GateDecision
    enabled: bool
    allowlist_size: int
    phone: str


async def evaluate_gate(db: AsyncSession, raw_phone: str) -> GateResult:
    phone = normalize_whatsapp_phone(raw_phone)
    settings = await get_or_create_settings(db)
    allowlist = {entry.phone_number for entry in settings.allowed_phone_numbers}

    if not settings.enabled:
        return GateResult(
            decision=GateDecision.DISABLED,
            enabled=False,
            allowlist_size=len(allowlist),
            phone=phone,
        )

    if allowlist and phone not in allowlist:
        return GateResult(
            decision=GateDecision.NOT_ALLOWLISTED,
            enabled=True,
            allowlist_size=len(allowlist),
            phone=phone,
        )

    return GateResult(
        decision=GateDecision.ALLOW,
        enabled=True,
        allowlist_size=len(allowlist),
        phone=phone,
    )
