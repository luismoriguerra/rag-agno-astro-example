# Implementation Plan: WhatsApp Agent Interface

**Branch**: `004-whatsapp-agent-interface` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-whatsapp-agent-interface/spec.md`

## Summary

Expose the existing search agent via WhatsApp by mounting Agno's `Whatsapp` interface into the current FastAPI backend at `/whatsapp/webhook`, with PostgreSQL-backed sessions, runtime settings (enable toggle + phone allowlist) managed from a new Astro Profile page, and sidebar navigation with a home page. WhatsApp is opt-in via env vars; webhook is JWT-excluded and HMAC-validated.

## Technical Context

**Language/Version**: Python 3.12 (backend); Node.js 22 + TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Agno/AgentOS (`Whatsapp` interface, `PostgresDb`), Astro SSR, Auth0 JWT middleware, SQLAlchemy 2 + Alembic, Pydantic v2
**Storage**: PostgreSQL — existing chat tables unchanged; new `whatsapp_settings` + `allowed_phone_numbers`; Agno-managed WhatsApp session tables
**Testing**: pytest (backend), frontend unit tests; manual WhatsApp + Meta webhook verification
**Target Platform**: Railway (Linux containers); local via Docker Postgres + ngrok
**Project Type**: RAG web application (FastAPI backend + Astro frontend)
**Performance Goals**: WhatsApp reply within 60 seconds (SC-001); agent parity with REST channel (SC-002)
**Constraints**: Single-instance in-process message queue; text-only v1; no phone encryption v1; opt-in WhatsApp mount
**Scale/Scope**: Personal project; global singleton settings; small allowlist (<20 numbers)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-design (PASS)

| Gate | Status | Notes |
|------|--------|-------|
| **Grounded RAG and Agent Behavior** | PASS (N/A) | Reuses existing DuckDuckGo search agent; no new retrieval sources. Same tool permissions and instructions. LangWatch traces via existing wrapper. |
| **Auth0-Centered Security Boundaries** | PASS | Settings API: Auth0 JWT + `access:api`. Webhook: HMAC-only, JWT excluded. Phone identity separate from Auth0 `sub`. |
| **Typed API and UI Contracts** | PASS | New Pydantic schemas for settings API; contracts in `contracts/`. Profile page handles loading/error/validation states. |
| **PostgreSQL and pgvector Integrity** | PASS | Alembic migration for settings tables only; no pgvector. Agno sessions in separate namespace. Lazy-init singleton. |
| **Railway-Ready Delivery and Observability** | PASS | Env vars documented; migration via `start.sh`; structured logs for WhatsApp events; quickstart verification steps. |

### Post-design (PASS)

No constitution violations. WhatsApp channel intentionally bypasses Auth0 for inbound Meta webhooks — documented exception with HMAC substitute. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/004-whatsapp-agent-interface/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── whatsapp-webhook-api.md
│   └── whatsapp-settings-api.md
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
apps/backend/
├── migrations/versions/
│   └── 002_whatsapp_settings.py          # NEW
├── src/agentos_chat/
│   ├── main.py                           # Mount WhatsApp routes; JWT exclude
│   ├── settings.py                       # WhatsApp env vars
│   ├── agents/
│   │   ├── search_agent.py               # Shared factory (reuse)
│   │   └── whatsapp_agent.py             # NEW — Agent + PostgresDb config
│   ├── api/
│   │   └── whatsapp_settings.py          # NEW — settings CRUD router
│   ├── auth/
│   │   └── jwt_middleware.py             # Add /whatsapp/webhook exclusion
│   ├── db/
│   │   ├── models.py                     # WhatsAppSettings, AllowedPhoneNumber
│   │   └── whatsapp_settings_repository.py  # NEW
│   ├── models/
│   │   └── schemas.py                    # WhatsApp settings Pydantic models
│   ├── services/
│   │   ├── whatsapp_gate.py              # NEW — enabled/allowlist check
│   │   ├── whatsapp_queue.py             # NEW — per-phone sequential queue
│   │   └── whatsapp_service.py           # NEW — mount + message orchestration
│   └── interfaces/
│       └── whatsapp_mount.py             # NEW — Agno Whatsapp interface wiring
└── tests/
    ├── unit/test_whatsapp_gate.py        # NEW
    ├── unit/test_whatsapp_settings_api.py # NEW
    └── integration/test_whatsapp_webhook.py # NEW

apps/frontend/
├── src/
│   ├── layouts/
│   │   └── AppLayout.astro               # NEW — sidebar shell
│   ├── components/
│   │   ├── Sidebar.astro                 # NEW
│   │   ├── ProfileSettings.tsx           # NEW — React island
│   │   └── ChatBox.tsx                   # Wrap in AppLayout
│   ├── pages/
│   │   ├── index.astro                   # Home page (replace redirect)
│   │   ├── chat.astro                    # Use AppLayout
│   │   └── profile.astro                 # NEW
│   └── services/
│       ├── whatsappApi.ts                # NEW
│       └── whatsappTypes.ts              # NEW

infra/railway/
└── project.env                           # Add WhatsApp keys to BACKEND_ENV_SYNC_KEYS
```

**Structure Decision**: Extends existing monorepo layout (`apps/backend`, `apps/frontend`, `infra/railway`). No new services on Railway — WhatsApp routes live on `agentos-chat-backend`.

## Implementation Phases

### Phase A — Backend foundation (blocking)

1. **Settings schema**: Add SQLAlchemy models + Alembic `002_whatsapp_settings` migration.
2. **Settings repository**: Lazy-create singleton; CRUD for allowlist with E.164 validation.
3. **Settings API**: Router `/api/whatsapp/settings` with GET/PATCH/POST allowlist/DELETE allowlist; JWT + `access:api`.
4. **Settings tests**: Unit tests for validation, lazy init, duplicate phone 409.

### Phase B — WhatsApp interface (P1 core)

5. **Settings/env**: Extend `Settings` with WhatsApp env vars + `whatsapp_configured` property.
6. **JWT exclusion**: Add `/whatsapp/webhook` to `excluded_route_paths`.
7. **WhatsApp agent**: `build_whatsapp_agent()` — shared model/tools, `PostgresDb`, `num_history_runs=10`.
8. **Gate service**: Check `enabled` + allowlist before agent invocation; silent ignore paths.
9. **Queue service**: Per-phone `asyncio` queue + "processing..." acknowledgment.
10. **Mount Agno interface**: `whatsapp_mount.py` — opt-in when env vars set; wire gate + queue around Agno handler.
11. **Retry wrapper**: 3× exponential backoff on outbound send failures.
12. **Logging**: Structured events for inbound/outbound/gate/retry.
13. **Webhook tests**: Signature validation, verify challenge, gate behavior (disabled, allowlist).

### Phase C — Frontend shell (P2, parallel after Phase A)

14. **AppLayout + Sidebar**: Persistent nav (Home, Chat, Profile) on all authenticated pages.
15. **Home page**: Replace `index.astro` redirect with basic landing content.
16. **Profile page**: User name/email from session; WhatsApp toggle + allowlist UI.
17. **whatsappApi.ts**: Typed client mirroring `chatApi.ts` auth pattern.
18. **Wire chat page**: Wrap existing `ChatBox` in `AppLayout`.

### Phase D — Deployment & docs

19. **Railway**: Add WhatsApp env keys to `BACKEND_ENV_SYNC_KEYS`; document in `infra/railway/README.md`.
20. **Backend `.env.example`**: Document all WhatsApp variables.
21. **Manual E2E**: Meta webhook + real WhatsApp message per quickstart checklist.

## Key Design Decisions

| Decision | Choice | Reference |
|----------|--------|-----------|
| Integration pattern | Mount Agno `Whatsapp` into existing FastAPI | research.md §1 |
| Session storage | Agno PostgreSQL adapter | research.md §2 |
| Settings storage | App-owned tables, lazy singleton | data-model.md |
| Webhook auth | JWT excluded; HMAC validated | contracts/whatsapp-webhook-api.md |
| Allowlist empty | Open access when enabled | spec FR-017 |
| Non-allowlisted | Silent ignore | spec clarification |
| Graceful degradation | Opt-in env var mount | spec FR-010 |
| Message concurrency | Per-phone queue | research.md §5 |

## Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Agno mount API differs from docs | Spike in Phase B step 10; fallback to manual router if needed |
| Temporary Meta token expires | Document System User token in quickstart; log clear error on 401 send |
| Email not in session cookie | Extend Auth0 callback to store email or add BFF `/api/auth/me` |
| Agno creates its own DB tables | Verify on first run; document in migration notes if manual DDL needed |
| WhatsApp message length limits | Truncate/split long agent replies in service layer if needed |

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | [research.md](./research.md) | Complete |
| Data model | [data-model.md](./data-model.md) | Complete |
| Webhook contract | [contracts/whatsapp-webhook-api.md](./contracts/whatsapp-webhook-api.md) | Complete |
| Settings contract | [contracts/whatsapp-settings-api.md](./contracts/whatsapp-settings-api.md) | Complete |
| Quickstart | [quickstart.md](./quickstart.md) | Complete |
| Tasks | [tasks.md](./tasks.md) | Complete |
| Checklists | [checklists/](./checklists/) | Complete |

## Next Step

Run `/speckit.implement` to execute tasks from `tasks.md`, starting with Phase 1 (Setup) and Phase 2 (Foundational).
