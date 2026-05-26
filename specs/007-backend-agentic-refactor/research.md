# Research: Backend Agentic Architecture Refactor

## Decision: AgentOS `base_app` Integration (Not Full Route Replacement)

**Decision**: Mount agents and teams on `AgentOS(agents=[...], teams=[...], db=PostgresDb(...), base_app=app, lifespan=merged_lifespan)` while **keeping existing custom FastAPI routers** for chat/research session CRUD, owner filtering, and SSE endpoints. AgentOS owns agent registration, session DB schema, and run execution primitives; custom routes remain the public API boundary (FR-010).

**Rationale**: Frontend contracts are frozen. AgentOS provides native `arun(stream=True, stream_events=True)`, PostgresDb session storage, and typed run events — but the product needs owner-scoped domain tables, article versioning, and custom SSE event shapes the frontend already consumes.

**Alternatives considered**:
- Full migration to AgentOS HTTP routes only: would break existing `/api/chat/*` and `/api/research/*` paths.
- Keep 100% custom execution with no AgentOS: duplicates run lifecycle, session storage, and streaming that Agno 2.4 already ships.

## Decision: Shared `RunExecutor` Service for Chat and Research

**Decision**: Introduce `services/run_executor.py` — a single async execution pipeline that:
1. Validates concurrency (per-session + per-user cap of 10)
2. Calls `agent.arun(...)` or `team.arun(...)` with `stream=True, stream_events=True`
3. Maps Agno `RunOutputEvent` / `TeamRunOutputEvent` instances to existing SSE event types via `isinstance` checks
4. Persists partial content on stop; projects final state to domain tables

**Rationale**: Satisfies SC-010 (one pattern for both workflows), eliminates fake chunk loops and sync `asyncio.to_thread` bridges, and centralizes cancel/timeout/orphan handling.

**Alternatives considered**:
- Separate executors per feature: duplicates cancel, timeout, tracing, and projection logic.
- AgentOS SSE routes directly: incompatible with current frontend event schema without frontend changes.

## Decision: Native Async Streaming (`arun`) Replacing Fake Chunking

**Decision**: Replace `agent.run(prompt, stream=False)` + manual 24-char chunk loop with:

```python
async for event in agent.arun(prompt, session_id=..., stream=True, stream_events=True):
    ...
```

Map `RunContentEvent` → `token`, `ToolCallStartedEvent` → `thinking`, `RunCompletedEvent` → finalize + `done`.

**Rationale**: FR-001/FR-002, SC-001, SC-009. Removes artificial `asyncio.sleep(0.02)` latency and unlocks real tool-call progress events.

**Alternatives considered**:
- Sync `run(stream=True)` in thread + `run_coroutine_threadsafe`: current research pattern; harder to cancel and reason about.

## Decision: Research `output_schema=ResearchResult` Replacing Delimiter Parsing

**Decision**: Add `output_schema=ResearchResult` to the research `Team` with `use_json_mode=True` (or model-native structured output). Delete `COORDINATOR_PROMPT` delimiter blocks and `parse_research_output()` regex pipeline.

**Rationale**: FR-003, SC-002. Eliminates format drift (`---CHAT_START---` forgotten → empty article).

**Alternatives considered**:
- Keep delimiter contract with stronger prompt: fragile; already failing in production.
- Separate agent calls for chat vs article: more latency and cost.

## Decision: Agent Session Store Authoritative; Domain Tables as Projection

**Decision**:
- **Chat**: `PostgresDb(session_table="chat_agno_sessions")` stores conversation history. `chat_messages` rows are written/updated by a projection layer after each run (including streaming partials and stopped status).
- **Research**: Existing `research_agno_sessions` table remains authoritative for agent context; `research_messages` continues as projection (already partially true).

On deploy, run a one-time backfill script to seed agent session store from existing `chat_messages` where session store is empty.

**Rationale**: Clarification Q3 (agent store authoritative). Agents use `add_history_to_context=True` without manual `format_user_prompt()` string stitching.

**Alternatives considered**:
- Domain tables authoritative: contradicts clarified spec; manual history injection stays.
- Dual-write with no winner: reconciliation complexity on every read.

## Decision: Tavily Tool Results for Source Extraction

**Decision**: Extract sources from `RunOutput.tools` / `ToolCallCompletedEvent` Tavily payloads (title, url, content snippet) instead of URL regex on final text.

**Rationale**: FR-006, SC-004. Tavily already returns structured results; regex yields `title == url`.

**Alternatives considered**:
- Citations from model response only: unreliable; model may omit or hallucinate URLs.

## Decision: Startup Agent Registration + Credential Injection

**Decision**: Register search `Agent` and research `Team` once in FastAPI lifespan. Pass `api_key=` to `OpenRouter(...)` and `TavilyTools(...)` directly from `Settings`. Remove per-request `os.environ[...]` mutation.

**Rationale**: FR-015, FR-016. Thread-safe under concurrent runs.

## Decision: JWKS Refresh in Lifespan

**Decision**: Move Auth0 JWKS fetch from module import to lifespan startup; schedule periodic refresh (e.g., every 6 hours or on verification failure). Store keys in `app.state.jwt_verification_keys`.

**Rationale**: FR-018. Avoids startup failure when Auth0 is briefly unreachable and supports key rotation without redeploy.

**Alternatives considered**:
- Fetch on every request: too slow.
- Static keys at import: current brittle behavior.

## Decision: Concurrency Enforcement

**Decision**:
- Per-session: reject with `409` + `{code: "run_in_progress"}` if `QUEUED|RUNNING|STOPPING` run exists (chat **and** research).
- Per-user: sum active runs in `agent_runs` (chat) and `research_agent_runs` (research); reject 11th with `{code: "concurrent_run_limit", message: "...max 10..."}`.

Implement in shared guard called from message submission endpoints before spawning executor.

**Rationale**: Clarifications Q1, Q5; FR-009, FR-009a, SC-011.

## Decision: Orphan Run Recovery on Startup

**Decision**: Lifespan startup query sets all `RUNNING|QUEUED|STOPPING` runs to `FAILED` with `error_code=orphaned` (or `STOPPED` if partial content exists).

**Rationale**: FR-017, SC-006.

## Decision: LangWatch Tracing for Both Chat and Research

**Decision**: Wrap `RunExecutor.execute(...)` with existing `trace_agent_run()` context for chat; extend same wrapper to research (currently missing).

**Rationale**: FR-013, SC-008. AgnoInstrumentor already loaded at startup.

## Decision: Pin Agno Version

**Decision**: Change `pyproject.toml` from `agno>=1.7.0` to `agno>=2.4,<3`.

**Rationale**: Installed 2.4.7; event types and AgentOS APIs differ from 1.x. Prevents silent breaking upgrades.

## Decision: Big-Bang Cutover (No Feature Flag Split)

**Decision**: Single PR/deploy switches chat and research execution to `RunExecutor` + AgentOS-backed agents. All contract tests must pass before merge.

**Rationale**: Clarification Q4. Avoids mixed architecture operational complexity.

## Decision: No New Railway Services for v1

**Decision**: Keep in-process `RunEventBus` for SSE (single Railway replica). Document multi-replica limitation in plan risks.

**Rationale**: Spec assumption; Redis pub/sub deferred unless load testing fails SC-005.

## Environment Variables (Consolidated)

| Variable | Change | Purpose |
|----------|--------|---------|
| `AGNO_TELEMETRY` | Wire to Agent/Team `telemetry=` | FR-020 |
| `TAVILY_API_KEY` | Already present | TavilyTools |
| `OPENROUTER_API_KEY` | Pass via constructor | Model auth |
| Existing Auth0/LangWatch vars | Unchanged | Auth + tracing |

No new mandatory env vars for v1.
