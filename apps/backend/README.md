# AgentOS Chat Backend

FastAPI service for search-backed chat and research with Agno 2.4+ / AgentOS, PostgreSQL, and Tavily.

## Architecture

The backend uses **AgentOS** as the runtime, mounting a custom FastAPI app (`base_app`) with existing chat and research routers. Key components:

| Module | Purpose |
|--------|---------|
| `services/run_executor.py` | Shared async execution pipeline for chat and research runs |
| `services/event_mapper.py` | Maps Agno events to SSE events (`token`, `thinking`, `source`, etc.) |
| `services/projection.py` | Syncs agent run state to domain tables for API restore |
| `services/concurrency.py` | Per-session + per-user (max 10) run guards |
| `services/orphan_cleanup.py` | Marks stuck runs as failed on startup |
| `agents/search_agent.py` | Chat search agent factory with PostgresDb session store |
| `agents/research_agent.py` | Research team with `output_schema=ResearchResult` |

### Session History

The **Agno session store** (`chat_agno_sessions`, `research_agno_sessions`) is authoritative for agent conversation context. Domain tables (`chat_messages`, `research_messages`) are maintained as read projections for REST API restore and owner-scoped queries.

### Concurrency Limits

- **Per-session**: One active run at a time per chat or research session (409 `run_in_progress`)
- **Per-user**: Maximum 10 concurrent active runs across all sessions (409 `concurrent_run_limit`)
- Active-run count sums both `agent_runs` and `research_agent_runs` tables

### Backfill Script

After deploying the refactored backend, run the backfill script once to seed the Agno session store for pre-existing chat sessions:

```bash
cd apps/backend && python -m scripts.backfill_chat_agno_sessions
```

Existing sessions will gain full history context on their next message via `add_history_to_context=True`.

## LangWatch Tracing (optional)

When `LANGWATCH_API_KEY` is set, both chat and research agent runs are exported to [LangWatch](https://langwatch.ai/) using the [Agno integration](https://docs.agno.com/observability/langwatch). Tracing is disabled when the key is empty; chat and research continue to work normally.

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LANGWATCH_API_KEY` | To enable tracing | (empty) | LangWatch API key |
| `LANGWATCH_ENDPOINT` | No | SaaS | Self-hosted LangWatch base URL |
| `APP_ENVIRONMENT` | No | `local` | Trace tag: `local`, `staging`, or `production` |

`AGNO_TELEMETRY` is independent of LangWatch.

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | localhost | PostgreSQL connection |
| `OPENROUTER_API_KEY` | Yes | — | Model provider |
| `TAVILY_API_KEY` | Yes | — | Web search provider |
| `AUTH0_DOMAIN` | For auth | — | Auth0 tenant |
| `AUTH0_ISSUER` | For auth | — | Auth0 issuer URL |
| `AUTH0_API_AUDIENCE` | For auth | — | Auth0 API audience |
| `AGENT_MODEL` | No | `openrouter/google/gemini-2.0-flash-001` | Chat model |
| `RESEARCH_AGENT_MODEL` | No | `deepseek/deepseek-v4-flash:nitro` | Research model |
| `REQUEST_TIMEOUT_SECONDS` | No | 60 | Chat run timeout |
| `RESEARCH_TIMEOUT_SECONDS` | No | 300 | Research run timeout |
