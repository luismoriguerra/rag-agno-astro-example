from agentos_chat.auth.jwt_middleware import (
    CHAT_API_SCOPE,
    build_chat_scope_mappings,
    normalize_token_scopes,
)


def test_build_chat_scope_mappings_includes_chat_routes() -> None:
    mappings = build_chat_scope_mappings()
    assert mappings["GET /api/chat/sessions"] == [CHAT_API_SCOPE]
    assert mappings["POST /api/chat/sessions"] == [CHAT_API_SCOPE]


def test_chat_api_scope_constant() -> None:
    assert CHAT_API_SCOPE == "access:api"


def test_normalize_token_scopes_splits_auth0_scope_string() -> None:
    scopes = normalize_token_scopes("openid profile email access:api offline_access")
    assert scopes == ["openid", "profile", "email", "access:api", "offline_access"]


def test_normalize_token_scopes_splits_list_wrapped_string() -> None:
    scopes = normalize_token_scopes(["openid profile email access:api"])
    assert "access:api" in scopes
