# Contract: WhatsApp Webhook API

## Purpose

Meta WhatsApp Cloud API webhook endpoint mounted at `/whatsapp/webhook` on the backend FastAPI service. **Not** protected by Auth0 JWT; secured by Meta verify token (GET) and HMAC-SHA256 (POST).

## Endpoints

### GET `/whatsapp/webhook` — Verification

Meta subscription verification challenge.

| Query param | Required | Description |
|-------------|----------|-------------|
| `hub.mode` | Yes | Must be `subscribe` |
| `hub.verify_token` | Yes | Must match `WHATSAPP_VERIFY_TOKEN` |
| `hub.challenge` | Yes | Echo back on success |

**Response**: `200` with challenge string body (plain text).

**Errors**: `403` if verify token mismatch.

### POST `/whatsapp/webhook` — Message delivery

Inbound events from Meta (messages, statuses).

| Header | Required | Description |
|--------|----------|-------------|
| `X-Hub-Signature-256` | Yes (prod) | `sha256={hmac}` of raw body with `WHATSAPP_APP_SECRET` |

**Pre-processing gate** (before Agno agent):

1. Validate signature (unless `WHATSAPP_SKIP_SIGNATURE_VALIDATION=true`).
2. Load `WhatsAppSettings` (lazy create if missing).
3. If `enabled=false` → return `200`, no agent call, no outbound message.
4. Extract sender phone (E.164); if allowlist non-empty and phone not listed → return `200`, silent ignore.
5. If empty/whitespace text → ignore.
6. If `/new` → delegate to Agno session reset.
7. Else queue message per phone and process with search agent.
8. On agent failure or timeout (60s), send FR-007 default error text via WhatsApp (no stack traces).

**Response**: `200` to acknowledge receipt (Meta retries on non-2xx).

**Errors**:
- `403` — invalid signature
- `500` — `WHATSAPP_APP_SECRET` missing and skip flag false

## JWT Middleware Exclusion

```text
excluded_route_paths: ["/health", "/whatsapp/webhook"]
```

## Environment Variables

| Variable | Required for mount | Description |
|----------|-------------------|-------------|
| `WHATSAPP_ACCESS_TOKEN` | Yes | Meta Graph API token |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes | Sending phone number ID |
| `WHATSAPP_VERIFY_TOKEN` | Yes | Webhook verification string |
| `WHATSAPP_APP_SECRET` | Prod | HMAC validation |
| `WHATSAPP_SKIP_SIGNATURE_VALIDATION` | No | Dev only; default false |

## Production Callback URL

```text
https://{RAILWAY_BACKEND_HOST}/whatsapp/webhook
```

Register in Meta App Dashboard → WhatsApp → Configuration.

## Outbound Behavior

- Agent reply sent as WhatsApp text message via Meta Graph API (via Agno interface).
- Retry failed sends 3× with backoff 2s, 4s, 8s.
- Queued concurrent messages: send "processing..." acknowledgment.

## Logging (structured)

Log fields (no raw tokens): `event=whatsapp_inbound|whatsapp_outbound|whatsapp_gate|whatsapp_error`, `phone` (optional mask), `allowed`, `enabled`, `retry_count`.
