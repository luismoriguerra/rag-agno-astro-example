# Contract: LangWatch Trace Metadata

## Purpose

Defines required metadata on every LangWatch trace produced by the chat backend for an agent run.
This is not an HTTP API contract; it is the observability interface between the backend and the
LangWatch dashboard.

## When Traces Are Emitted

| Condition | Behavior |
|-----------|----------|
| `LANGWATCH_API_KEY` unset or empty | No LangWatch setup; no traces exported |
| `LANGWATCH_API_KEY` set | `langwatch.setup` at startup; traces on each `agent.run` |
| Export failure | Chat API unaffected; structured log event `langwatch_export_failed` (or `langwatch_setup_failed` at startup) |

## Root Trace Metadata (required)

Every chat agent run MUST attach these key-value attributes on the root trace (or equivalent
LangWatch trace context wrapping `agent.run`):

| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `run_id` | string (UUID) | `550e8400-e29b-41d4-a716-446655440000` | Matches `AgentRun.id` |
| `session_id` | string (UUID) | `6ba7b810-9dad-11d1-80b4-00c04fd430c8` | Matches `ChatSession.id` |
| `auth_subject` | string | `mock\|local-dev-user` | Auth0 `sub` or mock subject |
| `environment` | enum string | `local` | One of: `local`, `staging`, `production` |

## Child Spans (automatic)

When LangWatch is enabled, `AgnoInstrumentor` MUST produce child spans for:

- LLM / model calls (includes full prompt and completion text per spec)
- Tool calls (e.g. DuckDuckGo search), including tool inputs/outputs as captured by OpenInference

No additional HTTP routes are added for span delivery; export uses LangWatch SDK → LangWatch SaaS
(or `LANGWATCH_ENDPOINT`).

## Correlation with Structured Logs

Existing JSON log events remain unchanged. Maintainers MAY correlate logs to LangWatch using
shared `run_id` and `session_id`:

```json
{"event": "agent_run_start", "run_id": "...", "session_id": "..."}
```

## Verification Checklist

1. Set `LANGWATCH_API_KEY` and `APP_ENVIRONMENT=local`.
2. Start backend; confirm startup log indicates LangWatch enabled (no secret values logged).
3. Submit one chat message via API or `/chat`.
4. In LangWatch, locate trace within 60s with metadata `run_id`, `session_id`, `auth_subject`,
   `environment=local`.
5. Confirm nested model and tool spans are visible.

## Out of Scope

- LangWatch prompt management APIs
- Frontend trace propagation
- Changes to OpenAPI `/v1/*` chat endpoints
