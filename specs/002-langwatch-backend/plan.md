# Implementation Plan: LangWatch Backend Observability

**Branch**: `002-langwatch-backend` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-langwatch-backend/spec.md`

## Summary

Add optional LangWatch tracing to `apps/backend` using the official Agno integration
(`langwatch.setup` + `AgnoInstrumentor`). Initialize at FastAPI startup when `LANGWATCH_API_KEY`
is set; wrap each `agent.run` with a LangWatch trace carrying `run_id`, `session_id`,
`auth_subject`, and `environment`. No chat API, database, or frontend changes. Document env vars in
`.env.example`, backend README, and Railway deployment notes.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Agno, `langwatch`, `openinference-instrumentation-agno` (new);
existing OpenRouter + DuckDuckGoTools agent stack unchanged  
**Storage**: N/A (no schema changes; traces stored in LangWatch)  
**Testing**: pytest unit tests for conditional LangWatch setup; manual LangWatch UI verification
per quickstart  
**Target Platform**: Local dev + Railway Linux backend service (`agentos-chat-backend`)  
**Project Type**: Backend-only observability addition to existing RAG web monorepo  
**Performance Goals**: No measurable regression to chat success rate (SC-002, SC-005); traces
visible within 60s of run completion when enabled (SC-001)  
**Constraints**: LangWatch optional everywhere; full trace content in all environments; single
LangWatch project with `environment` tag; `AGNO_TELEMETRY` unchanged when LangWatch enabled  
**Scale/Scope**: One new module (`observability/langwatch.py` or similar), settings fields, lifespan
hook, agent service trace wrapper, env template + docs

**Environment variables**:

| Variable | Purpose |
|----------|---------|
| `LANGWATCH_API_KEY` | Enables LangWatch when non-empty |
| `LANGWATCH_ENDPOINT` | Optional self-hosted endpoint |
| `APP_ENVIRONMENT` | `local` \| `staging` \| `production` trace tag |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Grounded RAG and Agent Behavior**: PASS (N/A for grounding). Agent tools and behavior unchanged;
  LangWatch adds execution traces (prompts, tool calls, completions) per principle I traceability.
- **Auth0-Centered Security Boundaries**: PASS WITH TRUSTED OBSERVABILITY STORE. Full message
  content exported to LangWatch in all environments (clarified). `auth_subject` on traces; chat API
  authorization unchanged. LangWatch project access limited to maintainers.
- **Typed API and UI Contracts**: PASS. No OpenAPI or Astro contract changes.
- **PostgreSQL and pgvector Integrity**: PASS (N/A). No migrations.
- **Railway-Ready Delivery and Observability**: PASS. Optional `LANGWATCH_API_KEY` on Railway;
  `APP_ENVIRONMENT` for prod/staging tags; structured logs retained; quickstart documents
  post-deploy trace verification.

**Post-Design Recheck**: PASS. Research, data model, trace metadata contract, and quickstart align
with all gates. No justified violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-langwatch-backend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── langwatch-trace-metadata.md
└── tasks.md             # Phase 2 — /speckit.tasks
```

### Source Code (repository root)

```text
apps/backend/
├── pyproject.toml                    # + langwatch, openinference-instrumentation-agno
├── .env.example                      # + LANGWATCH_*, APP_ENVIRONMENT
├── README.md                         # LangWatch setup section
└── src/agentos_chat/
    ├── main.py                       # lifespan: configure_langwatch()
    ├── settings.py                   # langwatch_api_key, app_environment, endpoint
    ├── observability/
    │   └── langwatch.py              # setup + trace_run_context helper
    ├── services/
    │   ├── agent_service.py          # wrap agent.run with trace metadata
    │   └── logging.py                # optional langwatch_export_failed event
    └── tests/
        └── unit/
            └── test_langwatch.py     # conditional setup tests

infra/railway/                        # document optional env vars (README or railway_up notes)
Makefile                              # no change required; existing smoke still valid
```

**Structure Decision**: Add `agentos_chat/observability/` for LangWatch wiring; keep agent logic in
`agent_service.py` with a thin trace wrapper to satisfy FR-009 without bloating `main.py`.

## Implementation Phases (for /speckit.tasks)

### Phase A — Dependencies and settings (foundational)

1. Add `langwatch` and `openinference-instrumentation-agno` to `pyproject.toml`.
2. Extend `Settings`: `langwatch_api_key`, `langwatch_endpoint`, `app_environment` (validated enum).
3. Update `.env.example` with placeholders and comments.

### Phase B — Startup instrumentation (P1)

4. Implement `configure_langwatch()`:
   - If no API key → log `langwatch_disabled` and return.
   - Else set `os.environ["LANGWATCH_API_KEY"]` if needed, apply `LANGWATCH_ENDPOINT` when
     configured, call `langwatch.setup(instrumentors=[AgnoInstrumentor()])`.
   - Log `langwatch_enabled` with `environment` only (never log key); on setup failure log
     `langwatch_setup_failed` without secrets.
5. Call from `lifespan` in `main.py` after `configure_logging()`.

### Phase C — Per-run metadata (P1)

6. Implement `trace_agent_run(run_id, session_id, auth_subject)` context manager using LangWatch
   trace API; set metadata per `contracts/langwatch-trace-metadata.md`.
7. Wrap `agent.run(...)` in `agent_service._execute_run` inside that context.
8. On export/setup errors in run path, log and continue (FR-006).

### Phase D — Docs and Railway (P3)

9. Update `apps/backend/README.md` and `specs/002-langwatch-backend/quickstart.md` cross-links.
10. Document optional Railway variables in `infra/railway/` or root README (no deploy gate).

### Phase E — Tests

11. Unit test: no setup when key missing; setup called when key present (mock `langwatch.setup`).
12. Manual verification checklist in quickstart (SC-001, SC-007, SC-008).

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Generated Artifacts

| Artifact | Path |
|----------|------|
| Research | [research.md](./research.md) |
| Data model | [data-model.md](./data-model.md) |
| Trace metadata contract | [contracts/langwatch-trace-metadata.md](./contracts/langwatch-trace-metadata.md) |
| Quickstart | [quickstart.md](./quickstart.md) |

## Next Command

Run **`/speckit.tasks`** to generate dependency-ordered `tasks.md` from this plan.
