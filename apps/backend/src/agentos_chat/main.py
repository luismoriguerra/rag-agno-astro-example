from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

from agno.os.middleware import JWTMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentos_chat.api import messages, runs, sessions, stream, whatsapp_settings
from agentos_chat.auth.jwt_middleware import build_jwt_middleware_kwargs, fetch_jwks_pem_keys_sync
from agentos_chat.models.schemas import HealthResponse
from agentos_chat.observability.langwatch import configure_langwatch
from agentos_chat.services.logging import configure_logging, log_auth_failure
from agentos_chat.services.whatsapp_service import mount_whatsapp_if_configured
from agentos_chat.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    configure_langwatch()
    yield


app = FastAPI(title="AgentOS Chat Search API", version="0.1.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.auth0_jwt_test_mode:
    app.add_middleware(
        JWTMiddleware,
        **cast(Any, build_jwt_middleware_kwargs(settings)),
    )
elif settings.auth0_configured:
    _jwt_verification_keys = fetch_jwks_pem_keys_sync(settings.auth0_jwks_url)
    app.add_middleware(
        JWTMiddleware,
        **cast(Any, build_jwt_middleware_kwargs(settings, _jwt_verification_keys)),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code in (401, 403):
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        code = str(detail.get("code", "auth_failed"))
        log_auth_failure(
            status_code=exc.status_code,
            code=code,
            path=str(request.url.path),
        )
        content = detail if isinstance(exc.detail, dict) else {
            "code": "auth_failed",
            "message": str(exc.detail),
        }
        return JSONResponse(status_code=exc.status_code, content=content)
    content = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def unhandled_exception(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": str(exc)},
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


app.include_router(sessions.router)
app.include_router(messages.router)
app.include_router(stream.router)
app.include_router(runs.router)
app.include_router(whatsapp_settings.router)

mount_whatsapp_if_configured(app, settings)


def main() -> None:
    import uvicorn

    uvicorn.run("agentos_chat.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
