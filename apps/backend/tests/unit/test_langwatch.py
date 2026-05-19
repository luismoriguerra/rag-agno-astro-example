import builtins
import uuid
from unittest.mock import MagicMock, patch

import pytest

import agentos_chat.observability.langwatch as langwatch_module
from agentos_chat.observability.langwatch import configure_langwatch, trace_agent_run
from agentos_chat.settings import Settings, get_settings

_ORIGINAL_IMPORT = builtins.__import__


@pytest.fixture(autouse=True)
def reset_langwatch_state() -> None:
    langwatch_module._langwatch_initialized = False
    get_settings.cache_clear()
    yield
    langwatch_module._langwatch_initialized = False
    get_settings.cache_clear()


def test_configure_langwatch_noop_without_api_key() -> None:
    with patch(
        "agentos_chat.observability.langwatch.get_settings",
        return_value=Settings(langwatch_api_key=""),
    ):
        with patch("builtins.__import__") as mock_import:
            configure_langwatch()
            mock_import.assert_not_called()
    assert langwatch_module.is_langwatch_enabled() is False


def test_configure_langwatch_calls_setup_with_instrumentor() -> None:
    settings = Settings(
        langwatch_api_key="test-key",
        langwatch_endpoint="https://custom.langwatch.example",
        app_environment="staging",
    )
    mock_langwatch = MagicMock()
    mock_instrumentor = MagicMock()
    mock_agno_mod = MagicMock()
    mock_agno_mod.AgnoInstrumentor.return_value = mock_instrumentor

    def fake_import(
        name: str,
        globals: dict | None = None,
        locals: dict | None = None,
        fromlist: tuple = (),
        level: int = 0,
    ) -> object:
        if name == "langwatch":
            return mock_langwatch
        if name == "openinference.instrumentation.agno":
            return mock_agno_mod
        return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)

    with patch("agentos_chat.observability.langwatch.get_settings", return_value=settings):
        with patch("builtins.__import__", side_effect=fake_import):
            configure_langwatch()
            mock_langwatch.setup.assert_called_once()
            call_kwargs = mock_langwatch.setup.call_args.kwargs
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["endpoint_url"] == "https://custom.langwatch.example"
            assert call_kwargs["instrumentors"] == [mock_instrumentor]
    assert langwatch_module.is_langwatch_enabled() is True


def test_trace_agent_run_noop_when_not_initialized() -> None:
    ran = False

    with trace_agent_run(uuid.uuid4(), uuid.uuid4(), "mock|user"):
        ran = True

    assert ran is True


def test_trace_agent_run_yields_when_trace_enter_fails() -> None:
    langwatch_module._langwatch_initialized = True
    run_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_langwatch = MagicMock()
    mock_langwatch.trace.side_effect = RuntimeError("export failed")

    def fake_import(
        name: str,
        globals: dict | None = None,
        locals: dict | None = None,
        fromlist: tuple = (),
        level: int = 0,
    ) -> object:
        if name == "langwatch":
            return mock_langwatch
        return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)

    with patch("agentos_chat.observability.langwatch.get_settings") as mock_settings:
        mock_settings.return_value = Settings(app_environment="local")
        with patch("builtins.__import__", side_effect=fake_import):
            ran = False
            with trace_agent_run(run_id, session_id, "mock|user"):
                ran = True
            assert ran is True
