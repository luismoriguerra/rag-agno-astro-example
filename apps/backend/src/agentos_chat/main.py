import asyncio
import contextlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

from agno.os import AgentOS
from agno.os.middleware import JWTMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentos_chat.agents.research_agent import create_research_team
from agentos_chat.agents.search_agent import create_search_agent
from agentos_chat.api import (
    messages,
    research_articles,
    research_sessions,
    research_stream,
    runs,
    sessions,
    stream,
)
from agentos_chat.auth.jwt_middleware import (
    build_jwt_middleware_kwargs,
    fetch_jwks_pem_keys,
    fetch_jwks_pem_keys_sync,
    jwks_refresh_loop,
)
from agentos_chat.db.session import get_engine, get_session_factory
from agentos_chat.models.schemas import HealthResponse
from agentos_chat.observability.langwatch import configure_langwatch
from agentos_chat.services.logging import configure_logging, log_auth_failure, log_orphan_cleanup
from agentos_chat.services.orphan_cleanup import cleanup_orphaned_runs
from agentos_chat.services.run_executor import RunExecutor, set_run_executor
from agentos_chat.settings import get_settings

_settings = get_settings()
_search_agent = create_search_agent(_settings)
_research_team = create_research_team(_settings)
_jwt_verification_keys: list[str] = []


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    configure_langwatch()

    refresh_task: asyncio.Task[None] | None = None
    if _settings.auth0_configured and not _settings.auth0_jwt_test_mode:
        keys = await fetch_jwks_pem_keys(_settings.auth0_jwks_url)
        _jwt_verification_keys.clear()
        _jwt_verification_keys.extend(keys)
        refresh_task = asyncio.create_task(
            jwks_refresh_loop(_jwt_verification_keys, _settings.auth0_jwks_url)
        )

    factory = get_session_factory()
    async with factory() as db:
        chat_cleaned, research_cleaned = await cleanup_orphaned_runs(db)
        await db.commit()
        log_orphan_cleanup(chat_cleaned, research_cleaned)

    executor = RunExecutor(
        search_agent=_search_agent,
        research_team=_research_team,
        settings=_settings,
    )
    set_run_executor(executor)
    app.state.run_executor = executor

    yield

    if refresh_task is not None:
        refresh_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await refresh_task

    engine = get_engine()
    await engine.dispose()


def _create_base_app() -> FastAPI:
    base = FastAPI(title="AgentOS Chat Search API", version="0.1.0", lifespan=lifespan)

    base.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if _settings.auth0_jwt_test_mode:
        base.add_middleware(
            JWTMiddleware,
            **cast(Any, build_jwt_middleware_kwargs(_settings)),
        )
    elif _settings.auth0_configured:
        if not _jwt_verification_keys:
            _jwt_verification_keys.extend(fetch_jwks_pem_keys_sync(_settings.auth0_jwks_url))
        base.add_middleware(
            JWTMiddleware,
            **cast(Any, build_jwt_middleware_kwargs(_settings, _jwt_verification_keys)),
        )

    @base.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code in (401, 403):
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            code = str(detail.get("code", "auth_failed"))
            log_auth_failure(
                status_code=exc.status_code,
                code=code,
                path=str(request.url.path),
            )
            content = (
                detail
                if isinstance(exc.detail, dict)
                else {
                    "code": "auth_failed",
                    "message": str(exc.detail),
                }
            )
            return JSONResponse(status_code=exc.status_code, content=content)
        content = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=content)

    @base.exception_handler(Exception)
    async def unhandled_exception(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": str(exc)},
        )

    @base.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse()

    base.include_router(sessions.router)
    base.include_router(messages.router)
    base.include_router(stream.router)
    base.include_router(runs.router)
    base.include_router(research_sessions.router)
    base.include_router(research_stream.router)
    base.include_router(research_articles.router)

    return base


_base_app = _create_base_app()
_agent_os = AgentOS(
    agents=[_search_agent],
    teams=[_research_team],
    base_app=_base_app,
    auto_provision_dbs=True,
    telemetry=_settings.agno_telemetry,
    on_route_conflict="preserve_base_app",
)
app = _agent_os.get_app()


def main() -> None:
    import uvicorn

    uvicorn.run("agentos_chat.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
