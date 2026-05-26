"""Auth0 JWT middleware helpers for FastAPI chat routes."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from agentos_chat.settings import Settings

logger = logging.getLogger(__name__)

CHAT_API_SCOPE = "access:api"

CHAT_ROUTE_PATTERNS = (
    "GET /api/chat/sessions",
    "POST /api/chat/sessions",
    "GET /api/chat/sessions/*",
    "DELETE /api/chat/sessions/*",
    "POST /api/chat/sessions/*/messages",
    "GET /api/chat/runs/*/stream",
    "POST /api/chat/runs/*/stop",
)

JWKS_REFRESH_INTERVAL_SECONDS = 3600


def build_chat_scope_mappings() -> dict[str, list[str]]:
    """Map chat API routes (METHOD + path) to the baseline API scope."""
    return {pattern: [CHAT_API_SCOPE] for pattern in CHAT_ROUTE_PATTERNS}


async def fetch_jwks_pem_keys(jwks_url: str) -> list[str]:
    """Fetch Auth0 JWKS and return PEM-encoded RSA public keys for JWTMiddleware."""
    import httpx

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        jwks_data = response.json()
    return _parse_jwks_pem_keys(jwks_data)


def fetch_jwks_pem_keys_sync(jwks_url: str) -> list[str]:
    """Synchronous JWKS fetch for application startup."""
    import httpx

    with httpx.Client(timeout=10.0) as client:
        response = client.get(jwks_url)
        response.raise_for_status()
        jwks_data = response.json()
    return _parse_jwks_pem_keys(jwks_data)


async def refresh_jwks_keys(verification_keys: list[str], jwks_url: str) -> None:
    """Replace JWKS verification keys in place for middleware hot refresh."""
    try:
        new_keys = await fetch_jwks_pem_keys(jwks_url)
        verification_keys.clear()
        verification_keys.extend(new_keys)
        logger.info("JWKS keys refreshed (%d keys)", len(new_keys))
    except Exception:  # noqa: BLE001
        logger.exception("JWKS refresh failed")


async def jwks_refresh_loop(verification_keys: list[str], jwks_url: str) -> None:
    while True:
        await asyncio.sleep(JWKS_REFRESH_INTERVAL_SECONDS)
        await refresh_jwks_keys(verification_keys, jwks_url)


def _parse_jwks_pem_keys(jwks_data: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for jwk in jwks_data.get("keys", []):
        if jwk.get("kty") != "RSA":
            continue
        pem = _jwk_to_pem(jwk)
        if pem:
            keys.append(pem)
    if not keys:
        raise ValueError("No RSA keys found in JWKS payload")
    return keys


def _jwk_to_pem(jwk: dict[str, Any]) -> str | None:
    from cryptography.hazmat.primitives import serialization
    from jwt.algorithms import RSAAlgorithm

    try:
        public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
        if not hasattr(public_key, "public_bytes"):
            return None
        pem_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem_bytes.decode()
    except Exception:
        return None


def normalize_token_scopes(raw: object) -> list[str]:
    """Expand Auth0/OIDC ``scope`` claim values into individual scope strings."""
    if isinstance(raw, str):
        return [part for part in raw.split() if part]
    if isinstance(raw, list):
        scopes: list[str] = []
        for item in raw:
            if isinstance(item, str):
                scopes.extend(part for part in item.split() if part)
        return scopes
    return []


def build_jwt_middleware_kwargs(
    settings: Settings, verification_keys: list[str] | None = None
) -> dict[str, object]:
    """Kwargs for ``app.add_middleware(JWTMiddleware, **build_jwt_middleware_kwargs(...))``."""
    jwt_kwargs: dict[str, object] = {
        "validate": True,
        "authorization": False,
        "scopes_claim": "scope",
        "verify_audience": True,
        "excluded_route_paths": ["/health"],
    }

    if settings.auth0_jwt_test_mode:
        jwt_kwargs.update(
            {
                "verification_keys": [settings.auth0_jwt_test_secret],
                "algorithm": "HS256",
                "audience": settings.auth0_api_audience or "test-audience",
            }
        )
        return jwt_kwargs

    if not verification_keys:
        raise ValueError("Auth0 JWKS verification keys are required when not in JWT test mode")

    jwt_kwargs.update(
        {
            "verification_keys": verification_keys,
            "algorithm": "RS256",
            "audience": settings.auth0_api_audience,
        }
    )
    return jwt_kwargs
