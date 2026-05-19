# Tasks: LangWatch Backend Observability

**Input**: Design documents from `/specs/002-langwatch-backend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Unit tests for conditional LangWatch setup are included (plan Phase E). Manual
LangWatch UI verification is documented in quickstart.md (no API key in CI).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label ([US1], [US2], [US3])
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add LangWatch dependencies and environment templates.

- [X] T001 Add `langwatch` and `openinference-instrumentation-agno` runtime dependencies in `apps/backend/pyproject.toml`
- [X] T002 [P] Add `LANGWATCH_API_KEY`, `LANGWATCH_ENDPOINT`, and `APP_ENVIRONMENT` placeholders with comments in `apps/backend/.env.example`
- [X] T003 [P] Create `apps/backend/src/agentos_chat/observability/__init__.py` package marker for LangWatch module

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Settings and observability module skeleton required before user story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Extend `Settings` with `langwatch_api_key`, `langwatch_endpoint`, and validated `app_environment` (`local` \| `staging` \| `production`, default `local`) in `apps/backend/src/agentos_chat/settings.py`
- [X] T005 Create `configure_langwatch()` stub and `trace_agent_run()` context manager signatures in `apps/backend/src/agentos_chat/observability/langwatch.py` (no-op implementations acceptable until US1)
- [X] T006 [P] Add `log_langwatch_disabled`, `log_langwatch_enabled`, `log_langwatch_setup_failed`, and `log_langwatch_export_failed` helpers in `apps/backend/src/agentos_chat/services/logging.py`

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Trace Agent Runs in LangWatch (Priority: P1) MVP

**Goal**: When `LANGWATCH_API_KEY` is set, each chat agent run exports a LangWatch trace with full
content, model/tool spans, and required metadata (`run_id`, `session_id`, `auth_subject`,
`environment`).

**Independent Test**: Set `LANGWATCH_API_KEY` and `APP_ENVIRONMENT=local`, start backend, submit
one chat message, confirm trace in LangWatch within 60s with correct metadata and nested spans
(per `specs/002-langwatch-backend/quickstart.md`).

### Tests for User Story 1

- [X] T007 [P] [US1] Add unit tests for conditional `configure_langwatch()` (no setup without key; `langwatch.setup` called with `AgnoInstrumentor` when key set) in `apps/backend/tests/unit/test_langwatch.py`

### Implementation for User Story 1

- [X] T008 [US1] Implement `configure_langwatch()` with `langwatch.setup(instrumentors=[AgnoInstrumentor()])`, apply `LANGWATCH_ENDPOINT` to the environment when `Settings.langwatch_endpoint` is set, log `langwatch_disabled` / `langwatch_enabled` / setup failures (no secrets), and never log API keys in `apps/backend/src/agentos_chat/observability/langwatch.py`
- [X] T009 [US1] Call `configure_langwatch()` from FastAPI lifespan after `configure_logging()` in `apps/backend/src/agentos_chat/main.py`
- [X] T010 [US1] Implement `trace_agent_run(run_id, session_id, auth_subject)` context manager setting metadata per `specs/002-langwatch-backend/contracts/langwatch-trace-metadata.md` in `apps/backend/src/agentos_chat/observability/langwatch.py`
- [X] T011 [US1] Wrap `agent.run(...)` inside `trace_agent_run` in `agent_service._execute_run`, catching export errors and logging via `log_langwatch_export_failed` without failing chat in `apps/backend/src/agentos_chat/services/agent_service.py`

**Checkpoint**: User Story 1 complete — traces visible in LangWatch when API key is configured.

---

## Phase 4: User Story 2 - Operate Without LangWatch in Development (Priority: P2)

**Goal**: Backend starts and chat works with no LangWatch API key; no traces sent; enabling key
after restart activates tracing without code changes.

**Independent Test**: Unset `LANGWATCH_API_KEY`, start backend, submit chat message — no startup
failure, no user-facing errors, no LangWatch traces (per spec User Story 2).

### Tests for User Story 2

- [X] T012 [P] [US2] Add unit test asserting `configure_langwatch()` is a no-op when `langwatch_api_key` is empty in `apps/backend/tests/unit/test_langwatch.py`
- [X] T013 [P] [US2] Add unit test asserting `_execute_run` path does not propagate LangWatch exceptions when tracing is disabled or export fails (mock) in `apps/backend/tests/unit/test_langwatch.py`

### Implementation for User Story 2

- [X] T014 [US2] Verify `build_search_agent()` and `Settings.agno_telemetry` are unchanged when LangWatch is enabled in `apps/backend/src/agentos_chat/agents/search_agent.py` and `apps/backend/src/agentos_chat/settings.py`
- [X] T015 [US2] Document optional LangWatch disable/enable workflow (no key vs key + restart) in `specs/002-langwatch-backend/quickstart.md` section "Disable Tracing"

**Checkpoint**: User Story 2 complete — local dev works with zero LangWatch configuration.

---

## Phase 5: User Story 3 - Deploy Observability to Railway (Priority: P3)

**Goal**: Maintainers can set optional Railway env vars and verify deployed traces tagged with
`environment=production` or `staging`.

**Independent Test**: Deploy backend with `LANGWATCH_API_KEY` and `APP_ENVIRONMENT=production` on
Railway, run smoke test or one chat message, confirm trace with non-`local` environment tag.

### Implementation for User Story 3

- [X] T016 [P] [US3] Add LangWatch optional env vars and verification steps to `apps/backend/README.md`
- [X] T017 [P] [US3] Document optional `LANGWATCH_API_KEY`, `LANGWATCH_ENDPOINT`, and `APP_ENVIRONMENT` for `agentos-chat-backend` Railway service in `infra/railway/README.md` (no deploy gate)
- [X] T018 [US3] Add Railway post-deploy trace verification checklist to `specs/002-langwatch-backend/quickstart.md` Railway section

**Checkpoint**: User Story 3 complete — deployment docs cover optional LangWatch configuration.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation and repository hygiene across all stories.

- [X] T019 Run `make check` and `make test` from repository root after LangWatch changes (ruff + backend unit/contract tests pass; mypy reports pre-existing errors in unrelated files)
- [ ] T020 Execute manual quickstart verification per `specs/002-langwatch-backend/quickstart.md`: first trace within 60s (SC-001), metadata (SC-007/SC-008), model vs tool spans on 10 search-backed runs (SC-003), failed/timeout run trace status (US1 scenario 3), chat works with key on/off (SC-002/SC-005), invalid-key log signal; record pass/fail in PR notes
- [X] T021 [P] Add one-line LangWatch feature pointer in root `readme.md` linking to `specs/002-langwatch-backend/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **blocks all user stories**
- **User Story 1 (Phase 3)**: Depends on Phase 2 — **MVP**
- **User Story 2 (Phase 4)**: Depends on Phase 3 implementation (validates disable path of same code)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (documents deployed tracing); can parallelize docs with US2 tests after US1 code lands
- **Polish (Phase 6)**: Depends on Phases 3–5

### User Story Dependencies

```text
Phase 1 Setup → Phase 2 Foundational → US1 (P1) → US2 (P2) validates US1 disable path
                                      └────────→ US3 (P3) docs (can start after US1)
```

- **US1 (P1)**: Core tracing — no dependency on US2/US3
- **US2 (P2)**: Tests and documents behavior of US1 when LangWatch is off
- **US3 (P3)**: Documentation only; no code dependency on US2

### Within Each User Story

- Tests before or alongside implementation (T007 before T008–T011)
- `configure_langwatch` before `trace_agent_run` usage
- `trace_agent_run` before `agent_service` wrap

### Parallel Opportunities

- **Phase 1**: T002 and T003 parallel after T001
- **Phase 2**: T006 parallel with T004–T005 after T004 starts
- **US1**: T007 parallel with early T008 prep (different files); T008–T009 sequential; T010–T011 sequential
- **US2**: T012 and T013 parallel
- **US3**: T016 and T017 parallel
- **Polish**: T021 parallel with T019–T020

---

## Parallel Example: User Story 1

```bash
# Tests first (mock langwatch.setup):
# Task T007 in apps/backend/tests/unit/test_langwatch.py

# Then sequential implementation:
# T008 → T009 in observability/langwatch.py
# T010 wraps context manager metadata
# T011 in agent_service.py
```

---

## Parallel Example: User Story 3

```bash
# Documentation tasks in parallel:
# T016 apps/backend/README.md
# T017 infra/railway/README.md
# Then T018 quickstart Railway section
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T006)
3. Complete Phase 3: User Story 1 (T007–T011)
4. **STOP and VALIDATE**: Manual quickstart — one trace in LangWatch with metadata
5. Optionally ship MVP before US2/US3 doc polish

### Incremental Delivery

1. Setup + Foundational → module and settings ready
2. US1 → LangWatch traces when key set (**MVP**)
3. US2 → Confirmed graceful disable + unit tests
4. US3 → Railway maintainer docs
5. Polish → `make check`, `make test`, manual SC verification

### Suggested MVP Scope

**Phases 1–3 only** (T001–T011): delivers P1 trace export; US2/US3 are validation and docs.

---

## Notes

- Do not commit real `LANGWATCH_API_KEY` values; use `.env` locally only
- `AGNO_TELEMETRY` remains independent per FR-012
- No PostgreSQL migrations or frontend changes in this feature
- Contract reference: `specs/002-langwatch-backend/contracts/langwatch-trace-metadata.md`
