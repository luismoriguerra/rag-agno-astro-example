# API Stability Contract: Backend Agentic Refactor

**Version**: 0.2.0 (internal refactor; external contract unchanged)  
**Base**: [001-agentos-chat-search/contracts/openapi.yaml](../../001-agentos-chat-search/contracts/openapi.yaml), [005-research-generator/contracts/research-api.md](../../005-research-generator/contracts/research-api.md)

## Principle

All existing REST paths, request bodies, response shapes, and SSE event names **MUST remain compatible** with the current Astro frontend. This refactor changes backend execution only (FR-010).

## Unchanged Endpoints

### Chat

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | Unchanged |
| GET/POST | `/api/chat/sessions` | Unchanged |
| GET/DELETE | `/api/chat/sessions/{session_id}` | Unchanged |
| POST | `/api/chat/sessions/{session_id}/messages` | 202 Accepted; may now return 409 (see below) |
| GET | `/api/chat/runs/{run_id}/stream` | SSE; same event names |
| POST | `/api/chat/runs/{run_id}/stop` | 202 Accepted |

### Research

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/research/sessions` | Unchanged |
| GET | `/api/research/sessions` | Unchanged |
| GET/DELETE | `/api/research/sessions/{session_id}` | Unchanged |
| POST | `/api/research/sessions/{session_id}/messages` | Unchanged |
| POST | `/api/research/sessions/{session_id}/retry` | Unchanged |
| GET | `/api/research/runs/{run_id}/stream` | SSE; same event names |
| POST | `/api/research/runs/{run_id}/stop` | Unchanged |
| PATCH | `/api/research/articles/{article_id}/status` | Unchanged |

## New Error Responses (Backward-Compatible Additions)

These status codes may appear where previously only 404 was returned. Frontend SHOULD handle 409 if not already.

### 409 Conflict — Run In Progress (Chat)

**When**: POST `/api/chat/sessions/{session_id}/messages` while session has active run.

```json
{
  "code": "run_in_progress",
  "message": "An agent run is already in progress."
}
```

### 409 Conflict — Concurrent Run Limit

**When**: POST message/create-session that would start an 11th active run for the user.

```json
{
  "code": "concurrent_run_limit",
  "message": "You have reached the maximum of 10 concurrent agent runs. Wait for a run to finish or stop one."
}
```

## SSE Event Contract (Unchanged Names)

Clients MUST continue to parse these `event:` types:

| Event | Payload keys (minimum) |
|-------|------------------------|
| `thinking` | `status`, `message` |
| `token` | `text` |
| `source` | `title`, `url`, `snippet`, `rank` |
| `article` | `markdown`, `version`, `title` |
| `article_preview` | `markdown`, `title` |
| `actions` | `actions` (string array) |
| `reasoning` | `content` (research only; optional; **redacted phase summary** — never raw chain-of-thought) |
| `done` | `run_id`, `status` |
| `error` | `code`, `message` |

**Behavior change (allowed)**: `token` events arrive at real generation cadence instead of post-hoc chunks. `thinking` events may appear earlier/more frequently from tool-call mapping.

### Reasoning Visibility (Constitution-Aligned)

- **MUST NOT** stream raw model chain-of-thought to clients via any SSE event.
- `thinking` events carry safe, user-facing progress strings (e.g., "Searching…", "Delegating to writer…").
- `reasoning` event (research only, optional) carries a **redacted phase summary** aggregated at run end — e.g., delegation milestones and tool-use counts — not reasoning tokens or internal deliberation.
- Full reasoning deltas belong in LangWatch traces and optional operator-only DB fields (`research_messages.reasoning_content`), not in SSE payloads.

## Authentication

Unchanged: Auth0 Bearer JWT, `access:api` scope, owner-filtered resources.

## Contract Test Gate

Before deploy, MUST pass:

- `tests/contract/test_chat_*.py`
- `tests/contract/test_research_*.py`
- `tests/contract/test_stop_run_contract.py`
- `tests/contract/test_concurrent_run_limit_contract.py` (SC-011)

SC-007: 100% pass rate.
