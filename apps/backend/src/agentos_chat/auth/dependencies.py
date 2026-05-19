"""Auth0 JWT identity dependency for protected chat routes."""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.jwt_middleware import CHAT_API_SCOPE, normalize_token_scopes
from agentos_chat.db.repositories import get_or_create_identity
from agentos_chat.db.session import get_db_session


@dataclass(frozen=True)
class CurrentIdentity:
    auth_subject: str
    display_name: str | None = None


def _extract_subject(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return str(user_id)

    jwt_payload = getattr(request.state, "jwt_payload", None)
    if isinstance(jwt_payload, dict) and jwt_payload.get("sub"):
        return str(jwt_payload["sub"])

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "missing_identity", "message": "Authentication required."},
    )


def _require_chat_api_scope(request: Request) -> None:
    scopes = normalize_token_scopes(getattr(request.state, "scopes", []))
    if CHAT_API_SCOPE not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "insufficient_scope",
                "message": "Insufficient permissions",
            },
        )


async def get_current_identity(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> CurrentIdentity:
    _require_chat_api_scope(request)
    subject = _extract_subject(request)
    name_claim = getattr(request.state, "name", None)
    display_name = str(name_claim) if name_claim else None
    await get_or_create_identity(db, auth_subject=subject, display_name=display_name)
    return CurrentIdentity(auth_subject=subject, display_name=display_name)
