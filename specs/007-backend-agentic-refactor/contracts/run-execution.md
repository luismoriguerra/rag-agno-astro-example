# Internal Contract: Run Execution Pipeline

**Audience**: Backend implementers  
**Stability**: Internal — not exposed to frontend

## RunExecutor Interface

```python
class RunExecutor:
    async def execute_chat_run(
        self,
        *,
        run_id: UUID,
        session_id: UUID,
        user_identity_id: UUID,
        auth_subject: str,
        user_content: str,
    ) -> None: ...

    async def execute_research_run(
        self,
        *,
        run_id: UUID,
        session_id: UUID,
        user_identity_id: UUID,
    ) -> None: ...
```

## Pre-Execution Guards (MUST run before spawning background task)

1. **Owner check** — session belongs to `user_identity_id`
2. **Session active run** — no `queued|running|stopping` run for this session → else `409 run_in_progress`
3. **User active run count** — sum of active chat runs (`agent_runs`) plus active research runs (`research_agent_runs`) for `user_identity_id` MUST be `< 10` → else `409 concurrent_run_limit`

## Agno Event → SSE Mapping

| Agno event type | SSE event | Notes |
|-----------------|-----------|-------|
| `RunContentEvent` / team content | `token` | Stream text deltas |
| `ToolCallStartedEvent` | `thinking` | Safe message e.g. "Searching…" |
| `RunStartedEvent` (member agent) | `thinking` | "Delegating to {name}…" |
| `ToolCallCompletedEvent` (Tavily) | `source` | Extract structured sources |
| `ModelRequestCompletedEvent` | (internal) | Token counts → cost records (research) |
| `ReasoningContentDeltaEvent` | `thinking` | Map to safe progress string only; never forward raw delta text |
| `RunCompletedEvent` / `TeamRunCompleted` | (internal) | Finalize projection |
| Research run end (optional) | `reasoning` | Redacted phase summary only (delegation/tool milestones) |
| Terminal | `done` | `{run_id, status}` |
| Exception / timeout | `error` | User-friendly message |

**MUST NOT** emit raw chain-of-thought to any user-visible SSE event. Research `reasoning` event (if emitted) carries a redacted phase summary at run end — not model reasoning tokens. Operator-only `reasoning_content` DB projection and LangWatch spans MAY retain fuller detail for debugging.

## Cancellation

- `run_event_bus.request_cancel(run_id)` checked between events
- On cancel: persist partial content, status `stopped`, emit `done`

## Timeout

- Chat: `settings.request_timeout_seconds` (default 60)
- Research: `settings.research_timeout_seconds` (default 300)
- On timeout: status `failed`, code `timeout`, emit `error` + `done`

## Projection Hooks

After terminal state:

| Workflow | Project to |
|----------|------------|
| Chat | `chat_messages`, `search_results`, `agent_runs` |
| Research | `research_messages`, `research_article_versions`, `research_costs`, `agent_runs` |

Agent session store writes happen automatically via Agno `db=` + `session_id`.

## Tracing

Wrap entire `execute_*` body in `trace_agent_run(run_id, session_id, auth_subject)` when LangWatch enabled.

## Agent Registration (lifespan)

```python
search_agent = Agent(model=..., db=chat_db, tools=[TavilyTools(...)], ...)
research_team = Team(model=..., db=research_db, output_schema=ResearchResult, ...)
agent_os = AgentOS(agents=[search_agent], teams=[research_team], base_app=app, ...)
```

Agents registered once; per-run `session_id` and `user_id` passed to `arun`.
