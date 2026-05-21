# Contract: WhatsApp Settings API

## Purpose

Authenticated REST API for managing global WhatsApp configuration from the Profile page. Protected by Auth0 Bearer JWT with `access:api` scope (same as `/api/chat/*`).

## Security Scheme

```yaml
components:
  securitySchemes:
    Auth0Bearer:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

All routes: `security: [Auth0Bearer: []]`

## Base Path

`/api/whatsapp/settings`

## Endpoints

### GET `/api/whatsapp/settings`

Return current global WhatsApp settings (lazy-create if missing).

**Response 200**:

```json
{
  "enabled": false,
  "allowed_phone_numbers": [
    { "phone_number": "+14155552671", "created_at": "2026-05-19T12:00:00Z" }
  ]
}
```

### PATCH `/api/whatsapp/settings`

Update enabled toggle.

**Request**:

```json
{ "enabled": true }
```

**Response 200**: Same shape as GET.

### POST `/api/whatsapp/settings/allowlist`

Add phone number to allowlist.

**Request**:

```json
{ "phone_number": "+14155552671" }
```

**Validation**: E.164 format required.

**Response 201**: Updated settings object.

**Errors**:
- `400` — invalid format
- `409` — duplicate phone number

### DELETE `/api/whatsapp/settings/allowlist/{phone_number}`

Remove phone from allowlist. Path param URL-encoded E.164 (e.g. `%2B14155552671`).

**Response 200**: Updated settings object.

**Errors**:
- `404` — phone not in allowlist

## Error Body (consistent with chat API)

```json
{
  "code": "invalid_phone_number" | "duplicate_phone" | "not_found" | "insufficient_scope",
  "message": "Human-readable message"
}
```

## Authorization

| Check | Failure |
|-------|---------|
| Missing/invalid JWT | 401 |
| Missing `access:api` scope | 403 |

No per-user ownership filter — global singleton; any authenticated user with API scope may read/update.

## Frontend Usage

`apps/frontend/src/services/whatsappApi.ts`:

- Uses `authFetch()` from existing pattern (Bearer via `/api/auth/access-token`).
- Called from Profile page React island.

## OpenAPI Update Scope

Extend backend OpenAPI / contract docs with `/api/whatsapp/*` paths alongside existing `/api/chat/*`.
