import hashlib
import hmac

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agentos_chat.agents.whatsapp_agent import build_whatsapp_agent
from agentos_chat.interfaces.whatsapp_mount import build_whatsapp_router, validate_webhook_signature
from agentos_chat.settings import Settings


def test_validate_webhook_signature_accepts_valid_hmac() -> None:
    secret = "test-secret"
    payload = b'{"object":"whatsapp_business_account"}'
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    settings = Settings(
        whatsapp_app_secret=secret,
        whatsapp_skip_signature_validation=False,
    )
    assert validate_webhook_signature(payload, f"sha256={digest}", settings)


def test_validate_webhook_signature_rejects_invalid() -> None:
    settings = Settings(
        whatsapp_app_secret="test-secret",
        whatsapp_skip_signature_validation=False,
    )
    assert not validate_webhook_signature(b"{}", "sha256=deadbeef", settings)


def test_validate_webhook_signature_skip_flag() -> None:
    settings = Settings(
        whatsapp_app_secret="",
        whatsapp_skip_signature_validation=True,
    )
    assert validate_webhook_signature(b"{}", None, settings)


@pytest.mark.asyncio
async def test_verify_webhook_challenge() -> None:
    settings = Settings(
        whatsapp_verify_token="my-verify-token",
        whatsapp_access_token="token",
        whatsapp_phone_number_id="123",
        whatsapp_skip_signature_validation=True,
    )
    app = FastAPI()
    agent = build_whatsapp_agent(settings)
    app.include_router(build_whatsapp_router(agent, settings))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "my-verify-token",
                "hub.challenge": "challenge123",
            },
        )
    assert response.status_code == 200
    assert response.text == "challenge123"


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature() -> None:
    settings = Settings(
        whatsapp_verify_token="my-verify-token",
        whatsapp_access_token="token",
        whatsapp_phone_number_id="123",
        whatsapp_app_secret="secret",
        whatsapp_skip_signature_validation=False,
    )
    app = FastAPI()
    agent = build_whatsapp_agent(settings)
    app.include_router(build_whatsapp_router(agent, settings))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/whatsapp/webhook",
            content=b"{}",
            headers={"X-Hub-Signature-256": "sha256=invalid"},
        )
    assert response.status_code == 403
