# Research: WhatsApp Agent Interface

## 1. Agno WhatsApp interface integration pattern

**Decision**: Mount Agno's `Whatsapp` interface into the existing FastAPI app in `agentos_chat/main.py` using `AgentOS(agents=[...], interfaces=[Whatsapp(...)])` and include its routes on the current `app` (single process, single port). Do **not** run a separate AgentOS server.

**Rationale**: Spec clarification — mount into existing app (FR-010). Agno docs show `Whatsapp(agent=..., prefix="/whatsapp")` with webhook at `{prefix}/webhook` → `/whatsapp/webhook`. Reuses existing deployment, logging, and PostgreSQL connection.

**Alternatives considered**:
- Separate AgentOS process — rejected; doubles Railway services and complicates auth/DB.
- Custom Meta webhook handler — rejected; spec requires Agno `Whatsapp` interface class.
- Full migration to AgentOS as primary server — rejected; breaks existing REST/SSE chat API.

**Implementation notes**:
- Opt-in: only register WhatsApp routes when `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_VERIFY_TOKEN` are set; log warning otherwise.
- Build dedicated WhatsApp `Agent` sharing model/instructions with `build_search_agent()` but with `db=PostgresDb(...)`, `num_history_runs=10`, `add_history_to_context=True`.
- Pre-agent gate: custom service checks `WhatsAppSettings.enabled` and allowlist before message reaches Agno (Agno interface does not know app settings).

**Reference**: [Agno WhatsApp interface](https://docs.agno.com/agent-os/interfaces/whatsapp/introduction)

---

## 2. PostgreSQL session storage for WhatsApp

**Decision**: Use Agno PostgreSQL storage adapter (`PostgresDb` / `PgAgentStorage` per installed Agno version) with the existing `DATABASE_URL`, separate session namespace from REST `ChatSession` tables.

**Rationale**: Clarification — PostgreSQL via Agno adapter; sessions survive Railway restarts. REST chat uses custom SQLAlchemy models; WhatsApp uses Agno-managed session tables (separate namespace).

**Alternatives considered**:
- SQLite — rejected; lost on container restart without volume.
- Reuse `ChatSession` model — rejected; channel isolation and different identity model (phone vs Auth0 `sub`).

---

## 3. Webhook authentication boundary

**Decision**: Add `/whatsapp/webhook` to JWT middleware `excluded_route_paths` (alongside `/health`). Validate Meta webhooks with HMAC-SHA256 via Agno/`WHATSAPP_APP_SECRET`. Optional `WHATSAPP_SKIP_SIGNATURE_VALIDATION=true` for local ngrok only.

**Rationale**: Meta sends HMAC signatures, not Auth0 JWTs. Without exclusion, JWTMiddleware returns 401 on all webhook POSTs.

**Alternatives considered**:
- Sub-app without JWT middleware — rejected; harder to share settings DB and logging; exclusion list is simpler.

---

## 4. WhatsApp settings and allowlist (app-owned tables)

**Decision**: Add SQLAlchemy models + Alembic migration `002_whatsapp_settings`:
- `whatsapp_settings` — singleton row (`enabled` boolean, timestamps)
- `allowed_phone_numbers` — FK to settings, unique E.164 `phone_number`

Lazy-create settings on first read (`enabled=false`, empty allowlist).

**Rationale**: Profile page needs runtime toggle without redeploy. Normalized allowlist table chosen in clarification.

**Gate logic** (webhook path, before agent):
1. If `enabled=false` → return 200 to Meta, no reply (silent).
2. If allowlist non-empty and phone ∉ allowlist → silent ignore.
3. If allowlist empty → open access (when enabled).

---

## 5. Per-user message queue

**Decision**: Implement in-process per-phone queue using `asyncio.Lock` + `asyncio.Queue` keyed by normalized E.164 phone number. Send "processing..." WhatsApp reply when a second message arrives while one is in flight.

**Rationale**: Spec FR-011; personal project single-instance deployment. No Redis/Celery needed.

**Alternatives considered**:
- Parallel processing — rejected in clarification.
- Reject with "please wait" — rejected in clarification.

---

## 6. Outbound retry strategy

**Decision**: Wrap Meta send calls (or Agno outbound hook) with 3 retries, exponential backoff 2s/4s/8s; log and discard on final failure.

**Rationale**: Spec FR-013. Agno may handle send internally — add retry wrapper in WhatsApp service layer if not built-in.

---

## 7. Frontend layout and Profile page

**Decision**:
- Add `AppLayout.astro` with persistent sidebar (Home, Chat, Profile).
- Replace `index.astro` redirect with basic home page.
- Add `profile.astro` + React island `ProfileSettings.tsx` for user info + WhatsApp toggle/allowlist.
- Add `whatsappApi.ts` mirroring `chatApi.ts` auth pattern.

**Rationale**: Spec User Stories 5–6. User name/email from signed `app_session` cookie (already stores `name`); email may require Auth0 userinfo or session extension.

**Note**: If email not in session cookie, fetch from Auth0 `/userinfo` once at Profile load via BFF endpoint or extend session at callback.

---

## 8. Settings API contract

**Decision**: REST endpoints under `/api/whatsapp/settings` (JWT + `access:api`):
- `GET` — return `{ enabled, allowed_phone_numbers[] }`
- `PATCH` — update `enabled`
- `POST /api/whatsapp/settings/allowlist` — add E.164 number
- `DELETE /api/whatsapp/settings/allowlist/{phone}` — remove number

**Rationale**: Matches existing `/api/chat/*` patterns, Pydantic schemas, `Depends(get_current_identity)`.

---

## 9. Railway and local development

**Decision**:
- **Local**: `make dev` + ngrok `ngrok http 8000` → register `https://{ngrok}/whatsapp/webhook` in Meta dashboard. Set `WHATSAPP_SKIP_SIGNATURE_VALIDATION=true` optionally for dev.
- **Production**: Railway backend public URL + `/whatsapp/webhook`. Add WhatsApp env vars to `BACKEND_ENV_SYNC_KEYS` in `infra/railway/project.env`. Migration runs via existing `start.sh`.

**Rationale**: Spec assumptions + existing Railway Makefile workflow.

**Meta setup** (out of repo scope but documented in quickstart): Meta Developer App → WhatsApp → API Setup → webhook URL, verify token, subscribe to `messages` field. Use System User token for production (temp tokens expire ~24h).

---

## 10. Agent parity with REST channel

**Decision**: Reuse `build_search_agent()` factory; share OpenRouter model, DuckDuckGo tools, instructions. WhatsApp agent adds `db`, `num_history_runs=10`, session scoped by phone (`wa:{agent_name}:{phone}` per Agno convention).

**Rationale**: SC-002 parity requirement. No new tools or RAG changes (constitution N/A for RAG).

---

## 11. Observability

**Decision**: Extend structured logging in WhatsApp message handler: inbound phone (masked optional), allowlist decision, agent run outcome, outbound retry count. LangWatch traces via existing `trace_agent_run()` wrapper where applicable.

**Rationale**: Constitution V + FR-008.
