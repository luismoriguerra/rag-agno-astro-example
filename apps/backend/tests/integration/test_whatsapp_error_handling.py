import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from agentos_chat.db.whatsapp_settings_repository import update_enabled
from agentos_chat.interfaces.whatsapp_mount import (
    AGENT_ERROR_MESSAGE,
    TIMEOUT_ERROR_MESSAGE,
    build_whatsapp_router,
)
from agentos_chat.settings import Settings


@pytest.fixture
def whatsapp_settings() -> Settings:
    return Settings(
        whatsapp_verify_token="verify",
        whatsapp_access_token="token",
        whatsapp_phone_number_id="123",
        whatsapp_skip_signature_validation=True,
        request_timeout_seconds=1,
    )


def _webhook_payload(phone: str, text: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": phone,
                                    "id": "msg-error",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }


@pytest.mark.asyncio
async def test_agent_failure_sends_user_message(
    whatsapp_settings: Settings,
    engine,
    db_session,
) -> None:
    await update_enabled(db_session, enabled=True)
    await db_session.commit()

    mock_agent = MagicMock()
    mock_agent.arun = AsyncMock(side_effect=RuntimeError("boom"))

    app = FastAPI()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    app.include_router(
        build_whatsapp_router(mock_agent, whatsapp_settings, session_factory=factory)
    )

    with patch(
        "agentos_chat.interfaces.whatsapp_mount.WhatsAppTools.send_text_message_async",
        new_callable=AsyncMock,
    ) as send_mock:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/whatsapp/webhook",
                json=_webhook_payload("14155550200", "trigger error"),
            )
        await asyncio.sleep(0.15)
        send_mock.assert_called()
        assert send_mock.call_args.kwargs["text"] == AGENT_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_agent_timeout_sends_user_message(
    whatsapp_settings: Settings,
    engine,
    db_session,
) -> None:
    await update_enabled(db_session, enabled=True)
    await db_session.commit()

    async def slow_arun(*_args, **_kwargs):
        await asyncio.sleep(2)
        return MagicMock(status="OK", content="late")

    mock_agent = MagicMock()
    mock_agent.arun = slow_arun

    app = FastAPI()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    app.include_router(
        build_whatsapp_router(mock_agent, whatsapp_settings, session_factory=factory)
    )

    with patch(
        "agentos_chat.interfaces.whatsapp_mount.WhatsAppTools.send_text_message_async",
        new_callable=AsyncMock,
    ) as send_mock:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/whatsapp/webhook",
                json=_webhook_payload("14155550201", "slow question"),
            )
        await asyncio.sleep(1.5)
        texts = [call.kwargs["text"] for call in send_mock.call_args_list]
        assert TIMEOUT_ERROR_MESSAGE in texts
