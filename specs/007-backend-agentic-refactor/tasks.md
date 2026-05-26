# Tasks: Backend Agentic Architecture Refactor

**Input**: Design documents from `/specs/007-backend-agentic-refactor/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Backend refactor per constitution — unit and integration tests included per plan/quickstart. Existing contract suite is the deploy gate (US7).

**Organization**: Tasks grouped by user story. **Big-bang release**: all phases must complete before production deploy (spec clarification); stories are logically separable for development and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps to spec user stories (US1–US7)
- Paths relative to repo root unless absolute

## Path Conventions

- **Backend**: `apps/backend/src/agentos_chat/`
- **Migrations**: `apps/backend/migrations/versions/`
- **Scripts**: `apps/backend/scripts/`
- **Tests**: `apps/backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency pins and tooling fixes before refactor

- [X] T001 Pin Agno to `>=2.4,<3` in `apps/backend/pyproject.toml`
- [X] T002 Fix mypy overrides to `[[tool.mypy.overrides]]` for `agno.*` in `apps/backend/pyproject.toml`
- [X] T003 [P] Add `scripts/` directory and ensure `apps/backend/scripts/` is on PYTHONPATH or invokable via `python -m` for backfill script in `apps/backend/scripts/__init__.py` (empty package if needed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: AgentOS wiring, lifespan, concurrency guards, and RunExecutor skeleton — **blocks all user stories**

**⚠️ CRITICAL**: No user story work until this phase completes

- [X] T004 Refactor `apps/backend/src/agentos_chat/main.py` to mount `AgentOS(agents=[...], teams=[...], db=PostgresDb(...), base_app=app)` while keeping existing routers; merge lifespan with logging, LangWatch, JWKS load, orphan cleanup, and `engine.dispose()` on shutdown
- [X] T005 [P] Add JWKS periodic refresh helper and app-state storage in `apps/backend/src/agentos_chat/auth/jwt_middleware.py`; call from lifespan in `apps/backend/src/agentos_chat/main.py` (remove sync fetch at import time)
- [X] T006 [P] Implement orphan run recovery on startup (mark `queued|running|stopping` → `failed` with `orphaned`) in `apps/backend/src/agentos_chat/services/orphan_cleanup.py` and invoke from lifespan in `apps/backend/src/agentos_chat/main.py`
- [X] T007 [P] Implement per-session and per-user (max 10) concurrency guards in `apps/backend/src/agentos_chat/services/concurrency.py` raising structured conflict errors (`run_in_progress`, `concurrent_run_limit`); user cap MUST sum active runs from both chat and research tables (FR-009a)
- [X] T008 [P] Add `has_active_chat_run(session_id)` to `apps/backend/src/agentos_chat/db/message_run_repository.py`; add `has_active_research_run(session_id)` and `count_active_research_runs_for_user(user_identity_id)` to `apps/backend/src/agentos_chat/db/research_repository.py`; implement `count_active_runs_for_user()` in `concurrency.py` summing both repositories
- [X] T009 Refactor `apps/backend/src/agentos_chat/agents/search_agent.py` to accept `Settings` and return lifespan-ready `Agent` with `PostgresDb(session_table="chat_agno_sessions")`, `OpenRouter(api_key=...)`, `TavilyTools(api_key=...)`, `telemetry=settings.agno_telemetry`; remove `os.environ` mutation and `format_user_prompt`/`build_history_prompt`
- [X] T010 [P] Refactor `apps/backend/src/agentos_chat/agents/research_agent.py` factory to accept `Settings`, wire `PostgresDb`, direct API keys, and prepare for `output_schema=ResearchResult`; keep `ResearchResult` model in same file
- [X] T011 [P] Create Agno→SSE event mapper with `isinstance` checks in `apps/backend/src/agentos_chat/services/event_mapper.py` per `specs/007-backend-agentic-refactor/contracts/run-execution.md`; map `ReasoningContentDeltaEvent` to safe `thinking` strings only; optional research `reasoning` event emits redacted phase summary at run end (never raw CoT)
- [X] T012 Create RunExecutor skeleton with shared cancel/timeout/trace hooks in `apps/backend/src/agentos_chat/services/run_executor.py`
- [X] T013 [P] Create domain projection helpers (chat + research message/run sync) in `apps/backend/src/agentos_chat/services/projection.py` per `specs/007-backend-agentic-refactor/data-model.md`

**Checkpoint**: AgentOS mounted, agents registered, guards and executor skeleton ready

---

## Phase 3: User Story 1 — Real-Time Agent Responses (Priority: P1) 🎯 MVP

**Goal**: Native async streaming via `arun(stream=True, stream_events=True)` — no fake chunk loops; safe `thinking` events during tool use

**Independent Test**: Submit chat message; SSE `thinking` within 3s, then progressive `token` events until `done` (quickstart §2)

### Tests for User Story 1

- [X] T014 [P] [US1] Add unit tests for `event_mapper.py` Agno event → SSE mapping in `apps/backend/tests/unit/test_event_mapper.py`
- [ ] T015 [P] [US1] Add integration test for native chat streaming (no bulk fake chunk burst) in `apps/backend/tests/integration/test_streaming_native.py` *(deferred — requires live agent)*

### Implementation for User Story 1

- [X] T016 [US1] Implement `RunExecutor.execute_chat_run()` with `async for event in agent.arun(..., stream=True, stream_events=True)` in `apps/backend/src/agentos_chat/services/run_executor.py`
- [X] T017 [US1] Refactor `apps/backend/src/agentos_chat/services/agent_service.py` to delegate `_execute_run` to `RunExecutor`; remove sync `asyncio.to_thread(agent.run)` and artificial 24-char chunk loop
- [X] T018 [US1] Wire `trace_agent_run()` around chat execution in `apps/backend/src/agentos_chat/services/run_executor.py`

**Checkpoint**: Chat streams natively; median time-to-first-token measurably faster

---

## Phase 4: User Story 2 — Reliable Research Output Structure (Priority: P1)

**Goal**: Research team returns typed `ResearchResult` via `output_schema`; remove delimiter regex parsing

**Independent Test**: Five research scenarios (new article, summary, Q&A, refinement, fallback) map correctly to chat/article/actions panels (spec US2)

### Tests for User Story 2

- [X] T019 [P] [US2] Replace delimiter parser unit tests with structured-output tests in `apps/backend/tests/unit/test_research_agent.py`

### Implementation for User Story 2

- [X] T020 [US2] Add `output_schema=ResearchResult` and trim `COORDINATOR_PROMPT` delimiter rules in `apps/backend/src/agentos_chat/agents/research_agent.py`; delete `parse_research_output()` and regex patterns
- [X] T021 [US2] Implement `RunExecutor.execute_research_run()` mapping structured `TeamRunOutput.content` to projection + SSE (`article`, `actions`, `token`) in `apps/backend/src/agentos_chat/services/run_executor.py`
- [X] T021a [US2] Persist research token/cost records from `ModelRequestCompletedEvent` via `projection.py` to `research_costs` table during research runs (FR-014)
- [X] T022 [US2] Refactor `apps/backend/src/agentos_chat/services/research_service.py` to delegate to `RunExecutor`; remove sync `_run_team_streaming` closure and `asyncio.run_coroutine_threadsafe` bridge

**Checkpoint**: Research produces reliable chat/article/actions without delimiter repair

---

## Phase 5: User Story 3 — Conversation Continuity (Priority: P1)

**Goal**: Agent session store authoritative; domain `chat_messages` projected for API restore; multi-turn context without manual history strings

**Independent Test**: Follow-up chat and research turns reference prior content after page reload (spec US3)

### Tests for User Story 3

- [ ] T023 [P] [US3] Add integration test for multi-turn chat history continuity in `apps/backend/tests/integration/test_chat_history_context.py` (extend existing file) *(deferred — requires live agent)*

### Implementation for User Story 3

- [X] T024 [US3] Pass `session_id=str(session_id)` and `add_history_to_context=True` in chat and research `arun` calls in `apps/backend/src/agentos_chat/services/run_executor.py`
- [X] T025 [US3] Implement chat message projection (incremental + final sync) from run state to `chat_messages` in `apps/backend/src/agentos_chat/services/projection.py`
- [X] T026 [US3] Implement research message projection including optional operator-only `reasoning_content` (redacted summary for SSE `reasoning` event; full detail DB-only) in `apps/backend/src/agentos_chat/services/projection.py`
- [X] T027 [P] [US3] Create idempotent backfill script from existing `chat_messages` to `chat_agno_sessions` in `apps/backend/scripts/backfill_chat_agno_sessions.py`

**Checkpoint**: Agents remember session history; restore API matches agent store

---

## Phase 6: User Story 4 — Accurate Source Citations (Priority: P2)

**Goal**: Sources from Tavily tool results with title, URL, snippet — not URL regex on answer text

**Independent Test**: Chat search answer includes source with human-readable title ≠ URL (quickstart §7)

### Implementation for User Story 4

- [X] T028 [US4] Extract Tavily sources from `ToolCallCompletedEvent` / `RunOutput.tools` in `apps/backend/src/agentos_chat/services/event_mapper.py` and emit `source` SSE events
- [X] T029 [US4] Persist ranked sources via `MessageRunRepository.add_search_results()` in `apps/backend/src/agentos_chat/services/projection.py`; remove `extract_sources_from_text()` usage from `apps/backend/src/agentos_chat/services/agent_service.py`
- [X] T030 [P] [US4] Delete URL regex helper from `apps/backend/src/agentos_chat/agents/search_agent.py` if no longer referenced

**Checkpoint**: Sources include titles and snippets when Tavily provides them

---

## Phase 7: User Story 5 — Stop and Recover (Priority: P2)

**Goal**: Reliable stop/timeout/orphan terminal states; partial content kept; per-session and per-user concurrency enforced at API

**Independent Test**: Stop mid-run preserves partial text; 409 on concurrent chat message; 409 on 11th user run (quickstart §3–5)

### Tests for User Story 5

- [X] T031 [P] [US5] Add unit tests for concurrency guards (per-session, cross-table user cap) in `apps/backend/tests/unit/test_concurrency.py`
- [ ] T032 [P] [US5] Extend contract test for chat concurrent run 409 in `apps/backend/tests/contract/test_chat_sessions_contract.py` *(deferred — needs run fixture)*
- [ ] T032a [P] [US5] Add contract test for `concurrent_run_limit` on 11th run (chat + research paths) in `apps/backend/tests/contract/test_concurrent_run_limit_contract.py` (SC-011) *(deferred — needs run fixture)*

### Implementation for User Story 5

- [X] T033a [US5] Implement timeout enforcement in `run_executor.py` using `asyncio.wait_for` for chat (`request_timeout_seconds`) and research (`research_timeout_seconds`); on timeout mark run `failed`, emit `error` + `done` with code `timeout` (FR-008)
- [X] T033 [US5] On cancel in `RunExecutor`, persist partial assistant content with `stopped` status via `apps/backend/src/agentos_chat/services/projection.py` (requires incremental projection from T025)
- [X] T034 [US5] Enforce concurrency guards before spawning runs in `apps/backend/src/agentos_chat/services/agent_service.py` and `apps/backend/src/agentos_chat/api/messages.py` (return 409 `run_in_progress`)
- [X] T035 [US5] Enforce concurrency guards in `apps/backend/src/agentos_chat/api/research_sessions.py` and research message/create paths (409 `run_in_progress` and `concurrent_run_limit`)
- [X] T036 [P] [US5] Optional Alembic migration for active-run query index in `apps/backend/migrations/versions/004_active_run_concurrency_index.py`

**Checkpoint**: Stop/timeout/orphan paths terminal; concurrency limits enforced

---

## Phase 8: User Story 6 — Operator Visibility (Priority: P2)

**Goal**: LangWatch traces for both chat and research runs with run/session/subject metadata

**Independent Test**: One chat + one research run appear in LangWatch with correlation fields (quickstart §10)

### Implementation for User Story 6

- [X] T037 [US6] Wrap `RunExecutor.execute_research_run()` with `trace_agent_run()` in `apps/backend/src/agentos_chat/services/run_executor.py`
- [X] T038 [P] [US6] Emit structured run lifecycle logs (`agent_run_start`, `stream_complete`, `run_failed`) from `RunExecutor` using `apps/backend/src/agentos_chat/services/logging.py`

**Checkpoint**: Chat and research runs fully traced when LangWatch enabled

---

## Phase 9: User Story 7 — Preserved Product Behavior (Priority: P1)

**Goal**: Zero regression — all existing contract/integration tests pass without frontend changes

**Independent Test**: `pytest tests/contract/` 100% pass (SC-007)

### Tests for User Story 7

- [X] T039 [US7] Run and fix regressions in full contract suite under `apps/backend/tests/contract/` until 100% pass (10/10 pass)
- [X] T040 [P] [US7] Run integration tests under `apps/backend/tests/integration/` and scenario tests under `apps/backend/tests/scenarios/`; fix failures (7/7 integration pass; 6 scenario skipped — require live API keys)

### Implementation for User Story 7

- [X] T041 [US7] Verify SSE event names and payloads match `specs/007-backend-agentic-refactor/contracts/api-stability.md` (no frontend-breaking changes)
- [X] T042 [US7] Remove dead code paths: manual history formatters, delimiter parser, fake chunk loops, per-request `os.environ` mutation across `apps/backend/src/agentos_chat/`

**Checkpoint**: Big-bang merge gate — all contract tests green

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, deploy readiness, final validation

- [X] T043 [P] Add unit tests for `RunExecutor` cancel/timeout paths in `apps/backend/tests/unit/test_run_executor.py`
- [X] T044 [P] Update `apps/backend/README.md` with agent session store, backfill script usage, and concurrency limits
- [X] T045 Run full `make check` and `make test` from repo root; fix lint/type errors (ruff clean; 57/57 non-scenario tests pass)
- [ ] T046 Execute manual verification checklist in `specs/007-backend-agentic-refactor/quickstart.md` and document baseline vs post-refactor time-to-first-token (SC-009)
- [ ] T047 Document Railway big-bang deploy steps including one-time backfill in `specs/007-backend-agentic-refactor/quickstart.md` Deploy Notes section if gaps found during T046

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) — BLOCKS all user stories
    ↓
Phase 3 (US1) ──┬── Phase 4 (US2) ──┬── Phase 5 (US3)
                │                    │
Phase 6 (US4) ←─┴── depends on US1 event_mapper/RunExecutor
Phase 7 (US5) ←── depends on RunExecutor + repositories + US3 projection (T025 before T033)
Phase 8 (US6) ←── depends on RunExecutor
    ↓
Phase 9 (US7) — requires US1–US6 complete (big-bang gate)
    ↓
Phase 10 (Polish)
```

### User Story Dependencies

| Story | Depends on | Notes |
|-------|------------|-------|
| US1 Real-time streaming | Phase 2 | MVP — chat native stream |
| US2 Research structure | Phase 2, US1 RunExecutor | Shares executor |
| US3 History continuity | Phase 2, US1 | Projection + backfill |
| US4 Sources | US1 event_mapper | Tool result extraction |
| US5 Stop/concurrency | US1 RunExecutor, **US3 projection (T025)** | T033 partial content requires incremental projection |
| US6 Observability | US1, US2 | Trace both paths |
| US7 Regression | All above | Deploy gate |

### Parallel Opportunities

**Phase 2 parallel batch**: T005, T006, T007, T008, T010, T011, T013 (after T004 started)

**After Phase 2**:
- US1 (T014–T018) and US2 prep (T019–T020) can overlap if RunExecutor skeleton (T012) is done
- US4 (T028–T30) parallel with US5 tests (T031–T032a) once US1 complete
- US5 implementation (T033a–T036) requires US3 T025 complete before T033
- US6 (T037–T38) parallel with US5 timeout/concurrency (T033a–T035)

---

## Parallel Example: User Story 1

```bash
# Tests in parallel:
T014: apps/backend/tests/unit/test_event_mapper.py
T015: apps/backend/tests/integration/test_streaming_native.py

# Then sequential:
T016 → T017 → T018 (run_executor.py → agent_service.py → tracing)
```

---

## Parallel Example: Foundational Phase

```bash
# After T004 main.py AgentOS mount starts:
T005 jwt_middleware.py + T006 orphan_cleanup.py + T007 concurrency.py
T008 message_run_repository.py + research_repository.py + concurrency.py cross-table count
T010 research_agent.py + T011 event_mapper.py + T013 projection.py
# Then T009 search_agent.py → T012 run_executor.py
```

---

## Implementation Strategy

### Development Order (big-bang deploy)

1. Complete Phase 1 + Phase 2 (foundation)
2. US1 → US2 → US3 (all P1 — core refactor)
3. US4 + US5 + US6 (P2 — can parallelize)
4. US7 contract gate — **do not deploy until green**
5. Phase 10 polish + Railway deploy with backfill

### MVP Scope (development validation only)

Phases 1–3 (through US1) prove native streaming on chat — sufficient for early demo, **not** sufficient for production (big-bang requires US7 gate).

### Task Count Summary

| Phase | Tasks | Story |
|-------|-------|-------|
| 1 Setup | 3 | — |
| 2 Foundational | 10 | — |
| 3 US1 | 5 | Real-time streaming |
| 4 US2 | 5 | Research structure (+ cost persistence) |
| 5 US3 | 4 | History continuity |
| 6 US4 | 3 | Source citations |
| 7 US5 | 8 | Stop/concurrency (+ timeout, contract test) |
| 8 US6 | 2 | Observability |
| 9 US7 | 4 | Regression gate |
| 10 Polish | 5 | — |
| **Total** | **49** | |

---

## Notes

- All tasks include exact file paths per speckit format
- `[P]` tasks touch different files — safe to parallelize
- Deploy only after T039–T042 pass (US7 big-bang gate)
- Run `apps/backend/scripts/backfill_chat_agno_sessions.py` once after deploy (T027)
- Constitution requires tests for backend changes — unit/integration included; contract suite is mandatory gate
