import json
import logging
from typing import Any

logger = logging.getLogger("agentos_chat")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, default=str))


def trace_session_restore(session_id: str, identity: str) -> None:
    log_event("session_restore", session_id=session_id, identity=identity)


def trace_agent_run_start(run_id: str, session_id: str) -> None:
    log_event("agent_run_start", run_id=run_id, session_id=session_id)


def trace_search_sources(run_id: str, source_count: int) -> None:
    log_event("search_sources_captured", run_id=run_id, source_count=source_count)


def trace_stream_complete(run_id: str, status: str) -> None:
    log_event("stream_complete", run_id=run_id, status=status)


def trace_run_stopped(run_id: str) -> None:
    log_event("run_stopped", run_id=run_id)


def trace_run_failed(run_id: str, code: str, message: str) -> None:
    log_event("run_failed", run_id=run_id, code=code, message=message)


def log_langwatch_disabled() -> None:
    log_event("langwatch_disabled")


def log_langwatch_enabled(environment: str) -> None:
    log_event("langwatch_enabled", environment=environment)


def log_langwatch_setup_failed(message: str) -> None:
    log_event("langwatch_setup_failed", message=message)


def log_langwatch_export_failed(run_id: str, message: str) -> None:
    log_event("langwatch_export_failed", run_id=run_id, message=message)
