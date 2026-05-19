# Data Model: Auth0 Integration

## Overview

No new PostgreSQL tables or migrations. Auth0 is the identity provider; `UserIdentity.auth_subject` binds to Auth0 `sub`. Mock subjects (`mock|*`) are legacy rows only — not visible to Auth0-authenticated users.

## External Entities (Auth0 — Terraform-managed)

### Auth0ApiResource

| Attribute | Source | Notes |
|-----------|--------|-------|
| `identifier` | `auth0_resource_server.*.identifier` | API audience / `aud` claim |
| `name` | Terraform variable | Display name |
| `signing_alg` | `RS256` | Matches backend JWT validation |
| `scopes` | `access:api` | Baseline backend scope |

### Auth0SpaClient

| Attribute | Source | Notes |
|-----------|--------|-------|
| `client_id` | Terraform output | Public frontend config |
| `callback_urls` | localhost + Railway frontend URL | Includes `/api/auth/callback` |
| `logout_urls` | localhost + Railway frontend URL | Federated logout return |
| `web_origins` | CORS for Auth0 silent auth |
| `grant_types` | `authorization_code`, `refresh_token` |

### Auth0AllowlistAction

| Attribute | Source | Notes |
|-----------|--------|-------|
| `trigger` | `post-login` | Blocks before token issuance |
| `allowed_emails` | Terraform list variable | Initial: `luismoridev@gmail.com` |
| `deploy` | `true` | Managed by Terraform apply |

### Auth0GoogleConnection

| Attribute | Notes |
|-----------|-------|
| `strategy` | `google-oauth2` |
| `enabled_clients` | SPA client only |

## Runtime Configuration (not in app DB)

### BackendAuthSettings

| Field | Env var | Required |
|-------|---------|----------|
| `auth0_domain` | `AUTH0_DOMAIN` | Yes |
| `auth0_issuer` | `AUTH0_ISSUER` | Yes (`https://{domain}/`) |
| `auth0_api_audience` | `AUTH0_API_AUDIENCE` | Yes |
| `auth0_jwks_url` | Derived | `{issuer}.well-known/jwks.json` |

Removed: `mock_auth_subject`.

### FrontendAuthSettings

| Field | Env var | Required |
|-------|---------|----------|
| `auth0_domain` | `PUBLIC_AUTH0_DOMAIN` | Yes |
| `auth0_client_id` | `PUBLIC_AUTH0_CLIENT_ID` | Yes |
| `auth0_audience` | `PUBLIC_AUTH0_AUDIENCE` | Yes |
| `api_base_url` | `PUBLIC_AGENTOS_API_BASE_URL` | Yes |
| `session_secret` | `AUTH0_SECRET` | Yes — signs httpOnly session cookie for Astro middleware |

Removed: `PUBLIC_MOCK_IDENTITY`.

## Unchanged Persistent Entities

From `specs/001-agentos-chat-search/data-model.md`:

### UserIdentity

| Field | Auth0 integration |
|-------|-------------------|
| `auth_subject` | Auth0 `sub` (e.g. `google-oauth2|1023...`) |
| `display_name` | Optional; from token `name` or email on first request |

**Lazy provisioning** (FR-007): `get_or_create_identity(db, auth_subject=sub)` on first authenticated API call — already implemented in `repositories.py`.

### ChatSession / ChatMessage / AgentRun

No schema changes. Owner filtering continues via `user_identity_id` resolved from JWT `sub`.

## Identity Lifecycle

```text
Google sign-in (Auth0 Action allowlist pass)
  → SPA obtains access token (audience = API, scope = access:api)
  → First API request with Bearer token
  → JWTMiddleware validates + scope check
  → get_or_create_identity(sub)
  → Chat operations scoped to user_identity_id
```

## Legacy Mock Data

| State | Behavior |
|-------|----------|
| Rows with `auth_subject` like `mock|*` | Remain in DB |
| Auth0 user queries | Filter by real `sub` only; no mock rows returned |
| Migration | None (clean break per clarification) |

## Validation Rules

- Access tokens MUST include `aud` matching `AUTH0_API_AUDIENCE`.
- Access tokens MUST include `access:api` in `scope` (or configured `scopes_claim`).
- `auth_subject` MUST NOT be accepted from client headers after mock removal.
- Email allowlist enforced only at Auth0 login — backend does not re-check email (FR-028).
