# Tasks: WhatsApp Agent Interface

**Input**: Design documents from `/specs/004-whatsapp-agent-interface/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Backend unit/integration tests included for settings API, webhook security, gate logic, and session behavior per plan (security and database boundary changes).

**Organization**: Tasks grouped by user story (US1–US6) with shared foundation first.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US6 maps to spec user stories
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment scaffolding and dependency verification.

- [x] T001 [P] Add WhatsApp environment variables to `apps/backend/.env.example` per `specs/004-whatsapp-agent-interface/quickstart.md`
- [x] T002 [P] Add WhatsApp keys to `BACKEND_ENV_SYNC_KEYS` in `infra/railway/project.env`
- [x] T003 Verify Agno `Whatsapp` interface and PostgreSQL storage adapter dependencies in `apps/backend/pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Settings schema, API, and JWT webhook exclusion — required before WhatsApp messaging or Profile UI.

**CRITICAL**: No user story work until this phase completes.

- [x] T004 Add `WhatsAppSettings` and `AllowedPhoneNumber` SQLAlchemy models to `apps/backend/src/agentos_chat/db/models.py`
- [x] T005 Create Alembic migration `002_whatsapp_settings.py` in `apps/backend/migrations/versions/`
- [x] T006 Implement lazy singleton and allowlist CRUD with E.164 validation in `apps/backend/src/agentos_chat/db/whatsapp_settings_repository.py`
- [x] T007 [P] Add WhatsApp settings Pydantic schemas to `apps/backend/src/agentos_chat/models/schemas.py`
- [x] T008 Implement settings router (GET/PATCH/POST allowlist/DELETE) in `apps/backend/src/agentos_chat/api/whatsapp_settings.py` per `contracts/whatsapp-settings-api.md`
- [x] T009 Register WhatsApp settings router in `apps/backend/src/agentos_chat/main.py`
- [x] T010 Extend `Settings` with WhatsApp env vars and `whatsapp_configured` property in `apps/backend/src/agentos_chat/settings.py`
- [x] T011 Add `/whatsapp/webhook` to `excluded_route_paths` in `apps/backend/src/agentos_chat/auth/jwt_middleware.py`
- [x] T012 [P] Add unit tests for settings repository and E.164 validation in `apps/backend/tests/unit/test_whatsapp_settings_repository.py`
- [x] T013 [P] Add integration tests for settings API auth and CRUD in `apps/backend/tests/integration/test_whatsapp_settings_api.py`

**Checkpoint**: Settings API works; migration applied; webhook path JWT-excluded. Enable bot via `PATCH /api/whatsapp/settings` for downstream tests.

---

## Phase 3: User Story 1 - Send a Question via WhatsApp (Priority: P1) MVP

**Goal**: User sends a WhatsApp text message and receives an agent reply within 60 seconds.

**Independent Test**: Enable WhatsApp via settings API; send "What is the capital of France?" to bot number; receive relevant text reply with sources when applicable.

### Tests for User Story 1

- [x] T014 [P] [US1] Add integration tests for webhook message handling and agent reply in `apps/backend/tests/integration/test_whatsapp_webhook.py`

### Implementation for User Story 1

- [x] T015 [P] [US1] Create `build_whatsapp_agent()` with shared search config, `PostgresDb`, `num_history_runs=10` in `apps/backend/src/agentos_chat/agents/whatsapp_agent.py`
- [x] T016 [P] [US1] Implement enabled/allowlist gate service in `apps/backend/src/agentos_chat/services/whatsapp_gate.py`
- [x] T017 [P] [US1] Implement per-phone sequential queue with "processing..." ack in `apps/backend/src/agentos_chat/services/whatsapp_queue.py`
- [x] T018 [US1] Implement Agno `Whatsapp` interface mount with opt-in credential check in `apps/backend/src/agentos_chat/interfaces/whatsapp_mount.py`
- [x] T019 [US1] Implement message orchestration with 3× retry backoff in `apps/backend/src/agentos_chat/services/whatsapp_service.py`
- [x] T020 [US1] Wire opt-in WhatsApp mount and startup warning in `apps/backend/src/agentos_chat/main.py`
- [x] T021 [US1] Add structured WhatsApp inbound/outbound/gate/retry log events in `apps/backend/src/agentos_chat/services/logging.py`
- [ ] T022 [US1] Manual verification: send WhatsApp message and receive reply per `specs/004-whatsapp-agent-interface/quickstart.md` section 6

**Checkpoint**: MVP — WhatsApp bot answers questions when enabled. REST `/chat` unaffected (SC-006).

---

## Phase 4: User Story 3 - Webhook Security and Verification (Priority: P2)

**Goal**: Meta webhook verification and HMAC-SHA256 signature validation; invalid signatures rejected.

**Note**: FR-001 and FR-002 are **implemented** in US1 (T018 mount). Phase 4 adds tests and manual verification — do not defer security wiring to this phase.

**Independent Test**: GET verify challenge returns 200; POST with bad signature returns 403; dev skip flag works locally.

### Tests for User Story 3

- [x] T023 [P] [US3] Add unit tests for verify-token challenge and HMAC signature rejection in `apps/backend/tests/unit/test_whatsapp_webhook_security.py`

### Implementation for User Story 3

- [x] T024 [US3] Document `WHATSAPP_SKIP_SIGNATURE_VALIDATION` dev-only usage in `apps/backend/.env.example`
- [ ] T025 [US3] Manual verification: Meta webhook verify flow and invalid signature rejection per `specs/004-whatsapp-agent-interface/contracts/whatsapp-webhook-api.md`

**Checkpoint**: Webhook security meets FR-001/FR-002/SC-005.

---

## Phase 5: User Story 2 - Conversation History within a Session (Priority: P2)

**Goal**: Multi-turn WhatsApp conversations retain context for follow-up questions.

**Independent Test**: Ask "Who is the president of France?" then "What is his age?" — second answer resolves pronoun correctly.

### Tests for User Story 2

- [x] T026 [P] [US2] Add integration test for multi-turn context in `apps/backend/tests/integration/test_whatsapp_session_context.py`

### Implementation for User Story 2

- [x] T027 [US2] Confirm 10-exchange context window and session persistence in `apps/backend/src/agentos_chat/agents/whatsapp_agent.py`
- [ ] T028 [US2] Manual verification: follow-up question resolves prior context per spec User Story 2

**Checkpoint**: Context-aware multi-turn WhatsApp Q&A works (SC-003).

---

## Phase 6: User Story 4 - Start a New Session (Priority: P3)

**Goal**: User sends `/new` in WhatsApp to reset conversation context.

**Independent Test**: Send message, send `/new`, ask question — bot does not reference prior conversation.

### Tests for User Story 4

- [x] T029 [P] [US4] Add integration test for `/new` session isolation in `apps/backend/tests/integration/test_whatsapp_new_session.py`

### Implementation for User Story 4

- [x] T030 [US4] Verify Agno `/new` command handling preserves old session in `apps/backend/src/agentos_chat/interfaces/whatsapp_mount.py`
- [ ] T031 [US4] Manual verification: `/new` resets context per spec User Story 4 (SC-004)

**Checkpoint**: Session reset via `/new` works; prior session data preserved.

---

## Phase 7: User Story 5 - Manage WhatsApp Settings via Profile Page (Priority: P2)

**Goal**: Profile page shows user info and WhatsApp toggle + phone allowlist management.

**FR-019 dependency**: Settings functionality (T033–T038) is independently testable at `/profile`. Sidebar on Profile per FR-019 requires US6 AppLayout (T039–T040) and profile wrap (T043). Execute frontend track as **US6 layout → US5 profile → T043 wrap**.

**Independent Test**: Log in → Profile (direct `/profile` or via sidebar after T043) → toggle enable → add phone → only that number receives bot replies.

### Tests for User Story 5

- [x] T032 [P] [US5] Add frontend unit tests for whatsappApi and E.164 validation in `apps/frontend/tests/whatsapp-settings.test.ts`

### Implementation for User Story 5

- [x] T033 [P] [US5] Create TypeScript types in `apps/frontend/src/services/whatsappTypes.ts`
- [x] T034 [P] [US5] Create authenticated API client in `apps/frontend/src/services/whatsappApi.ts`
- [x] T035 [P] [US5] Create `ProfileSettings.tsx` React island with toggle and allowlist UI in `apps/frontend/src/components/ProfileSettings.tsx`
- [x] T036 [US5] Extend Auth0 callback session to include email for Profile display in `apps/frontend/src/pages/api/auth/callback.ts`
- [x] T037 [US5] Create Profile page with user info header and WhatsApp section in `apps/frontend/src/pages/profile.astro`
- [ ] T038 [US5] Manual verification: Profile toggle and allowlist control bot access per spec User Story 5

**Checkpoint**: Self-service WhatsApp settings via UI (T038). **FR-019 complete** when Profile is wrapped in AppLayout with sidebar (T043 after T039–T040).

---

## Phase 8: User Story 6 - Sidebar Navigation and Home Page (Priority: P2)

**Goal**: Persistent sidebar with Home, Chat, Profile links; home page replaces redirect.

**Independent Test**: Visit `/` → see landing page with sidebar; navigate to Chat and Profile.

### Implementation for User Story 6

- [x] T039 [P] [US6] Create `Sidebar.astro` navigation component in `apps/frontend/src/components/Sidebar.astro`
- [x] T040 [P] [US6] Create `AppLayout.astro` shell with sidebar in `apps/frontend/src/layouts/AppLayout.astro`
- [x] T041 [US6] Replace redirect with basic home landing page in `apps/frontend/src/pages/index.astro`
- [x] T042 [US6] Wrap chat page with AppLayout in `apps/frontend/src/pages/chat.astro`
- [x] T043 [US6] Wrap profile page with AppLayout in `apps/frontend/src/pages/profile.astro`
- [ ] T044 [US6] Manual verification: sidebar navigation across Home, Chat, Profile per spec User Story 6

**Checkpoint**: Full frontend navigation shell complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Deployment docs, gate tests, regression checks, end-to-end validation.

- [x] T045 [P] Add unit tests for gate allowlist and silent-ignore logic in `apps/backend/tests/unit/test_whatsapp_gate.py`
- [x] T046 [P] Update WhatsApp deployment section in `infra/railway/README.md`
- [x] T047 Run `make check` and `make test` for backend and frontend (covers SC-006 automated scope)
- [ ] T048 Manual E2E: complete `specs/004-whatsapp-agent-interface/quickstart.md` checklist including ngrok local and Railway production webhook
- [ ] T049 [P] Manual SC-002 parity verification: run 10-question set in `quickstart.md` §7 via REST and WhatsApp; record pass/fail; require ≥9/10
- [x] T050 [P] Add integration test for FR-007 agent failure and timeout paths returning user-visible WhatsApp messages (no silent failure) in `apps/backend/tests/integration/test_whatsapp_error_handling.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Foundational — **MVP**
- **US3 (Phase 4)**: Depends on US1 mount (T018–T020); **validates** FR-001/FR-002 already wired in T018
- **US2 (Phase 5)**: Depends on US1 agent and sessions
- **US4 (Phase 6)**: Depends on US1 mount
- **US5 (Phase 7)**: Depends on Foundational settings API; **FR-019 sidebar** requires US6 T039–T040 + T043
- **US6 (Phase 8)**: No backend dependency — **start T039–T040 before US5 profile wrap** for FR-019
- **Polish (Phase 9)**: Depends on desired user stories complete

### User Story Dependencies

| Story | Priority | Depends on | Can parallel with |
|-------|----------|------------|-------------------|
| US1 | P1 | Foundational | — (MVP first) |
| US3 | P2 | US1 mount | US2, US5, US6 |
| US2 | P2 | US1 | US3, US5, US6 |
| US4 | P3 | US1 | US2, US3, US5, US6 |
| US5 | P2 | Foundational; US6 T039–T040 for FR-019 (T043) | US1, US6 |
| US6 | P2 | Foundational | US1, US5 (T037 before T043) |

### Within Each User Story

- Tests before or alongside implementation (write failing tests first where practical)
- Models/repository before services
- Services before mount/integration
- Backend settings API before Profile UI (US5)
- **US6 AppLayout (T039–T040) before Profile AppLayout wrap (T043)** — FR-019
- AppLayout before wrapping pages (US6)

### Parallel Opportunities

**After Phase 2 completes**, these tracks can run in parallel:

```text
Track A (backend):  US1 → US3 → US2 → US4
Track B (frontend): US6 layout (T039–T040) → US5 profile (T033–T037) → US6 pages + T043 wrap
Track C (polish):   After Track A + B
```

**Phase 2 parallel**: T007, T012, T013 (after T004–T006)

**US1 parallel**: T014, T015, T016, T021 (after foundational)

**US5 parallel**: T033, T034, T035 (after foundational)

**US6 parallel**: T039, T040 (after foundational)

---

## Parallel Example: User Story 1

```bash
# Parallel implementation (after Phase 2):
Task T015: build_whatsapp_agent() in apps/backend/src/agentos_chat/agents/whatsapp_agent.py
Task T016: whatsapp_gate.py in apps/backend/src/agentos_chat/services/
Task T017: whatsapp_queue.py in apps/backend/src/agentos_chat/services/
Task T021: integration tests in apps/backend/tests/integration/test_whatsapp_webhook.py

# Sequential after parallel block:
Task T018: whatsapp_mount.py (depends on T015–T017)
Task T019: whatsapp_service.py (depends on T018)
Task T020: main.py wiring (depends on T019)
```

---

## Parallel Example: Frontend (US6 + US5)

```bash
# Step 1 — layout shell (US6, required for FR-019):
Task T039: Sidebar.astro
Task T040: AppLayout.astro

# Step 2 — profile content (US5, parallel with T033–T034):
Task T033: whatsappTypes.ts
Task T034: whatsappApi.ts
Task T035: ProfileSettings.tsx
Task T037: profile.astro

# Step 3 — wrap all pages (US6):
Task T041: index.astro home page
Task T042: chat.astro wrap
Task T043: profile.astro AppLayout wrap   # completes FR-019 on Profile
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**critical**)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Enable via settings API; send WhatsApp message; verify reply
5. Optional: Phase 4 (US3 security tests) before production

### Incremental Delivery

1. Setup + Foundational → settings API ready
2. **US1** → WhatsApp bot answers questions (MVP)
3. **US3** → webhook security hardened for production
4. **US6 layout** (T039–T040) → **US5 Profile** (T033–T038) → **US6 page wraps** (T041–T043)
5. **US2** → multi-turn context verified
6. **US4** → `/new` session reset
7. Polish → T049 parity, T050 error tests, Railway deploy + full quickstart E2E

### Suggested MVP Scope

**Minimum shippable increment**: Phase 1 + Phase 2 + Phase 3 (US1) + Phase 4 (US3)

- Delivers core WhatsApp Q&A with secure webhook
- Settings managed via API until US5 Profile UI lands
- Frontend navigation (US6) and Profile (US5) can follow immediately after

---

## Notes

- WhatsApp routes mount **opt-in** only when `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN` are set
- Default `enabled=false` — must toggle via settings API or Profile page before bot responds
- Empty allowlist = open access when enabled; non-empty = restricted (silent ignore for others)
- Meta App setup is manual (outside repo) — see `quickstart.md`
- Agno session tables may auto-create on first run; document if manual DDL needed
- Commit after each task or logical group; run `make migrate` after T005
