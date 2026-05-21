from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from agentos_chat.interfaces.whatsapp_mount import build_whatsapp_router
from agentos_chat.settings import Settings


@pytest.fixture
def whatsapp_settings() -> Settings:
    return Settings(
        whatsapp_verify_token="verify",
        whatsapp_access_token="token",
        whatsapp_phone_number_id="123",
        whatsapp_skip_signature_validation=True,
        request_timeout_seconds=5,
    )


@pytest.mark.asyncio
async def test_webhook_ignores_when_disabled(
    whatsapp_settings: Settings,
    engine,
    db_session,
) -> None:
    mock_agent = MagicMock()
    mock_agent.arun = AsyncMock()

    app = FastAPI()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    app.include_router(
        build_whatsapp_router(mock_agent, whatsapp_settings, session_factory=factory)
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "14155550100",
                                    "id": "msg1",
                                    "type": "text",
                                    "text": {"body": "Hello"},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/whatsapp/webhook", json=payload)
        assert response.status_code == 200

    await db_session.commit()
    mock_agent.arun.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_processes_when_enabled(
    whatsapp_settings: Settings,
    engine,
    db_session,
) -> None:
    from agentos_chat.db.whatsapp_settings_repository import update_enabled

    await update_enabled(db_session, enabled=True)
    await db_session.commit()

    mock_response = MagicMock()
    mock_response.status = "OK"
    mock_response.content = "Paris is the capital."

    mock_agent = MagicMock()
    mock_agent.arun = AsyncMock(return_value=mock_response)

    app = FastAPI()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    app.include_router(
        build_whatsapp_router(mock_agent, whatsapp_settings, session_factory=factory)
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "14155550101",
                                    "id": "msg2",
                                    "type": "text",
                                    "text": {"body": "What is the capital of France?"},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }

    with patch(
        "agentos_chat.interfaces.whatsapp_mount.WhatsAppTools.send_text_message_async",
        new_callable=AsyncMock,
    ) as send_mock:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/whatsapp/webhook", json=payload)
            assert response.status_code == 200

        import asyncio

        await asyncio.sleep(0.1)
        mock_agent.arun.assert_called_once()
        send_mock.assert_called()
