import logging

from fastapi import FastAPI

from agentos_chat.agents.whatsapp_agent import build_whatsapp_agent
from agentos_chat.interfaces.whatsapp_mount import build_whatsapp_router
from agentos_chat.settings import Settings

logger = logging.getLogger("agentos_chat")


def mount_whatsapp_if_configured(app: FastAPI, settings: Settings) -> None:
    if not settings.whatsapp_configured:
        logger.warning(
            "WhatsApp not configured — skipping mount "
            "(set WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN)"
        )
        return

    import os

    os.environ.setdefault("WHATSAPP_ACCESS_TOKEN", settings.whatsapp_access_token)
    os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", settings.whatsapp_phone_number_id)
    os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", settings.whatsapp_verify_token)
    if settings.whatsapp_app_secret:
        os.environ.setdefault("WHATSAPP_APP_SECRET", settings.whatsapp_app_secret)

    agent = build_whatsapp_agent(settings)
    router = build_whatsapp_router(agent, settings)
    app.include_router(router)
    logger.info("WhatsApp webhook mounted at /whatsapp/webhook")
