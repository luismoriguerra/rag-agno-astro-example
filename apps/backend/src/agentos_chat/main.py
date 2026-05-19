from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentos_chat.api import messages, runs, sessions, stream
from agentos_chat.models.schemas import HealthResponse
from agentos_chat.services.logging import configure_logging
from agentos_chat.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
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


def main() -> None:
    import uvicorn

    uvicorn.run("agentos_chat.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
