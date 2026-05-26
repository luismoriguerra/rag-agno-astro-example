# Quickstart: Backend Agentic Architecture Refactor

## Prerequisites

- Python 3.12, Node.js 22 (frontend unchanged but useful for E2E)
- PostgreSQL running locally
- `.env` configured per `apps/backend/.env.example` plus valid `OPENROUTER_API_KEY` and `TAVILY_API_KEY`

## Setup

```bash
make install
make dev   # or: cd apps/backend && alembic upgrade head && uvicorn ...
```

Ensure `agno>=2.4,<3` after dependency pin:

```bash
cd apps/backend && pip show agno | grep Version
```

## Verification Checklist

### 1. Contract tests (regression gate)

```bash
cd apps/backend && pytest tests/contract/ -v
```

Expected: all pass (SC-007).

### 2. Real streaming (not fake chunks)

1. Submit a chat message via UI or API.
2. Observe SSE: `thinking` within 3s, then `token` events before run completes.
3. Confirm no long pause followed by rapid token burst (old fake-stream signature).

### 3. Chat concurrent run rejection

1. Start a long chat run (complex question).
2. Before completion, POST second message to same session.
3. Expect HTTP 409 `{code: "run_in_progress"}`.

### 4. Per-user run limit

1. Create 10 sessions with active runs (or mock via DB/integration test).
2. Submit 11th run.
3. Expect HTTP 409 `{code: "concurrent_run_limit"}`.

### 5. Stop preserves partial content

1. Start research run.
2. Stop mid-flight.
3. Reload session — assistant message shows partial text, status stopped.

### 6. Research structured output

1. Create research session with new topic.
2. On completion: chat panel summary, article panel markdown, action chips present.
3. Ask summary-only follow-up — article panel unchanged.

### 7. Source citations

1. Chat question requiring web search.
2. Verify `source` SSE events include `title` ≠ `url` when Tavily provides titles.

### 8. Session history continuity

1. Chat three turns with follow-up referencing prior answer.
2. Reload page, send fourth message — context preserved.

### 9. Orphan recovery

1. Start run, kill backend process (`SIGTERM`).
2. Restart backend.
3. Verify run status is `failed` (orphaned), not stuck `running` (SC-006).

### 10. Observability

With `LANGWATCH_API_KEY` set:

1. Complete one chat and one research run.
2. Confirm traces in LangWatch with `run_id`, `session_id`, `auth_subject`.

### 11. Static checks

```bash
make check
make test
```

## Baseline Comparison (SC-009)

Before refactor, measure median time from message submit to first SSE `token` or `thinking` event (browser devtools or curl SSE). After refactor, median should improve ≥30%.

## Deploy Notes (Railway)

- Big-bang deploy: chat + research switch together
- Run backfill script once after deploy if pre-existing chat sessions need agent store seeding
- No new Railway services required
- Verify `/health` after deploy

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Stuck "running" runs | Orphan recovery on startup logs |
| Empty sources | Tavily API key; tool result extraction logs |
| 409 on first message | Stale active run in DB; run orphan cleanup |
| History not continuous | Agent session store backfill; projection sync logs |
