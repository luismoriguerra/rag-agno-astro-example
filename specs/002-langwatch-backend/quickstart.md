# Quickstart: LangWatch Backend Observability

## Prerequisites

- Python 3.12 backend from feature `001-agentos-chat-search` running locally
- LangWatch account: https://langwatch.ai/
- API key from LangWatch dashboard

## Environment

Add to `apps/backend/.env` (see `.env.example` after implementation):

```bash
LANGWATCH_API_KEY=your-key-here
APP_ENVIRONMENT=local
# Optional self-hosted:
# LANGWATCH_ENDPOINT=https://your-langwatch.example
```

Keep existing variables (`OPENROUTER_API_KEY`, `DATABASE_URL`, etc.).

| Variable | Required for tracing | Default |
|----------|----------------------|---------|
| `LANGWATCH_API_KEY` | Yes, to enable export | (empty = disabled) |
| `APP_ENVIRONMENT` | No | `local` |
| `LANGWATCH_ENDPOINT` | No | LangWatch SaaS |
| `AGNO_TELEMETRY` | No | independent of LangWatch |

## Install and Run

```bash
make install
make db-up
make migrate
make dev-backend
```

With no `LANGWATCH_API_KEY`, chat works normally; no traces are sent.

## Enable Tracing (first trace in &lt;15 minutes)

1. Copy API key into `apps/backend/.env` as `LANGWATCH_API_KEY`.
2. Set `APP_ENVIRONMENT=local`.
3. Restart backend (`make dev-backend`).
4. Open `http://localhost:4321/chat` (or call `POST /v1/sessions/{id}/messages`).
5. Submit a question that triggers search (e.g. current events).
6. Open https://app.langwatch.ai/ and find the latest trace.
7. Verify metadata: `run_id`, `session_id`, `auth_subject`, `environment=local`.
8. Expand spans: model call + DuckDuckGo tool activity.

Optional CLI (if `langwatch` CLI installed):

```bash
langwatch trace search --limit 5
```

## Disable Tracing

Remove or comment out `LANGWATCH_API_KEY` and restart the backend. Chat behavior must be unchanged.

## Railway

LangWatch is **optional** for deploy (no gate).

1. Set on `agentos-chat-backend` service:
   - `LANGWATCH_API_KEY` (same project key as local, per spec)
   - `APP_ENVIRONMENT=production` (or `staging`)
2. Deploy: `make railway-deploy`
3. Run smoke test: `make railway-smoke`
4. Confirm a trace with `environment=production` (not `local`) in LangWatch.

## Verification (SC-001, SC-003, SC-007, SC-008)

Use this checklist during T020 / PR review:

| Check | How |
|-------|-----|
| SC-001 (60s trace) | Submit one chat message; trace visible in LangWatch within 60s of run completion |
| SC-007 (metadata) | Trace shows `run_id`, `session_id`, `auth_subject` matching DB/API records |
| SC-008 (environment) | Trace `environment` matches `APP_ENVIRONMENT` (`local` locally) |
| SC-003 (model vs tool) | On **10** search-backed runs, confirm model + DuckDuckGo tool spans in ≥9 traces (90%) |
| US1 scenario 3 (failure) | Trigger a failed or timed-out run (`REQUEST_TIMEOUT_SECONDS=1` temporarily); trace shows error/incomplete status; chat still returns user-facing error without crash |
| SC-002 / SC-005 (no regression) | With `LANGWATCH_API_KEY` unset vs set, submit the same chat flow; compare user-visible success (no new API errors when tracing on/off) |
| Invalid / revoked key | Set invalid `LANGWATCH_API_KEY`, restart; chat works; logs contain `langwatch_export_failed` or setup-failure event (no secret values in log) |

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No traces | `LANGWATCH_API_KEY` set? Backend restarted? Key valid? |
| Traces without metadata | Implementation regression; see `contracts/langwatch-trace-metadata.md` |
| Chat errors after enabling LangWatch | Should not happen (FR-006); check backend logs, not LangWatch UI |
| Export failures | Look for `langwatch_export_failed` in `make dev-backend` logs or `make railway-logs-backend` |

## Tests

```bash
make check
cd apps/backend && pytest tests/unit/test_langwatch.py  # after implementation
```
