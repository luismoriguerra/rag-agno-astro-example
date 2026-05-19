from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING
from uuid import UUID

from agentos_chat.services.logging import (
    log_langwatch_disabled,
    log_langwatch_enabled,
    log_langwatch_export_failed,
    log_langwatch_setup_failed,
)
from agentos_chat.settings import AppEnvironment, get_settings

if TYPE_CHECKING:
    pass

_langwatch_initialized = False


def is_langwatch_enabled() -> bool:
    return _langwatch_initialized


def configure_langwatch() -> None:
    """Initialize LangWatch when API key is configured; no-op otherwise."""
    global _langwatch_initialized
    _langwatch_initialized = False

    settings = get_settings()
    api_key = settings.langwatch_api_key.strip()
    if not api_key:
        log_langwatch_disabled()
        return

    try:
        langwatch = __import__("langwatch")
        agno_instrumentation = __import__(
            "openinference.instrumentation.agno",
            fromlist=["AgnoInstrumentor"],
        )
        agno_instrumentor = agno_instrumentation.AgnoInstrumentor

        os.environ["LANGWATCH_API_KEY"] = api_key
        endpoint = settings.langwatch_endpoint.strip()
        if endpoint:
            os.environ["LANGWATCH_ENDPOINT"] = endpoint

        endpoint_url = endpoint or None
        langwatch.setup(
            api_key=api_key,
            endpoint_url=endpoint_url,
            instrumentors=[agno_instrumentor()],
        )
        _langwatch_initialized = True
        log_langwatch_enabled(settings.app_environment)
    except Exception as exc:  # noqa: BLE001
        log_langwatch_setup_failed(str(exc))


def _trace_metadata(
    run_id: UUID,
    session_id: UUID,
    auth_subject: str,
    environment: AppEnvironment,
) -> dict[str, str]:
    return {
        "run_id": str(run_id),
        "session_id": str(session_id),
        "auth_subject": auth_subject,
        "environment": environment,
    }


@contextmanager
def trace_agent_run(
    run_id: UUID,
    session_id: UUID,
    auth_subject: str,
) -> Generator[None, None, None]:
    """Wrap agent execution with LangWatch root trace metadata when enabled."""
    if not _langwatch_initialized:
        yield
        return

    settings = get_settings()
    metadata = _trace_metadata(run_id, session_id, auth_subject, settings.app_environment)

    trace_ctx = None
    try:
        langwatch = __import__("langwatch")
        trace_ctx = langwatch.trace(
            name="chat_agent_run",
            type="agent",
            metadata=metadata,
        )
        trace_ctx.__enter__()
    except Exception as exc:  # noqa: BLE001
        log_langwatch_export_failed(str(run_id), str(exc))
        yield
        return

    try:
        yield
    finally:
        if trace_ctx is not None:
            try:
                trace_ctx.__exit__(None, None, None)
            except Exception as exc:  # noqa: BLE001
                log_langwatch_export_failed(str(run_id), str(exc))
