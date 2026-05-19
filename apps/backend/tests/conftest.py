import os

# JWT test mode must be set before importing the FastAPI app (middleware registration).
os.environ.setdefault("AUTH0_JWT_TEST_MODE", "true")
os.environ.setdefault("AUTH0_API_AUDIENCE", "test-audience")
os.environ.setdefault("APP_ENVIRONMENT", "test")

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agentos_chat.db.models import Base
from agentos_chat.db.session import get_db_session
from agentos_chat.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/agentos_chat_test",
)

TEST_JWT_SECRET = os.getenv(
    "AUTH0_JWT_TEST_SECRET",
    "test-jwt-secret-at-least-32-characters-long",
)
TEST_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "test-audience")


def make_test_jwt(
    *,
    sub: str = "auth0|test-user",
    scope: str = "access:api",
    audience: str = TEST_AUDIENCE,
    secret: str = TEST_JWT_SECRET,
    expires_in_hours: int = 1,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "scope": scope,
        "aud": audience,
        "exp": now + timedelta(hours=expires_in_hours),
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = make_test_jwt()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_no_scope() -> dict[str, str]:
    token = make_test_jwt(scope="")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    """Backward-compatible alias for contract tests."""
    return auth_headers
