import asyncio
import hashlib
import hmac
import logging
import uuid
from collections.abc import Callable
from typing import Any

from agno.agent import Agent
from agno.tools.whatsapp import WhatsAppTools
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentos_chat.db.session import get_session_factory
from agentos_chat.services.logging import (
    log_whatsapp_error,
    log_whatsapp_gate,
    log_whatsapp_inbound,
    log_whatsapp_outbound,
)
from agentos_chat.services.whatsapp_gate import GateDecision, evaluate_gate
from agentos_chat.services.whatsapp_queue import PROCESSING_ACK, WhatsAppMessageQueue
from agentos_chat.settings import Settings

logger = logging.getLogger("agentos_chat")

AGENT_ERROR_MESSAGE = "Sorry, I couldn't process your message. Please try again."
TIMEOUT_ERROR_MESSAGE = (
    "Sorry, this is taking too long. Please try again or send /new to start fresh."
)
NEW_SESSION_ACK = "Started a new conversation."

RETRY_DELAYS_SECONDS = (2, 4, 8)


class WhatsAppSessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}

    def get_session_id(self, phone: str) -> str:
        if phone not in self._sessions:
            self._sessions[phone] = f"wa:{phone}"
        return self._sessions[phone]

    def reset_session(self, phone: str) -> str:
        session_id = f"wa:{phone}:{uuid.uuid4().hex[:8]}"
        self._sessions[phone] = session_id
        return session_id


def validate_webhook_signature(
    payload: bytes,
    signature_header: str | None,
    settings: Settings,
) -> bool:
    if settings.whatsapp_skip_signature_validation:
        return True

    if not settings.whatsapp_app_secret:
        raise HTTPException(
            status_code=500,
            detail="WHATSAPP_APP_SECRET is not set",
        )

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = signature_header.split("sha256=", 1)[1]
    calculated = hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(calculated, expected)


async def send_with_retry(
    send_fn: Callable[[], Any],
    *,
    phone: str,
) -> bool:
    for attempt, delay in enumerate(RETRY_DELAYS_SECONDS, start=1):
        try:
            await send_fn()
            log_whatsapp_outbound(phone=phone, retry_count=attempt - 1, success=True)
            return True
        except Exception as exc:
            log_whatsapp_outbound(
                phone=phone,
                retry_count=attempt,
                success=False,
                error=str(exc),
            )
            if attempt < len(RETRY_DELAYS_SECONDS):
                await asyncio.sleep(delay)
    return False


def build_whatsapp_router(
    agent: Agent,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
    queue = WhatsAppMessageQueue()
    sessions = WhatsAppSessionRegistry()
    whatsapp_tools = WhatsAppTools(async_mode=True)
    db_factory = session_factory or get_session_factory()

    async def send_text(phone: str, text: str) -> None:
        async def _send() -> None:
            await whatsapp_tools.send_text_message_async(recipient=phone, text=text)

        success = await send_with_retry(_send, phone=phone)
        if not success:
            log_whatsapp_error(phone=phone, message="outbound_delivery_failed")

    @router.get("/webhook")
    async def verify_webhook(request: Request) -> PlainTextResponse:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        if not settings.whatsapp_verify_token:
            raise HTTPException(status_code=500, detail="WHATSAPP_VERIFY_TOKEN is not set")

        if mode == "subscribe" and token == settings.whatsapp_verify_token:
            if not challenge:
                raise HTTPException(status_code=400, detail="No challenge received")
            return PlainTextResponse(content=challenge)

        raise HTTPException(status_code=403, detail="Invalid verify token or mode")

    @router.post("/webhook")
    async def webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")

        if not validate_webhook_signature(payload, signature, settings):
            raise HTTPException(status_code=403, detail="Invalid signature")

        body = await request.json()
        if body.get("object") != "whatsapp_business_account":
            return {"status": "ignored"}

        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                messages = change.get("value", {}).get("messages", [])
                if not messages:
                    continue
                message = messages[0]
                background_tasks.add_task(process_message, message)

        return {"status": "processing"}

    async def process_message(message: dict[str, object]) -> None:
        if message.get("type") != "text":
            return

        raw_phone = message.get("from", "")
        message_text = message.get("text", {}).get("body", "")
        if not raw_phone:
            return

        if not message_text or not message_text.strip():
            return

        async with db_factory() as db:
            gate = await evaluate_gate(db, raw_phone)
            log_whatsapp_gate(
                phone=gate.phone,
                enabled=gate.enabled,
                allowed=gate.decision == GateDecision.ALLOW,
                decision=gate.decision.value,
            )
            if gate.decision != GateDecision.ALLOW:
                return

        log_whatsapp_inbound(phone=gate.phone, message_preview=message_text[:80])

        async def handle() -> None:
            text = message_text.strip()
            if text.lower() == "/new":
                sessions.reset_session(gate.phone)
                await send_text(gate.phone, NEW_SESSION_ACK)
                return

            session_id = sessions.get_session_id(gate.phone)
            try:
                response = await asyncio.wait_for(
                    agent.arun(
                        text,
                        user_id=gate.phone,
                        session_id=session_id,
                    ),
                    timeout=settings.request_timeout_seconds,
                )
            except TimeoutError:
                log_whatsapp_error(phone=gate.phone, message="agent_timeout")
                await send_text(gate.phone, TIMEOUT_ERROR_MESSAGE)
                return
            except Exception as exc:
                log_whatsapp_error(phone=gate.phone, message=str(exc))
                await send_text(gate.phone, AGENT_ERROR_MESSAGE)
                return

            if getattr(response, "status", None) == "ERROR":
                log_whatsapp_error(phone=gate.phone, message="agent_error_status")
                await send_text(gate.phone, AGENT_ERROR_MESSAGE)
                return

            content = getattr(response, "content", None) or str(response)
            await send_text(gate.phone, str(content))

        async def ack_queued() -> None:
            await send_text(gate.phone, PROCESSING_ACK)

        await queue.enqueue(gate.phone, handle, on_queued=ack_queued)

    return router
