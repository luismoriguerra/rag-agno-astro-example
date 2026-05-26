# Implementation Plan: Backend Agentic Architecture Refactor

**Branch**: `007-backend-agentic-refactor` | **Date**: 2026-05-25 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/007-backend-agentic-refactor/spec.md`

## Summary

Refactor `apps/backend` from a custom agent execution stack (sync runs, fake streaming, regex research parsing, manual history injection) into a well-structured Agno 2.4 / AgentOS-backed architecture with a shared async `RunExecutor`, native `arun` streaming, structured research output, agent session store as history authority, and domain-table projections — while preserving all existing REST/SSE contracts for chat and research in a single big-bang release.

## Technical Context

**Language/Version**: Python 3.12 (backend only; frontend unchanged)  
**Primary Dependencies**: FastAPI, Agno 2.4+ / AgentOS, OpenRouter, TavilyTools, Pydantic, SQLAlchemy async, Alembic, LangWatch + openinference-instrumentation-agno  
**Storage**: PostgreSQL — existing domain tables + Agno `PostgresDb` session tables (`chat_agno_sessions`, `research_agno_sessions`); no pgvector changes  
**Testing**: pytest (unit, contract, integration, scenarios); existing contract suite is the regression gate  
**Target Platform**: Local development + Railway Linux (single backend replica v1)  
**Project Type**: Backend refactor within existing RAG web application monorepo  
**Performance Goals**: First SSE event within 3s (SC-001); ≥30% median time-to-first-token improvement (SC-009); stop within 10s (SC-005)  
**Constraints**: No frontend changes; no new Railway services; max 10 concurrent runs per user; Auth0 JWT unchanged  
**Scale/Scope**: ~15 backend files touched/added; remove ~200 lines of delimiter parsing and fake streaming; pin `agno>=2.4,<3`

**Environment variables (unchanged set; wiring fixes only)**:
- `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `AGNO_TELEMETRY`, Auth0 vars, LangWatch vars — all existing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Grounded RAG and Agent Behavior**: PASS. TavilyTools remains sole web grounding source. Sources extracted from tool results (not URL regex). Chat = single agent; research = coordinator + writer team with `output_schema`. Safe progress only in SSE; traces via LangWatch for both workflows. Tool permissions: Tavily search only.
- **Auth0-Centered Security Boundaries**: PASS. Existing JWTMiddleware + scope check preserved. JWKS refresh moved to lifespan (improvement). Owner filtering unchanged. Research routes explicitly in scope enforcement. New 409 responses are auth-safe (no data leak).
- **Typed API and UI Contracts**: PASS. [contracts/api-stability.md](./contracts/api-stability.md) documents frozen external contract. Only additive 409 error codes. SSE event names unchanged. Frontend not modified.
- **PostgreSQL and pgvector Integrity**: PASS. No vector search. Agno session tables auto-provisioned. Domain tables remain for owner filtering and restore. Optional backfill script; no destructive migration. Projection invariants documented in [data-model.md](./data-model.md).
- **Railway-Ready Delivery and Observability**: PASS. Same Railway service. Lifespan adds orphan cleanup + JWKS refresh + engine dispose. Structured logs preserved. LangWatch extended to research. [quickstart.md](./quickstart.md) defines verification. Contract tests gate deploy.

**Post-Design Recheck**: PASS. Research decisions, data model, and contracts satisfy all gates. No constitution violations requiring complexity tracking.

## Project Structure

### Documentation (this feature)

```text
specs/007-backend-agentic-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Two-layer persistence model
├── quickstart.md        # Verification steps
├── contracts/
│   ├── api-stability.md # Frozen external API
│   └── run-execution.md # Internal RunExecutor contract
└── tasks.md             # Phase 2 (/speckit.tasks — not yet created)
```

### Source Code (repository root)

```text
apps/backend/
├── src/agentos_chat/
│   ├── main.py                    # AgentOS + base_app; merged lifespan
│   ├── settings.py                # Wire agno_telemetry; no env mutation
│   ├── agents/
│   │   ├── search_agent.py        # Factory → lifespan-registered Agent + PostgresDb
│   │   └── research_agent.py      # Team + output_schema; remove regex parser
│   ├── services/
│   │   ├── run_executor.py        # NEW: shared async execution pipeline
│   │   ├── event_mapper.py        # NEW: Agno events → SSE events
│   │   ├── projection.py          # NEW: agent store → domain tables
│   │   ├── agent_service.py       # Slim: submit/stop → RunExecutor
│   │   ├── research_service.py    # Slim: delegates to RunExecutor
│   │   ├── run_events.py          # Keep in-process SSE bus (v1)
│   │   └── concurrency.py         # NEW: per-session + per-user guards
│   ├── auth/
│   │   └── jwt_middleware.py      # JWKS refresh helper (called from lifespan)
│   ├── observability/
│   │   └── langwatch.py           # Extend trace to research runs
│   ├── api/
│   │   ├── messages.py            # Add 409 for chat concurrent run
│   │   └── research_sessions.py   # Add concurrent_run_limit 409
│   └── db/
│       ├── message_run_repository.py  # has_active_chat_run for chat sessions
│       └── research_repository.py     # has_active_research_run; research-side active count
│   # concurrency.py sums both repos for FR-009a user cap
├── migrations/versions/
│   └── 004_chat_active_run_index.py  # Optional: index for concurrency queries
├── scripts/
│   └── backfill_chat_agno_sessions.py  # NEW: one-time history seed
└── tests/
    ├── unit/test_run_executor.py
    ├── unit/test_event_mapper.py
    ├── unit/test_concurrency.py
    ├── integration/test_streaming_native.py
    └── contract/                  # Must all pass unchanged
```

**Structure Decision**: Extend existing `apps/backend/src/agentos_chat/` layout. Introduce `services/run_executor.py` as the single execution entry point. Agent factories become registration helpers called from lifespan. Delete obsolete code paths (`format_user_prompt`, `parse_research_output`, fake chunk loops, sync thread bridges) after RunExecutor is wired.

## Implementation Phases

### Phase A — Foundation (blocking)

1. Pin `agno>=2.4,<3`; fix `[[tool.mypy.overrides]]` in pyproject.toml
2. Add `PostgresDb` for chat (`chat_agno_sessions`); register agents in lifespan with direct `api_key=` injection
3. Implement `concurrency.py` guards (session + user cap 10)
4. Move JWKS fetch to lifespan; add `engine.dispose()` on shutdown
5. Orphan run cleanup on startup

### Phase B — RunExecutor Core

1. `event_mapper.py`: Agno event → SSE mapping via `isinstance`
2. `run_executor.py`: async `arun` loop for chat; cancel/timeout/tracing
3. `projection.py`: domain table sync from run state
4. Refactor `agent_service.py` to delegate; remove fake streaming

### Phase C — Research Migration

1. Add `output_schema=ResearchResult` to Team; remove delimiter prompts/parser
2. Refactor `research_service.py` to use RunExecutor
3. Extend LangWatch tracing to research runs

### Phase D — Sources, Guards, Polish

1. Tavily tool-result source extraction (replace URL regex)
2. Chat `has_active_run` + 409 on concurrent message
3. `concurrent_run_limit` 409 on research + chat create/message paths
4. Backfill script for existing chat sessions

### Phase E — Verification & Deploy

1. New unit/integration tests per quickstart
2. Full contract suite pass
3. Baseline vs post-refactor time-to-first-token measurement
4. Big-bang Railway deploy with backfill

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Agno 2.x event API drift | Pin `<3`; unit test event_mapper with recorded fixtures |
| Projection drift vs agent store | Integration test: restore API == agent history |
| Single-replica SSE | Document; defer Redis if needed |
| Big-bang regression | Contract test gate; no merge without 100% pass |
| Backfill incomplete | Script idempotent; log sessions needing manual review |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
