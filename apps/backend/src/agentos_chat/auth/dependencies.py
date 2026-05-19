"""Mock Auth0-compatible identity for local and non-production use.

Transport contract:
- Header: `X-Mock-Identity` — Auth0-style subject (must start with `mock|`).
- Falls back to `MOCK_AUTH_SUBJECT` from settings when header is absent (local dev only).

Production must replace this dependency with real Auth0 JWT validation before exposing
persisted history or agent tools.
"""

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from agentos_chat.settings import get_settings

MOCK_PREFIX = "mock|"


@dataclass(frozen=True)
class CurrentIdentity:
    auth_subject: str
    display_name: str | None = None


def _validate_mock_subject(subject: str) -> str:
    subject = subject.strip()
    if not subject.startswith(MOCK_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_identity",
                "message": "Mock identity must use the mock| prefix.",
            },
        )
    if len(subject) <= len(MOCK_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_identity", "message": "Mock identity subject is empty."},
        )
    return subject


async def get_current_identity(
    x_mock_identity: str | None = Header(default=None, alias="X-Mock-Identity"),
) -> CurrentIdentity:
    settings = get_settings()
    raw = x_mock_identity or settings.mock_auth_subject
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "missing_identity", "message": "Authentication required."},
        )
    subject = _validate_mock_subject(raw)
    return CurrentIdentity(auth_subject=subject)
