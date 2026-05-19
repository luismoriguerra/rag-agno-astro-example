# Contract: Authenticated Chat API Security

## Purpose

Replaces the mock `X-Mock-Identity` security scheme from `specs/001-agentos-chat-search/contracts/openapi.yaml` with Auth0 Bearer JWT access tokens.

## Security Scheme

```yaml
components:
  securitySchemes:
    Auth0Bearer:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: >
        Auth0 access token for the application API (audience = AUTH0_API_AUDIENCE,
        scope includes access:api). Obtained by the frontend via Auth0 SPA SDK after
        Google Universal Login.
```

All `/api/chat/*` operations use `security: [Auth0Bearer: []]` instead of `MockIdentity`.

`/health` remains unsecured.

## Request Headers

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes (protected routes) | `Bearer {access_token}` |
| `Content-Type` | Yes (JSON bodies) | `application/json` |

**Removed**: `X-Mock-Identity`

## Token Validation (backend)

Agno `JWTMiddleware` + FastAPI identity dependency:

| Check | Failure HTTP status |
|-------|---------------------|
| Missing/invalid signature | 401 Unauthorized |
| Wrong issuer | 401 |
| Wrong audience | 401 |
| Expired | 401 |
| Missing `access:api` scope | 403 Forbidden |

Structured error body (unchanged pattern):

```json
{
  "code": "missing_identity" | "invalid_token" | "insufficient_scope",
  "message": "Human-readable message without secrets"
}
```

## Identity Resolution

| Claim | Usage |
|-------|-------|
| `sub` | `UserIdentity.auth_subject` (lazy create) |
| `scope` | Must include `access:api` |
| `aud` | Must match `AUTH0_API_AUDIENCE` |

Email claim is **not** validated on backend (allowlist at Auth0 Action only).

## Frontend Token Lifecycle

1. User completes Google login via Universal Login.
2. SPA SDK caches tokens; attaches `Authorization` on all `chatApi` fetch/SSE calls.
3. On 401: silent refresh once → retry request once → prompt re-auth (FR-015).
4. SSE stream uses same Bearer header on initial connection.

## Public Frontend Routes (no Bearer required)

- `/api/auth/login`, `/api/auth/callback`, `/api/auth/logout`
- Static assets under `/_astro/*`, `/favicon.*`, etc.
- Backend `/health`

## OpenAPI Update Scope

During implementation, update `specs/001-agentos-chat-search/contracts/openapi.yaml` or add `specs/003-auth0-integration/contracts/openapi-auth0.yaml` overlay documenting the security scheme change for contract tests.
