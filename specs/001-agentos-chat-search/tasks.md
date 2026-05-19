# Tasks: AgentOS Chat Search

**Input**: Design documents from `/specs/001-agentos-chat-search/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Contract, integration, frontend interaction, migration, and deployment smoke tests are
included because this feature touches backend API contracts, persisted history, identity
boundaries, streaming, and Railway deployment.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the two-service monorepo, tooling, local environment examples, and root automation.

- [X] T001 Create backend and frontend project directories in `apps/backend/src/agentos_chat/`, `apps/backend/tests/`, `apps/frontend/src/`, and `apps/frontend/tests/`
- [X] T002 Create backend Python project metadata and dependency declarations in `apps/backend/pyproject.toml`
- [X] T003 Create frontend Astro project metadata and scripts in `apps/frontend/package.json`
- [X] T004 Configure backend linting, typing, and pytest settings in `apps/backend/pyproject.toml`
- [X] T005 Configure Astro and TypeScript settings in `apps/frontend/astro.config.ts` and `apps/frontend/tsconfig.json`
- [X] T006 [P] Create root Makefile skeleton with local and Railway target names in `Makefile`
- [X] T007 [P] Create backend and frontend environment examples in `apps/backend/.env.example` and `apps/frontend/.env.example`
- [X] T008 [P] Create Railway deployment notes directory and README in `infra/railway/README.md`
- [X] T009 [P] Update project README with feature overview and local command summary in `readme.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend, database, identity, and frontend client foundation that MUST be complete before any user story.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T010 Create database migration for `user_identities`, `chat_sessions`, `chat_messages`, `agent_runs`, and `search_results` in `apps/backend/migrations/versions/001_initial_chat_schema.py`
- [X] T011 [P] Add backend runtime settings loader for database, mock identity, CORS, model provider, and Agno telemetry in `apps/backend/src/agentos_chat/settings.py`
- [X] T012 [P] Implement mocked Auth0-compatible identity dependency in `apps/backend/src/agentos_chat/auth/dependencies.py`
- [X] T012a [P] Document mock identity transport contract (`X-Mock-Identity` header) in `apps/backend/src/agentos_chat/auth/dependencies.py` and OpenAPI spec
- [X] T013 [P] Define Pydantic API schemas for sessions, messages, runs, sources, SSE payloads, and errors in `apps/backend/src/agentos_chat/models/schemas.py`
- [X] T014 Create PostgreSQL connection/session management in `apps/backend/src/agentos_chat/db/session.py`
- [X] T015 Create repository base helpers with owner-filtered query utilities in `apps/backend/src/agentos_chat/db/repositories.py`
- [X] T016 [P] Create FastAPI app entrypoint with health route, CORS, routers, and structured error responses in `apps/backend/src/agentos_chat/main.py`
- [X] T017 [P] Create Agno agent factory with DuckDuckGoTools and safe progress abstractions in `apps/backend/src/agentos_chat/agents/search_agent.py`
- [X] T018 [P] Create backend structured logging configuration and trace field helpers in `apps/backend/src/agentos_chat/services/logging.py`
- [X] T019 [P] Create frontend typed API client and SSE helpers in `apps/frontend/src/services/chatApi.ts`
- [X] T020 [P] Create frontend chat state types in `apps/frontend/src/services/chatTypes.ts`
- [X] T021 [P] Create shared backend test fixtures for database, mock identity, and app client in `apps/backend/tests/conftest.py`

**Checkpoint**: Foundation ready. User story implementation can now begin in priority order or in parallel when dependencies allow.

---

## Phase 3: User Story 1 - Ask a Search-Backed Question (Priority: P1) MVP

**Goal**: A visitor can open `/chat`, restore owned history, submit a question, receive safe progress, streamed answer text, and search sources, create a new chat, and delete the active session.

**Independent Test**: Open `/chat`, ask a public-web question, verify streamed answer text and sources, create a new chat, reload history, and delete the active session so it is no longer restored or used as context.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**

- [X] T022 [P] [US1] Add contract tests for session list/create/restore/delete endpoints in `apps/backend/tests/contract/test_chat_sessions_contract.py`
- [X] T023 [P] [US1] Add contract tests for message submission and SSE event contract in `apps/backend/tests/contract/test_chat_stream_contract.py`
- [X] T024 [P] [US1] Add integration tests for owner-filtered history restore and deleted-session exclusion in `apps/backend/tests/integration/test_chat_history_context.py`
- [ ] T025 [P] [US1] Add integration test for DuckDuckGo-grounded agent response with visible sources in `apps/backend/tests/integration/test_search_grounding.py`
- [X] T026 [P] [US1] Add frontend interaction test for `/chat` submit, streaming, source rendering, New Chat, and Delete active session in `apps/frontend/tests/chat-happy-path.test.ts`

### Implementation for User Story 1

- [X] T027 [P] [US1] Implement user identity and chat session repository methods in `apps/backend/src/agentos_chat/db/identity_session_repository.py`
- [X] T028 [P] [US1] Implement chat message, agent run, and search result repository methods in `apps/backend/src/agentos_chat/db/message_run_repository.py`
- [X] T029 [US1] Implement chat session service for create/list/restore/delete and active-session filtering in `apps/backend/src/agentos_chat/services/session_service.py`
- [X] T030 [US1] Implement agent run service that injects current identity active session history into every run in `apps/backend/src/agentos_chat/services/agent_service.py`
- [X] T031 [US1] Implement DuckDuckGo search response grounding, source capture, and insufficient-context fallback in `apps/backend/src/agentos_chat/agents/search_agent.py`
- [X] T032 [US1] Implement session API routes for list/create/restore/delete in `apps/backend/src/agentos_chat/api/sessions.py`
- [X] T033 [US1] Implement message submission route that creates user message and run record in `apps/backend/src/agentos_chat/api/messages.py`
- [X] T034 [US1] Implement SSE stream route for `thinking`, `token`, `source`, `done`, and `error` events in `apps/backend/src/agentos_chat/api/stream.py`
- [X] T035 [P] [US1] Create Astro `/chat` page shell in `apps/frontend/src/pages/chat.astro`
- [X] T036 [P] [US1] Create chat transcript, message composer, source list, and session action components in `apps/frontend/src/components/ChatBox.tsx`
- [X] T037 [US1] Implement frontend session restore, New Chat, Delete active session, submit, and SSE streaming logic in `apps/frontend/src/services/chatApi.ts`
- [X] T038 [US1] Wire `/chat` UI states for empty, restoring, ready, submitting, thinking, streaming, deleted, and failed states in `apps/frontend/src/components/ChatBox.tsx`
- [X] T039 [US1] Add safe source rendering and unsupported-answer fallback display in `apps/frontend/src/components/ChatBox.tsx`
- [X] T040 [US1] Add structured trace logs for session restore, agent run start, search source capture, and stream completion in `apps/backend/src/agentos_chat/services/logging.py`

- [ ] T076 [P] [US1] Add integration test for visible answer latency target (SC-001) in `apps/backend/tests/integration/test_chat_latency.py`
- [ ] T077 [P] [US1] Add integration test for history restore latency target (SC-004) in `apps/backend/tests/integration/test_chat_latency.py`
- [ ] T078 [P] [US1] Add integration test for stream start latency target (SC-009) in `apps/backend/tests/integration/test_chat_latency.py`
- [X] T079 [US1] Document manual latency measurement steps for SC-001, SC-004, SC-009 in `specs/001-agentos-chat-search/quickstart.md`

**Checkpoint**: User Story 1 is fully functional and independently testable as the MVP.

---

## Phase 4: User Story 2 - Handle Chat and Search Failures Gracefully (Priority: P2)

**Goal**: The UI and backend handle search failures, timeouts, empty input, repeated submits, stop actions, interrupted streams, invalid mock identity, and unavailable history without losing prior messages.

**Independent Test**: Simulate each failure mode and verify a user-readable, retryable state while preserving the latest submitted question and prior completed messages.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**

- [X] T041 [P] [US2] Add contract tests for stop endpoint and terminal run conflicts in `apps/backend/tests/contract/test_stop_run_contract.py`
- [ ] T042 [P] [US2] Add integration tests for search provider failure, timeout, and malformed agent output in `apps/backend/tests/integration/test_agent_failures.py`
- [ ] T043 [P] [US2] Add integration tests for invalid mock identity and unavailable history in `apps/backend/tests/integration/test_identity_and_restore_failures.py`
- [ ] T044 [P] [US2] Add frontend interaction tests for empty input, retryable error, Stop, repeated submit, and interrupted stream states in `apps/frontend/tests/chat-failure-states.test.ts`

### Implementation for User Story 2

- [X] T045 [US2] Implement run cancellation state transitions and ownership checks in `apps/backend/src/agentos_chat/services/agent_service.py`
- [X] T046 [US2] Implement stop route for active agent runs in `apps/backend/src/agentos_chat/api/runs.py`
- [X] T047 [US2] Implement backend timeout, rate-limit, malformed-output, and search-unavailable error mapping in `apps/backend/src/agentos_chat/services/agent_service.py`
- [X] T048 [US2] Implement identity failure handling and user-safe error responses in `apps/backend/src/agentos_chat/auth/dependencies.py`
- [X] T049 [US2] Implement frontend Stop button behavior and cancellation UI in `apps/frontend/src/components/ChatBox.tsx`
- [X] T050 [US2] Implement frontend empty-input validation and duplicate-submit prevention in `apps/frontend/src/components/ChatBox.tsx`
- [X] T051 [US2] Implement frontend retryable error state preservation for failed submits and streams in `apps/frontend/src/services/chatApi.ts`
- [X] T052 [US2] Implement accessibility affordances for streaming updates, errors, Stop, and New Chat controls in `apps/frontend/src/components/ChatBox.tsx`
- [X] T053 [US2] Add backend logging for stopped, failed, timed-out, and invalid-identity runs in `apps/backend/src/agentos_chat/services/logging.py`

**Checkpoint**: User Stories 1 and 2 both work independently, with graceful recovery from expected failure modes.

---

## Phase 5: User Story 3 - Publish the Chat Experience (Priority: P3)

**Goal**: A maintainer can use local Makefile commands to create/configure Railway services with minimum CPU and memory, deploy both services, inspect status/logs, and run a smoke test without GitHub Actions.

**Independent Test**: From a clean environment with required credentials and secrets, run the documented Makefile deployment commands, open the published `/chat` URL, and complete the primary chat flow.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**

- [ ] T054 [P] [US3] Add Makefile target tests for required local and Railway commands in `apps/backend/tests/integration/test_makefile_targets.py`
- [ ] T055 [P] [US3] Add Railway configuration validation tests for service names, env vars, and minimum CPU/memory exception documentation in `apps/backend/tests/integration/test_railway_config.py`
- [X] T056 [P] [US3] Add deployment smoke test script for frontend-to-backend connectivity in `infra/railway/smoke_test.py`
- [ ] T057 [P] [US3] Add frontend production build verification test for `/chat` route configuration in `apps/frontend/tests/chat-build.test.ts`

### Implementation for User Story 3

- [X] T058 [US3] Implement Makefile targets `install`, `db-up`, `migrate`, `dev`, `check`, `test`, and `smoke-local` in `Makefile`
- [X] T059 [US3] Implement Makefile targets `railway-preflight`, `railway-up`, `railway-deploy`, `railway-status`, `railway-smoke`, `railway-logs-backend`, and `railway-logs-frontend` in `Makefile`
- [X] T060 [US3] Create Railway service setup helper with two-service topology and pgvector database provisioning in `infra/railway/railway_up.sh`
- [X] T061 [US3] Add Railway variable and service naming documentation in `infra/railway/README.md`
- [X] T062 [US3] Add minimum CPU/memory configuration and documented exception handling in `infra/railway/railway_up.sh`
- [X] T063 [US3] Configure backend production start command and health endpoint documentation in `apps/backend/pyproject.toml` and `infra/railway/README.md`
- [X] T064 [US3] Configure frontend production build/start settings for Railway in `apps/frontend/package.json` and `apps/frontend/astro.config.ts`
- [X] T065 [US3] Implement deployed smoke test for public `/chat` and backend `/health` checks in `infra/railway/smoke_test.py`
- [X] T066 [US3] Update quickstart deployment commands and troubleshooting details in `specs/001-agentos-chat-search/quickstart.md`

**Checkpoint**: All user stories are independently functional and deployable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, documentation, and verification across all stories.

- [ ] T067 [P] Add backend unit tests for repository ownership filters and deleted/inactive session exclusions in `apps/backend/tests/unit/test_repository_filters.py`
- [ ] T068 [P] Add backend unit tests for safe progress event serialization and hidden-reasoning exclusion in `apps/backend/tests/unit/test_safe_progress_events.py`
- [ ] T069 [P] Add frontend unit tests for chat state reducer transitions in `apps/frontend/tests/chat-state.test.ts`
- [ ] T070 [P] Add migration rollback and index verification tests in `apps/backend/tests/integration/test_migrations.py`
- [ ] T071 Run full local verification commands and record results in `specs/001-agentos-chat-search/quickstart.md`
- [ ] T072 [P] Update API contract examples after implementation in `specs/001-agentos-chat-search/contracts/openapi.yaml`
- [ ] T073 [P] Update UI contract examples after implementation in `specs/001-agentos-chat-search/contracts/chat-ui.md`
- [X] T074 Review security boundaries for mocked identity and future Auth0 replacement in `apps/backend/src/agentos_chat/auth/dependencies.py`
- [X] T075 Validate Railway deployment exception documentation for CPU/memory settings in `infra/railway/README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies, can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion; delivers MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational and may use US1's run/session code, but has independent failure-state validation.
- **User Story 3 (Phase 5)**: Depends on Foundational and can start after service shape is known; final smoke test depends on US1 and US2 behavior.
- **Polish (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1 Ask a Search-Backed Question**: Start after Phase 2. This is the MVP.
- **US2 Handle Chat and Search Failures Gracefully**: Start after Phase 2; integrates with US1 endpoints and UI but can be tested by simulated failures.
- **US3 Publish the Chat Experience**: Start after Phase 2 for Makefile/Railway scaffolding; deployment smoke completion depends on US1.

### Within Each User Story

- Tests must be written and fail before implementation tasks.
- Backend repositories and services precede API route wiring.
- API contract behavior precedes frontend integration.
- Frontend state handling precedes smoke validation.
- Story checkpoint must pass before moving to the next priority when working sequentially.

### Parallel Opportunities

- Setup tasks T004-T009 can run in parallel after T001-T003.
- Foundational tasks T011-T013 and T016-T021 can run in parallel after T010 where they do not share files.
- US1 tests T022-T026 can run in parallel.
- US1 backend repository tasks T027-T028 can run in parallel with frontend shell tasks T035-T036.
- US2 tests T041-T044 can run in parallel.
- US3 tests T054-T057 can run in parallel.
- Polish tasks T067-T070 and T072-T073 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch US1 contract/integration/frontend tests together:
Task: "T022 [P] [US1] Add contract tests for session list/create/restore/delete endpoints in apps/backend/tests/contract/test_chat_sessions_contract.py"
Task: "T023 [P] [US1] Add contract tests for message submission and SSE event contract in apps/backend/tests/contract/test_chat_stream_contract.py"
Task: "T024 [P] [US1] Add integration tests for owner-filtered history restore and deleted-session exclusion in apps/backend/tests/integration/test_chat_history_context.py"
Task: "T025 [P] [US1] Add integration test for DuckDuckGo-grounded agent response with visible sources in apps/backend/tests/integration/test_search_grounding.py"
Task: "T026 [P] [US1] Add frontend interaction test for /chat submit, streaming, source rendering, New Chat, and Delete active session in apps/frontend/tests/chat-happy-path.test.ts"

# Launch independent US1 implementation work:
Task: "T027 [P] [US1] Implement user identity and chat session repository methods in apps/backend/src/agentos_chat/db/identity_session_repository.py"
Task: "T028 [P] [US1] Implement chat message, agent run, and search result repository methods in apps/backend/src/agentos_chat/db/message_run_repository.py"
Task: "T035 [P] [US1] Create Astro /chat page shell in apps/frontend/src/pages/chat.astro"
Task: "T036 [P] [US1] Create chat transcript, message composer, source list, and session action components in apps/frontend/src/components/ChatBox.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "T041 [P] [US2] Add contract tests for stop endpoint and terminal run conflicts in apps/backend/tests/contract/test_stop_run_contract.py"
Task: "T042 [P] [US2] Add integration tests for search provider failure, timeout, and malformed agent output in apps/backend/tests/integration/test_agent_failures.py"
Task: "T043 [P] [US2] Add integration tests for invalid mock identity and unavailable history in apps/backend/tests/integration/test_identity_and_restore_failures.py"
Task: "T044 [P] [US2] Add frontend interaction tests for empty input, retryable error, Stop, repeated submit, and interrupted stream states in apps/frontend/tests/chat-failure-states.test.ts"
```

## Parallel Example: User Story 3

```bash
Task: "T054 [P] [US3] Add Makefile target tests for required local and Railway commands in apps/backend/tests/integration/test_makefile_targets.py"
Task: "T055 [P] [US3] Add Railway configuration validation tests for service names, env vars, and minimum CPU/memory exception documentation in apps/backend/tests/integration/test_railway_config.py"
Task: "T056 [P] [US3] Add deployment smoke test script for frontend-to-backend connectivity in infra/railway/smoke_test.py"
Task: "T057 [P] [US3] Add frontend production build verification test for /chat route configuration in apps/frontend/tests/chat-build.test.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational prerequisites.
3. Complete Phase 3: Ask a Search-Backed Question.
4. Stop and validate US1 independently with backend contract tests, integration tests, frontend interaction test, and local smoke flow.
5. Demo locally before adding failure hardening or deployment automation.

### Incremental Delivery

1. Setup + Foundational -> backend/frontend skeleton, DB schema, identity boundary, agent factory.
2. US1 -> working chat loop with persisted active-session history, streaming, sources, New Chat, and Delete active session.
3. US2 -> graceful stop, timeout, search failure, invalid identity, and retryable UI states.
4. US3 -> Makefile and Railway deployment workflow with minimum CPU/memory settings and smoke tests.
5. Polish -> additional unit tests, contract updates, security review, and deployment documentation.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup and Foundational tasks together.
2. Backend developer implements repositories/services/routes for US1 while frontend developer builds `/chat`.
3. Test/deployment developer writes US1 tests and begins US3 Makefile validation scaffolding.
4. After US1 checkpoint, one developer hardens US2 failure states while another completes US3 deployment automation.

---

## Notes

- [P] tasks are safe to run in parallel because they touch different files or depend only on completed setup.
- [US1], [US2], and [US3] labels map directly to the prioritized user stories in `spec.md`.
- All backend read/write paths must filter by mocked/Auth0-compatible identity.
- User-facing thinking/progress must never expose raw hidden reasoning, internal prompts, secrets, or chain-of-thought.
- Railway deployment stays local-first through `Makefile`; GitHub Actions is out of scope for this release.
