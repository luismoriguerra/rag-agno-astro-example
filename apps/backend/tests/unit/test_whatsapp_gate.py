import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.db.whatsapp_settings_repository import add_allowlist_phone, update_enabled
from agentos_chat.services.whatsapp_gate import GateDecision, evaluate_gate


@pytest.mark.asyncio
async def test_gate_disabled(db_session: AsyncSession) -> None:
    result = await evaluate_gate(db_session, "14155550001")
    assert result.decision == GateDecision.DISABLED


@pytest.mark.asyncio
async def test_gate_open_when_enabled_empty_allowlist(db_session: AsyncSession) -> None:
    await update_enabled(db_session, enabled=True)
    result = await evaluate_gate(db_session, "14155550002")
    assert result.decision == GateDecision.ALLOW


@pytest.mark.asyncio
async def test_gate_blocks_non_allowlisted(db_session: AsyncSession) -> None:
    await update_enabled(db_session, enabled=True)
    await add_allowlist_phone(db_session, phone_number="+14155550003")
    result = await evaluate_gate(db_session, "14155559999")
    assert result.decision == GateDecision.NOT_ALLOWLISTED


@pytest.mark.asyncio
async def test_gate_allows_listed_number(db_session: AsyncSession) -> None:
    await update_enabled(db_session, enabled=True)
    await add_allowlist_phone(db_session, phone_number="+14155550004")
    result = await evaluate_gate(db_session, "14155550004")
    assert result.decision == GateDecision.ALLOW
